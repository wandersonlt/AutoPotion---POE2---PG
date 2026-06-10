from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

from .database import engine, get_db, Base
from .auth import AuthHandler
from .license_service import LicenseService
from .stripe_service import StripeService
from .updater_service import UpdaterService
from .admin_routes import router as admin_router
from .user_routes import router as user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="License Manager API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
auth_handler = AuthHandler()
license_service = LicenseService()
stripe_service = StripeService()
updater_service = UpdaterService()

# Routers
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/user", tags=["user"])

@app.get("/")
async def root():
    return {"message": "License Manager API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/verify-license")
async def verify_license(license_key: str, machine_id: str, db=Depends(get_db)):
    result = await license_service.verify_license(license_key, machine_id, db)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@app.get("/api/check-update")
async def check_update(current_version: str):
    return await updater_service.check_update(current_version)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)