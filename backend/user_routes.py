from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pydantic import BaseModel

from .database import get_db
from .models import User, License, AuditLog
from .auth import AuthHandler
from .license_service import LicenseService

router = APIRouter()
auth_handler = AuthHandler()

class ReactivateRequest(BaseModel):
    license_key: str
    new_machine_id: str

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(auth_handler.get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    license = db.query(License).filter(License.user_id == current_user.id).first()
    
    remaining_days = None
    if license and license.expires_at:
        remaining = license.expires_at - datetime.utcnow()
        remaining_days = remaining.days
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat()
        },
        "license": {
            "key": license.key if license else None,
            "plan": license.plan.name if license and license.plan else None,
            "status": license.status.value if license else None,
            "expires_at": license.expires_at.isoformat() if license and license.expires_at else None,
            "remaining_days": remaining_days,
            "machine_id": license.machine_id if license else None
        } if license else None
    }

@router.post("/reactivate")
async def request_reactivation(
    request: ReactivateRequest,
    current_user: User = Depends(auth_handler.get_current_user),
    db: Session = Depends(get_db)
):
    """Request license reactivation for new machine"""
    license = db.query(License).filter(
        License.key == request.license_key,
        License.user_id == current_user.id
    ).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Update machine ID
    license.machine_id = request.new_machine_id
    license.status = "ACTIVE"
    db.commit()
    
    # Log reactivation
    audit_log = AuditLog(
        user_id=current_user.id,
        license_id=license.id,
        action="REACTIVATE",
        details=f"License reactivated for new machine: {request.new_machine_id}"
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "message": "License reactivated successfully"}

@router.get("/history")
async def get_license_history(
    current_user: User = Depends(auth_handler.get_current_user),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get license access history"""
    license = db.query(License).filter(License.user_id == current_user.id).first()
    
    if not license:
        return {"history": []}
    
    logs = db.query(AuditLog).filter(
        AuditLog.license_id == license.id
    ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "history": [
            {
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    }
