import os
import logging
from backend.database import engine, Base, SessionLocal
from backend.models import User, Plan
from backend.auth import AuthHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    logger.info("🔧 Iniciando setup do banco de dados...")
    
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelas criadas com sucesso!")
    
    db = SessionLocal()
    
    try:
        # Criar admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            logger.info("👨‍💼 Criando usuario administrador...")
            auth = AuthHandler()
            admin = User(
                username="admin",
                email="admin@autopotion.com",
                password_hash=auth.get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info("✅ Admin criado! Usuario: admin / senha: admin123")
        else:
            logger.info("✅ Admin ja existe")
        
        # Remover planos antigos e criar novos
        db.query(Plan).delete()
        
        plans = [
            {"name": "Free", "validity_days": None, "price": 0.00},
            {"name": "1 Dia", "validity_days": 1, "price": 0.50},
            {"name": "7 Dias", "validity_days": 7, "price": 2.90},
            {"name": "1 Mes", "validity_days": 30, "price": 9.90},
        ]
        
        for plan_data in plans:
            plan = Plan(**plan_data, is_active=True)
            db.add(plan)
            logger.info(f"📦 Plano criado: {plan_data['name']} - R$ {plan_data['price']:.2f}")
        
        db.commit()
        logger.info("✅ Planos criados com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro no setup: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    logger.info("🎉 Setup do banco de dados concluido!")

if __name__ == "__main__":
    init_database()