from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from .database import get_db
from .models import User, License, Plan, AuditLog, LicenseStatus, PlanType
from .auth import AuthHandler
from .license_service import LicenseService

router = APIRouter()
auth_handler = AuthHandler()

# ==================== MODELOS ====================

class AdminLogin(BaseModel):
    username: str
    password: str

class PlanCreate(BaseModel):
    name: str
    type: PlanType
    validity_days: Optional[int] = None
    price: float
    stripe_product_id: Optional[str] = None
    stripe_price_id: Optional[str] = None

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    validity_days: Optional[int] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    stripe_product_id: Optional[str] = None
    stripe_price_id: Optional[str] = None

class LicenseCreate(BaseModel):
    user_id: int
    plan_type: PlanType

# ==================== LOGIN ====================

@router.post("/login")
async def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    if not auth_handler.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    token = auth_handler.encode_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "role": user.role}}

# ==================== DASHBOARD ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_licenses = db.query(License).count()
    active_licenses = db.query(License).filter(License.status == LicenseStatus.ACTIVE).count()
    expired_licenses = db.query(License).filter(License.status == LicenseStatus.EXPIRED).count()
    blocked_licenses = db.query(License).filter(License.status == LicenseStatus.BLOCKED).count()
    revenue = db.query(func.sum(Plan.price)).join(License).filter(License.created_at >= datetime.utcnow() - timedelta(days=30)).scalar() or 0
    recent_activity = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return {
        "total_users": total_users,
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "expired_licenses": expired_licenses,
        "blocked_licenses": blocked_licenses,
        "revenue_last_30_days": revenue,
        "recent_activity": [{"action": log.action, "details": log.details, "created_at": log.created_at.isoformat(), "user": log.user.username if log.user else None} for log in recent_activity]
    }

# ==================== LICENÇAS ====================

@router.get("/licenses")
async def get_licenses(skip: int = 0, limit: int = 100, status: Optional[LicenseStatus] = None, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    query = db.query(License)
    if status:
        query = query.filter(License.status == status)
    total = query.count()
    licenses = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "licenses": [{
            "id": l.id, "key": l.key, "user": l.user.username if l.user else None,
            "user_email": l.user.email if l.user else None, "plan": l.plan.name if l.plan else None,
            "status": l.status.value, "machine_id": l.machine_id,
            "created_at": l.created_at.isoformat(), "expires_at": l.expires_at.isoformat() if l.expires_at else None,
            "last_access": l.last_access.isoformat() if l.last_access else None,
            "remaining_days": (l.expires_at - datetime.utcnow()).days if l.expires_at and l.expires_at > datetime.utcnow() else 0
        } for l in licenses]
    }

@router.post("/licenses")
async def create_license(license_data: LicenseCreate, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    try:
        license = await LicenseService.create_license(license_data.user_id, license_data.plan_type, db)
        return {"success": True, "license": {"key": license.key, "plan": license.plan.name, "expires_at": license.expires_at.isoformat() if license.expires_at else None}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/licenses/{license_key}/block")
async def block_license(license_key: str, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    license = db.query(License).filter(License.key == license_key).first()
    if license:
        license.status = LicenseStatus.BLOCKED
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404, detail="License not found")

@router.put("/licenses/{license_key}/unblock")
async def unblock_license(license_key: str, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    license = db.query(License).filter(License.key == license_key).first()
    if license:
        license.status = LicenseStatus.ACTIVE
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404, detail="License not found")

@router.delete("/licenses/{license_key}")
async def delete_license(license_key: str, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    license = db.query(License).filter(License.key == license_key).first()
    if license:
        db.delete(license)
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404, detail="License not found")

# ==================== PLANOS ====================

@router.get("/plans")
async def get_plans(admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    plans = db.query(Plan).all()
    return [{"id": p.id, "name": p.name, "type": p.type.value, "validity_days": p.validity_days, "price": p.price, "stripe_product_id": p.stripe_product_id, "stripe_price_id": p.stripe_price_id, "is_active": p.is_active} for p in plans]

@router.post("/plans")
async def create_plan(plan_data: PlanCreate, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    existing = db.query(Plan).filter(Plan.type == plan_data.type).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plan type already exists")
    plan = Plan(**plan_data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"success": True, "plan": plan_data.model_dump()}

@router.put("/plans/{plan_id}")
async def update_plan(plan_id: int, plan_data: PlanUpdate, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for key, value in plan_data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    return {"success": True}

@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if plan:
        db.delete(plan)
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404, detail="Plan not found")