from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import pedidos
from app.database.connection import init_db
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pedidos Service",
    description="Microservicio de gestión de pedidos con validación de inventario en tiempo real",
    version="1.0.1"
)

# Configuración de CORS optimizada
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Incluir rutas
app.include_router(pedidos.router, prefix="/api/v1", tags=["pedidos"])

@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al iniciar"""
    try:
        await init_db()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy", "service": "pedidos-service"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PEDIDOS_SERVICE_PORT", 8007))
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        workers=1,
        loop="asyncio",
        access_log=False,
        log_level="warning"
    )
