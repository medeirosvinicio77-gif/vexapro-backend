from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VexaPro", version="0.1.0")

# CORS - Permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Importar TODAS as Rotas ============

from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.projects import router as projects_router
from api.v1.videos import router as videos_router
from api.v1.measurements import router as measurements_router
from api.v1.marketplace import router as marketplace_router
from api.v1.design import router as design_router
from api.v1.pipeline_endpoint import router as pipeline_router

# ============ Registrar Rotas ============

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(measurements_router, prefix="/api/v1")
app.include_router(marketplace_router, prefix="/api/v1")
app.include_router(design_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")

# ============ Rotas Básicas ============

@app.get("/")
def root():
    return {
        "message": "VexaPro API",
        "version": "0.1.0",
        "status": "running",
        "modules": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "projects": "/api/v1/projects",
            "videos": "/api/v1/videos",
            "measurements": "/api/v1/measurements",
            "marketplace": "/api/v1/marketplace",
            "design": "/api/v1/design",
            "pipeline": "/api/v1/pipeline"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}