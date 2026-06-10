from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import string
from typing import Dict, Any
from models import License, LicenseStatus, Plan, User, AuditLog
from dateutil import parser

class LicenseService:
    
    @staticmethod
    def generate_license_key() -> str:
        """Generate a unique license key"""
        characters = string.ascii_uppercase + string.digits
        parts = []
        for _ in range(5):
            part = ''.join(secrets.choice(characters) for _ in range(5))
            parts.append(part)
        return '-'.join(parts)
    
    @staticmethod
    async def verify_license(license_key: str, machine_id: str, db: Session) -> Dict[str, Any]:
        """Verify license validity"""
        license = db.query(License).filter(License.key == license_key).first()
        
        if not license:
            return {"valid": False, "message": "Invalid license key"}
        
        # Check status
        if license.status == LicenseStatus.BLOCKED:
            return {"valid": False, "message": "License is blocked"}
        
        if license.status == LicenseStatus.SUSPENDED:
            return {"valid": False, "message": "License is suspended"}
        
        # Check expiration
        if license.expires_at and license.expires_at < datetime.utcnow():
            if license.plan.type != "LIFETIME":
                license.status = LicenseStatus.EXPIRED
                db.commit()
                return {"valid": False, "message": "License has expired"}
        
        # Check machine ID
        if not license.machine_id:
            # First activation
            license.machine_id = machine_id
            license.last_access = datetime.utcnow()
            db.commit()
        elif license.machine_id != machine_id:
            return {"valid": False, "message": "License already activated on another machine"}
        else:
            # Update last access
            license.last_access = datetime.utcnow()
            db.commit()
        
        # Get remaining days
        remaining_days = None
        if license.expires_at and license.plan.type != "LIFETIME":
            remaining = license.expires_at - datetime.utcnow()
            remaining_days = remaining.days
        
        # Log access
        audit_log = AuditLog(
            user_id=license.user_id,
            license_id=license.id,
            action="ACCESS",
            details="License accessed"
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "valid": True,
            "message": "License verified successfully",
            "license": {
                "key": license.key,
                "plan": license.plan.name,
                "expires_at": license.expires_at.isoformat() if license.expires_at else None,
                "remaining_days": remaining_days,
                "status": license.status.value
            }
        }
    
    @staticmethod
    async def create_license(user_id: int, plan_type: str, db: Session) -> License:
        """Create a new license"""
        plan = db.query(Plan).filter(Plan.type == plan_type).first()
        if not plan:
            raise ValueError(f"Plan {plan_type} not found")
        
        # Calculate expiration date
        expires_at = None
        if plan.validity_days:
            expires_at = datetime.utcnow() + timedelta(days=plan.validity_days)
        
        license_key = LicenseService.generate_license_key()
        
        license = License(
            key=license_key,
            user_id=user_id,
            plan_id=plan.id,
            expires_at=expires_at,
            status=LicenseStatus.ACTIVE
        )
        
        db.add(license)
        db.commit()
        db.refresh(license)
        
        # Log creation
        audit_log = AuditLog(
            user_id=user_id,
            license_id=license.id,
            action="CREATE",
            details=f"License created for plan {plan.name}"
        )
        db.add(audit_log)
        db.commit()
        
        return license
    
    @staticmethod
    async def renew_license(license_id: int, db: Session) -> License:
        """Renew an existing license"""
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            raise ValueError("License not found")
        
        # Extend expiration by plan validity days
        if license.plan.validity_days:
            if license.expires_at and license.expires_at > datetime.utcnow():
                license.expires_at = license.expires_at + timedelta(days=license.plan.validity_days)
            else:
                license.expires_at = datetime.utcnow() + timedelta(days=license.plan.validity_days)
        
        license.status = LicenseStatus.ACTIVE
        db.commit()
        
        # Log renewal
        audit_log = AuditLog(
            user_id=license.user_id,
            license_id=license.id,
            action="RENEW",
            details="License renewed"
        )
        db.add(audit_log)
        db.commit()
        
        return license
    
    @staticmethod
    async def block_license(license_id: int, db: Session) -> License:
        """Block a license"""
        license = db.query(License).filter(License.id == license_id).first()
        if license:
            license.status = LicenseStatus.BLOCKED
            db.commit()
        return license
    
    @staticmethod
    async def unblock_license(license_id: int, db: Session) -> License:
        """Unblock a license"""
        license = db.query(License).filter(License.id == license_id).first()
        if license:
            license.status = LicenseStatus.ACTIVE
            db.commit()
        return license