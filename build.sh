#!/bin/bash

echo "🚀 Iniciando build do projeto..."

# Instalar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p static templates

# Executar setup do banco de dados
echo "🗄️ Configurando banco de dados..."
python setup_db.py

echo "✅ Build concluído com sucesso!"