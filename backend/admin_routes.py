from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from .database import get_db
from .models import User, License, Plan, AuditLog, LicenseStatus
from .auth import AuthHandler
from .license_service import LicenseService

router = APIRouter()
auth_handler = AuthHandler()

class AdminLogin(BaseModel):
    username: str
    password: str

class PlanCreate(BaseModel):
    name: str
    validity_days: Optional[int] = None
    price: float

class LicenseCreate(BaseModel):
    user_id: int
    plan_id: int

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
    return {"access_token": token, "token_type": "bearer"}

@router.get("/dashboard/stats")
async def get_dashboard_stats(admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_licenses = db.query(License).count()
    active_licenses = db.query(License).filter(License.status == LicenseStatus.ACTIVE).count()
    expired_licenses = db.query(License).filter(License.status == LicenseStatus.EXPIRED).count()
    blocked_licenses = db.query(License).filter(License.status == LicenseStatus.BLOCKED).count()
    
    return {
        "total_users": total_users,
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "expired_licenses": expired_licenses,
        "blocked_licenses": blocked_licenses,
        "revenue_last_30_days": 0
    }

@router.get("/plans")
async def get_plans(admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.is_active == True).all()
    return [{"id": p.id, "name": p.name, "validity_days": p.validity_days, "price": p.price} for p in plans]

@router.post("/plans")
async def create_plan(plan_data: PlanCreate, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    existing = db.query(Plan).filter(Plan.name == plan_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plano já existe")
    
    plan = Plan(**plan_data.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"success": True, "plan": {"id": plan.id, "name": plan.name, "validity_days": plan.validity_days, "price": plan.price}}

@router.get("/licenses")
async def get_licenses(skip: int = 0, limit: int = 100, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    licenses = db.query(License).offset(skip).limit(limit).all()
    return {
        "licenses": [
            {
                "id": l.id,
                "key": l.key,
                "user": l.user.username if l.user else None,
                "plan": l.plan.name if l.plan else None,
                "status": l.status,
                "machine_id": l.machine_id if l.machine_id else "Not assigned",
                "created_at": l.created_at.isoformat(),
                "expires_at": l.expires_at.isoformat() if l.expires_at else None
            }
            for l in licenses
        ]
    }

@router.post("/licenses")
async def create_license(license_data: LicenseCreate, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    try:
        license = await LicenseService.create_license(license_data.user_id, license_data.plan_id, db)
        return {"success": True, "license": {"key": license.key}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/licenses/{license_key}/block")
async def block_license(license_key: str, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    license = db.query(License).filter(License.key == license_key).first()
    if license:
        license.status = LicenseStatus.BLOCKED
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404)

@router.delete("/licenses/{license_key}")
async def delete_license(license_key: str, admin: User = Depends(auth_handler.require_admin), db: Session = Depends(get_db)):
    license = db.query(License).filter(License.key == license_key).first()
    if license:
        db.delete(license)
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404)