"""
Script para inicializar o banco de dados
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.database import init_db, SessionLocal, engine, Base
from models.user import User
from models.project import Project
from models.video import Video
from models.measurement import Measurement
from core.security import get_password_hash

def create_tables():
    """Cria todas as tabelas"""
    print("🗄️ Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")
    print("   Tabelas:", list(Base.metadata.tables.keys()))

def create_default_users():
    """Cria usuários padrão para teste"""
    db = SessionLocal()
    
    try:
        # Admin
        admin = db.query(User).filter(User.email == "admin@vexapro.com").first()
        if not admin:
            admin = User(
                email="admin@vexapro.com",
                hashed_password=get_password_hash("admin123"),
                name="Administrador",
                role="admin",
                is_verified=True
            )
            db.add(admin)
            print("✅ Admin criado")
        
        # Profissional (marceneiro)
        pro = db.query(User).filter(User.email == "marceneiro@vexapro.com").first()
        if not pro:
            pro = User(
                email="marceneiro@vexapro.com",
                hashed_password=get_password_hash("marceneiro123"),
                name="João Marceneiro",
                role="professional",
                is_verified=True
            )
            db.add(pro)
            print("✅ Profissional criado")
        
        # Cliente (PF)
        client = db.query(User).filter(User.email == "cliente@vexapro.com").first()
        if not client:
            client = User(
                email="cliente@vexapro.com",
                hashed_password=get_password_hash("cliente123"),
                name="Maria Cliente",
                role="client",
                is_verified=True
            )
            db.add(client)
            print("✅ Cliente criado")
        
        db.commit()
        print("\n👥 Usuários cadastrados:")
        print("   Admin: admin@vexapro.com / admin123")
        print("   Profissional: marceneiro@vexapro.com / marceneiro123")
        print("   Cliente: cliente@vexapro.com / cliente123")
    
    except Exception as e:
        print(f"❌ Erro ao criar usuários: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🗄️ VexaPro - Inicialização do Banco de Dados")
    print("=" * 50)
    create_tables()
    print()
    create_default_users()
    print()
    print("✅ Banco de dados inicializado com sucesso!")