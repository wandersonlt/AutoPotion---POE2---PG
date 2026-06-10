from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="USER")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    licenses = relationship("License", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    validity_days = Column(Integer)
    price = Column(Float)
    stripe_price_id = Column(String(100))
    stripe_product_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    licenses = relationship("License", back_populates="plan")

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))
    machine_id = Column(String(255))
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    last_access = Column(DateTime(timezone=True))
    activation_ip = Column(String(45))
    
    user = relationship("User", back_populates="licenses")
    plan = relationship("Plan", back_populates="licenses")
    audit_logs = relationship("AuditLog", back_populates="license")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    license_id = Column(Integer, ForeignKey("licenses.id"))
    action = Column(String(50), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="audit_logs")
    license = relationship("License", back_populates="audit_logs")