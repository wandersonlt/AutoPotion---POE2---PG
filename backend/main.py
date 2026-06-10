from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

# Importações relativas
from .database import engine, get_db, Base
from .auth import AuthHandler
from .license_service import LicenseService
from .stripe_service import StripeService
from .updater_service import UpdaterService
from .admin_routes import router as admin_router
from .user_routes import router as user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORREÇÃO: Função lifespan síncrona para criar tabelas
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - criar tabelas de forma síncrona
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")
    yield
    # Shutdown
    logger.info("Shutting down...")

# Initialize FastAPI
app = FastAPI(title="License Manager API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
auth_handler = AuthHandler()
license_service = LicenseService()
stripe_service = StripeService()
updater_service = UpdaterService()

# Include routers
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/user", tags=["user"])

# Public endpoints
@app.get("/")
async def root():
    return {"message": "License Manager API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/verify-license")
async def verify_license(license_key: str, machine_id: str, db=Depends(get_db)):
    """Verify license and get access"""
    result = await license_service.verify_license(license_key, machine_id, db)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@app.get("/api/check-update")
async def check_update(current_version: str):
    """Check for application updates"""
    return await updater_service.check_update(current_version)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)