from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Optional
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

# Usar pbkdf2_sha256 em vez de bcrypt (mais compatível)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class AuthHandler:
    security = HTTPBearer()
    
    def __init__(self):
        self.secret = os.getenv("JWT_SECRET", "your-secret-key-change-this")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    
    def get_password_hash(self, password: str) -> str:
        """Hash password using pbkdf2_sha256 (no bcrypt issues)"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def encode_token(self, user_id: int, role: str) -> str:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': str(user_id),
            'role': role
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    
    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        return self.decode_token(auth.credentials)
    
    def get_current_user(self, token_data: dict = Depends(auth_wrapper), db: Session = Depends(get_db)) -> User:
        user = db.query(User).filter(User.id == int(token_data['sub'])).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    def require_admin(self, user: User = Depends(get_current_user)) -> User:
        if user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user