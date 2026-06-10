from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

# Adicione NO INÍCIO do arquivo (com os outros imports)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.requests import Request

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

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory="admin_panel/templates")
app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")

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

# Rota para página inicial (redireciona para admin)
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>License Manager API</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h1>License Manager API</h1>
            <p>API está rodando normalmente.</p>
            <p>Acesse <a href="/admin/login">/admin/login</a> para o painel administrativo.</p>
            <p>Acesse <a href="/docs">/docs</a> para a documentação da API.</p>
        </body>
    </html>
    """

# Rota para login do admin
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Rota para dashboard do admin
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Rota para gerenciamento de licenças
@app.get("/admin/licenses", response_class=HTMLResponse)
async def admin_licenses_page(request: Request):
    return templates.TemplateResponse("licenses.html", {"request": request})

# Rota para gerenciamento de planos
@app.get("/admin/plans", response_class=HTMLResponse)
async def admin_plans_page(request: Request):
    return templates.TemplateResponse("plans.html", {"request": request})

# Rota para página base (template)
@app.get("/admin/base", response_class=HTMLResponse)
async def admin_base_page(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)