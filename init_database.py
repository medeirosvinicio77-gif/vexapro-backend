import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database.database import init_db, SessionLocal, engine, Base
from models.user import User
from models.project import Project
from models.video import Video
from models.measurement import Measurement
from core.security import get_password_hash

def create_tables():
    print("🗄️ Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas!")

def create_users():
    db = SessionLocal()
    try:
        users_data = [
            {"email": "admin@vexapro.com", "password": "admin123", "name": "Administrador", "role": "admin"},
            {"email": "marceneiro@vexapro.com", "password": "marceneiro123", "name": "João Marceneiro", "role": "professional"},
            {"email": "cliente@vexapro.com", "password": "cliente123", "name": "Maria Cliente", "role": "client"}
        ]
        for u in users_data:
            if not db.query(User).filter(User.email == u["email"]).first():
                user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    name=u["name"],
                    role=u["role"],
                    is_verified=True
                )
                db.add(user)
        db.commit()
        print("✅ Usuários padrão criados")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    create_users()
