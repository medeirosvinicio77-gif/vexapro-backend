import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "VexaPro"
    VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-2024")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # SQLite para desenvolvimento (não precisa instalar PostgreSQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./vexapro.db"
    )
    
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

settings = Settings()