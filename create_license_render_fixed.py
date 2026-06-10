import psycopg2
import secrets
import string
from datetime import datetime, timedelta
import hashlib

# URL do banco no Render
DATABASE_URL = "postgresql://autopotion_user:wHym9OXEbmlvo1JfQxTHQvkGiirtT1tD@dpg-d8kjtnddt1ts73a5kr1g-a.ohio-postgres.render.com/autopotion_licenses?sslmode=require"

def generate_license_key():
    characters = string.ascii_uppercase + string.digits
    parts = []
    for _ in range(5):
        part = ''.join(secrets.choice(characters) for _ in range(5))
        parts.append(part)
    return '-'.join(parts)

def create_license_on_render():
    print("🔧 Conectando ao banco do Render...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("✅ Conectado ao PostgreSQL do Render!")
        
        # Verificar se admin existe
        cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
        admin = cursor.fetchone()
        
        if not admin:
            print("👨‍💼 Criando usuário admin...")
            admin_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, ("admin", "admin@autopotion.com", admin_password_hash, "ADMIN", True))
            admin_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✅ Admin criado com ID: {admin_id}")
        else:
            admin_id = admin[0]
            print(f"✅ Admin encontrado com ID: {admin_id}")
        
        # Criar usuário de teste
        test_username = f"test_user_{secrets.token_hex(4)}"
        test_password_hash = hashlib.sha256("test123".encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (test_username, f"{test_username}@test.com", test_password_hash, "USER", True))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Usuário de teste criado: {test_username}")
        
        # Pegar plano 30 days
        cursor.execute("SELECT id, validity_days FROM plans WHERE type = 'THIRTY_DAYS' LIMIT 1")
        plan = cursor.fetchone()
        
        if not plan:
            print("❌ Plano '30 Days' não encontrado!")
            return
        
        plan_id = plan[0]
        validity_days = plan[1]
        
        # Criar licença
        license_key = generate_license_key()
        expires_at = datetime.now() + timedelta(days=validity_days)
        
        cursor.execute("""
            INSERT INTO licenses (key, user_id, plan_id, status, expires_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (license_key, user_id, plan_id, "ACTIVE", expires_at, datetime.now()))
        
        conn.commit()
        
        print("\n" + "="*50)
        print("✅ LICENÇA CRIADA NO RENDER COM SUCESSO!")
        print("="*50)
        print(f"📝 Chave: {license_key}")
        print(f"👤 Usuário: {test_username}")
        print(f"📧 Email: {test_username}@test.com")
        print(f"📋 Plano: 30 Days")
        print(f"⏰ Expira em: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        with open("render_license.txt", "w") as f:
            f.write(f"License Key: {license_key}\n")
            f.write(f"Username: {test_username}\n")
            f.write(f"Email: {test_username}@test.com\n")
            f.write(f"Password: test123\n")
            f.write(f"Plan: 30 Days\n")
            f.write(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("\n💾 Licença salva em render_license.txt")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    create_license_on_render()
