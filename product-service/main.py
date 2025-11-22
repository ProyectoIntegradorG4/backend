# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.products import router as products_router
from app.routes.lotes import router as lotes_router
from app.routes.plan_venta import router as plan_venta_router
from app.database.connection import init_db, test_db_connection, SessionLocal, ensure_database_exists
from app.database.seed import seed_categories, seed_warehouses
import asyncio
import logging


logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Product Service (HU-WEB-003 & HU-WEB-008)",
    description="Microservicio de productos médicos y planes de venta",
    version="1.2.5"
)

# Endpoints “legacy” sin prefijo
app.include_router(products_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Endpoints públicos versión v1
app.include_router(products_router, prefix="/api/v1", tags=["products"])
app.include_router(lotes_router, prefix="/api/v1", tags=["lotes"])
app.include_router(plan_venta_router, tags=["planes-venta"]) 

@app.on_event("startup")
async def startup_event():
    # Asegurar que la BD exista antes de conectar
    logger.info("🔍 Ensuring database exists...")
    ensure_database_exists()

    # Probar conexión con reintentos
    for attempt in range(5):
        if test_db_connection():
            logger.info("Conexión a BD establecida.")
            break
        logger.warning(f"Intento {attempt + 1}/5 fallido. Reintentando en 3s...")
        await asyncio.sleep(3)
    else:
        logger.error("No se pudo conectar a la BD. Continuando sin seed.")
        return

    # Migraciones/creación de tablas y seed de datos
    # OJO: init_db es sincrónica -> NO usar 'await'
    init_db()
    with SessionLocal() as db:
        seed_categories(db)
        seed_warehouses(db)
    logger.info("Seed de categorías y bodegas completado.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-service"}

if __name__ == "__main__":
    import uvicorn
    # workers=1 para evitar condiciones de carrera con el seed en entornos locales
    uvicorn.run(app, host="0.0.0.0", port=8005, workers=1, loop="asyncio")
