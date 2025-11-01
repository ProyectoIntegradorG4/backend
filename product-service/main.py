from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.products import router as products_router
from app.database.connection import init_db, test_db_connection, SessionLocal, ensure_database_exists
from app.database.seed import seed_categories
import asyncio
import logging

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Product Service (HU-WEB-003)",
    description="Microservicio de carga individual de productos médicos",
    version="1.1.6"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

app.include_router(products_router, prefix="/api/v1", tags=["products"])

@app.on_event("startup")
async def startup_event():
    # Ensure database exists before attempting connection
    logger.info("🔍 Ensuring database exists...")
    ensure_database_exists()

    for attempt in range(5):
        if test_db_connection():
            logger.info("✅ Conexión a BD establecida.")
            break
        logger.warning(f"Intento {attempt+1}/5 fallido. Reintentando en 3s...")
        await asyncio.sleep(3)
    else:
        logger.error("❌ No se pudo conectar a la BD. Continuando sin seed.")
        return

    await init_db()
    with SessionLocal() as db:
        seed_categories(db)
    logger.info("🌱 Seed de categorías completado.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, workers=1, loop="asyncio")
