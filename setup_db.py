import os
import sys
import logging
from backend.database import engine, Base, SessionLocal
from backend.models import User, Plan, PlanType
from backend.auth import AuthHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    logger.info("🔧 Iniciando setup do banco de dados...")
    
    # Criar tabelas
    logger.info("📊 Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelas criadas com sucesso!")
    
    db = SessionLocal()
    
    try:
        # Criar usuário admin
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        admin = db.query(User).filter(User.username == admin_username).first()
        if not admin:
            logger.info("👨‍💼 Criando usuário administrador...")
            auth = AuthHandler()
            admin = User(
                username=admin_username,
                email="admin@autopotion.com",
                password_hash=auth.get_password_hash(admin_password),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info(f"✅ Admin criado! Usuário: {admin_username}")
            logger.info(f"⚠️  SENHA ADMIN: {admin_password} (GUARDE ESTA SENHA!)")
        else:
            logger.info("✅ Admin já existe")
        
        # Criar planos padrão
        plans_data = [
            {"name": "Free", "type": PlanType.FREE, "validity_days": None, "price": 0.0},
            {"name": "30 Days", "type": PlanType.THIRTY_DAYS, "validity_days": 30, "price": 29.90},
            {"name": "90 Days", "type": PlanType.NINETY_DAYS, "validity_days": 90, "price": 79.90},
            {"name": "180 Days", "type": PlanType.ONE_EIGHTY_DAYS, "validity_days": 180, "price": 149.90},
            {"name": "365 Days", "type": PlanType.THREE_SIXTY_FIVE_DAYS, "validity_days": 365, "price": 299.90},
            {"name": "Lifetime", "type": PlanType.LIFETIME, "validity_days": None, "price": 499.90},
        ]
        
        for plan_data in plans_data:
            existing_plan = db.query(Plan).filter(Plan.type == plan_data["type"]).first()
            if not existing_plan:
                logger.info(f"📦 Criando plano: {plan_data['name']}")
                plan = Plan(**plan_data)
                db.add(plan)
        
        db.commit()
        logger.info("✅ Planos criados com sucesso!")
        
        # Listar planos criados
        plans = db.query(Plan).all()
        logger.info("📋 Planos disponíveis:")
        for plan in plans:
            logger.info(f"   - {plan.name} (R${plan.price:.2f})")
        
    except Exception as e:
        logger.error(f"❌ Erro no setup: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    logger.info("🎉 Setup do banco de dados concluído!")

if __name__ == "__main__":
    init_database()