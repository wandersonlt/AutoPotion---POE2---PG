from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import string
from typing import Dict, Any

from .models import License, LicenseStatus, Plan, User, AuditLog

class LicenseService:
    
    @staticmethod
    def generate_license_key() -> str:
        characters = string.ascii_uppercase + string.digits
        parts = []
        for _ in range(5):
            part = ''.join(secrets.choice(characters) for _ in range(5))
            parts.append(part)
        return '-'.join(parts)
    
    @staticmethod
    async def verify_license(license_key: str, machine_id: str, db: Session) -> Dict[str, Any]:
        license = db.query(License).filter(License.key == license_key).first()
        
        if not license:
            return {"valid": False, "message": "Invalid license key"}
        
        if license.status == LicenseStatus.BLOCKED:
            return {"valid": False, "message": "License is blocked"}
        
        if license.expires_at:
            expires_naive = license.expires_at.replace(tzinfo=None) if license.expires_at.tzinfo else license.expires_at
            if expires_naive < datetime.utcnow():
                license.status = LicenseStatus.EXPIRED
                db.commit()
                return {"valid": False, "message": "License has expired"}
        
        if not license.machine_id:
            license.machine_id = machine_id
            license.last_access = datetime.utcnow()
            db.commit()
        elif license.machine_id != machine_id:
            return {"valid": False, "message": "License already activated on another machine"}
        else:
            license.last_access = datetime.utcnow()
            db.commit()
        
        remaining_days = None
        if license.expires_at:
            expires_naive = license.expires_at.replace(tzinfo=None) if license.expires_at.tzinfo else license.expires_at
            remaining = expires_naive - datetime.utcnow()
            remaining_days = remaining.days
        
        return {
            "valid": True,
            "message": "License verified successfully",
            "license": {
                "key": license.key,
                "plan": license.plan.name,
                "expires_at": license.expires_at.isoformat() if license.expires_at else None,
                "remaining_days": remaining_days,
                "status": license.status
            }
        }
    
    @staticmethod
    async def create_license(user_id: int, plan_id: int, db: Session):
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        expires_at = None
        if plan.validity_days:
            expires_at = datetime.utcnow() + timedelta(days=plan.validity_days)
        
        license_key = LicenseService.generate_license_key()
        
        license = License(
            key=license_key,
            user_id=user_id,
            plan_id=plan_id,
            expires_at=expires_at,
            status=LicenseStatus.ACTIVE
        )
        
        db.add(license)
        db.commit()
        db.refresh(license)
        
        return license