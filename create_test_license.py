import asyncio
import secrets
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models import User, License, Plan
from backend.license_service import LicenseService

async def create_test_license():
    print("🔧 Criando licença de teste...")
    db = SessionLocal()
    
    try:
        # Criar usuário de teste
        test_username = f"test_user_{secrets.token_hex(4)}"
        
        # Criar usuário diretamente (sem hash para teste local)
        test_user = User(
            username=test_username,
            email=f"{test_username}@test.com",
            password_hash="dummy_hash_for_test",
            role="USER",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Pegar o plano de 30 dias
        plan = db.query(Plan).filter(Plan.type == "THIRTY_DAYS").first()
        
        if not plan:
            print("❌ Plano não encontrado!")
            return
        
        # Criar licença (USANDO AWAIT)
        license = await LicenseService.create_license(test_user.id, plan.type, db)
        
        print("\n" + "="*50)
        print("✅ LICENÇA DE TESTE CRIADA COM SUCESSO!")
        print("="*50)
        print(f"📝 Chave: {license.key}")
        print(f"👤 Usuário: {test_user.username}")
        print(f"📧 Email: {test_user.email}")
        print(f"📋 Plano: {plan.name}")
        if license.expires_at:
            print(f"⏰ Expira em: {license.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        # Salvar em arquivo
        with open("test_license.txt", "w") as f:
            f.write(f"License Key: {license.key}\n")
            f.write(f"Username: {test_user.username}\n")
            f.write(f"Email: {test_user.email}\n")
            f.write(f"Plan: {plan.name}\n")
            if license.expires_at:
                f.write(f"Expires: {license.expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("\n💾 Licença salva em test_license.txt")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_test_license())