from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

# Detecta se está no Render ou localmente
IS_RENDER = os.environ.get("RENDER", False)

if IS_RENDER:
    # No Render, usa PostgreSQL obrigatoriamente
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não configurada no Render")
    
    # Render já fornece a URL no formato correto
    engine = create_engine(DATABASE_URL)
    
else:
    # Desenvolvimento local - pode escolher
    db_type = os.getenv("DB_TYPE", "sqlite")  # sqlite ou postgresql
    
    if db_type == "postgresql":
        # Para testar PostgreSQL localmente
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/license_db")
        engine = create_engine(DATABASE_URL)
    else:
        # SQLite para desenvolvimento rápido (recomendado)
        DATABASE_URL = "sqlite:///./license_manager.db"
        engine = create_engine(
            DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()