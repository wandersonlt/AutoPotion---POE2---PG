#!/bin/bash

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Inicializar banco de dados
python -c "from backend.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Iniciar com gunicorn (mais estável que uvicorn)
gunicorn backend.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120