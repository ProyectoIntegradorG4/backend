from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users
from app.database.connection import init_db

app = FastAPI(
    title="User Service",
    description="Microservicio de gestión de usuarios con orquestador de registro optimizado",
    version="2.0.0"
)

# Configuración de CORS optimizada
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests por 1 hora
)

# Incluir rutas
app.include_router(users.router, tags=["users"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        workers=1,  # En contenedor, usar 1 worker por contenedor
        loop="asyncio",
        access_log=False,  # Deshabilitar logs de acceso para mayor rendimiento
        log_level="warning"  # Reducir verbosidad de logs
    )