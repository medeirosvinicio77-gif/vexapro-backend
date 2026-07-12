from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VexaPro", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Importar Rotas (com fallback para módulos pesados) ============
routers = []

# Rotas essenciais (sempre carregam)
from api.v1.auth import router as auth_router
routers.append(auth_router)
from api.v1.users import router as users_router
routers.append(users_router)
from api.v1.projects import router as projects_router
routers.append(projects_router)
from api.v1.videos import router as videos_router
routers.append(videos_router)
from api.v1.measurements import router as measurements_router
routers.append(measurements_router)

# Rotas que dependem de bibliotecas pesadas (open3d, torch, ifcopenshell)
# Se falharem, o servidor continua funcionando sem elas
try:
    from api.v1.marketplace import router as marketplace_router
    routers.append(marketplace_router)
    print("✅ Marketplace carregado")
except Exception as e:
    print(f"⚠️ Marketplace não carregado: {e}")

try:
    from api.v1.design import router as design_router
    routers.append(design_router)
    print("✅ Design carregado")
except Exception as e:
    print(f"⚠️ Design não carregado: {e}")

# Registrar todas as rotas coletadas
for router in routers:
    app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": "VexaPro API",
        "version": "0.1.0",
        "status": "running",
        "modules_loaded": len(routers)
    }

@app.get("/health")
def health():
    return {"status": "ok"}