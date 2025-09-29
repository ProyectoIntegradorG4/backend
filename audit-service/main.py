from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import audits
from app.database.connection import init_db

app = FastAPI(
    title="Audit Service",
    description="Microservicio para auditoría y logs del sistema",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de auditoría
app.include_router(audits.router, tags=["audits"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "audit-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)