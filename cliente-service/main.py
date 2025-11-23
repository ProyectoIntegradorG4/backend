from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.clientes import router as clientes_router
from app.database.connection import init_db, test_db_connection, ensure_database_exists, SessionLocal
from app.database.seed import run_seeds
import asyncio
import logging

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Cliente Service (HU-MOV-002)",
    description="Microservicio de gestión de clientes institucionales para gerentes de cuenta",
    version="1.0.5"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests por 1 hora
)

# Incluir rutas con prefijo /api/v1
app.include_router(clientes_router, prefix="/api/v1/clientes", tags=["clientes"])


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio: configurar base de datos y ejecutar seeds
    """
    logger.info("🚀 Iniciando Cliente Service...")
    
    # Asegurar que la base de datos existe
    logger.info("🔍 Verificando existencia de base de datos...")
    ensure_database_exists()
    
    # Intentar conectar a la base de datos con reintentos
    for attempt in range(5):
        if test_db_connection():
            logger.info("✅ Conexión a base de datos establecida.")
            break
        logger.warning(f"Intento {attempt+1}/5 fallido. Reintentando en 3s...")
        await asyncio.sleep(3)
    else:
        logger.error("❌ No se pudo conectar a la base de datos. Continuando sin seed.")
        return
    
    # Crear tablas
    logger.info("📋 Creando tablas...")
    init_db()
    
    # Ejecutar migraciones
    logger.info("🔄 Ejecutando migraciones...")
    from app.database.migration import run_migrations
    with SessionLocal() as db:
        run_migrations(db)
    
    # Ejecutar seeds de datos de prueba
    logger.info("🌱 Ejecutando seeds de datos de prueba...")
    with SessionLocal() as db:
        run_seeds(db)
    
    logger.info("✅ Cliente Service iniciado correctamente")


@app.get("/health")
async def health_check():
    """
    Health check endpoint para verificar el estado del servicio
    """
    return {
        "status": "healthy",
        "service": "cliente-service",
        "version": "1.0.5"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8013,
        workers=1,  # En contenedor, usar 1 worker por contenedor
        loop="asyncio",
        access_log=False,  # Deshabilitar logs de acceso para mayor rendimiento
        log_level="info"
    )

