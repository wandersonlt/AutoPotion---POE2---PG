import os
import sys
from backend.database import SessionLocal
from backend.models import User, License, Plan, PlanType
from backend.license_service import LicenseService
from backend.auth import AuthHandler
import uuid

def create_test_license():
    print("🔧 Criando licença de teste...")
    db = SessionLocal()
    
    try:
        # Criar usuário de teste
        auth = AuthHandler()
        test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        
        test_user = User(
            username=test_username,
            email=f"{test_username}@test.com",
            password_hash=auth.get_password_hash("test123"),
            role="USER",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Pegar o plano de 30 dias
        plan = db.query(Plan).filter(Plan.type == PlanType.THIRTY_DAYS).first()
        
        if not plan:
            print("❌ Plano não encontrado! Execute setup_db.py primeiro.")
            return
        
        # Criar licença
        license = LicenseService.create_license(test_user.id, plan.type, db)
        
        print("\n" + "="*50)
        print("✅ LICENÇA DE TESTE CRIADA COM SUCESSO!")
        print("="*50)
        print(f"📝 Chave da Licença: {license.key}")
        print(f"👤 Usuário: {test_user.username}")
        print(f"📧 Email: {test_user.email}")
        print(f"📋 Plano: {plan.name}")
        print(f"⏰ Expira em: {license.expires_at}")
        print("="*50)
        print("\n⚠️  Use esta chave para testar o login no aplicativo!")
        
        # Salvar em arquivo para fácil acesso
        with open("test_license.txt", "w") as f:
            f.write(f"License Key: {license.key}\n")
            f.write(f"Username: {test_user.username}\n")
            f.write(f"Email: {test_user.email}\n")
            f.write(f"Plan: {plan.name}\n")
        
        print("\n💾 Licença salva em test_license.txt")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_license()