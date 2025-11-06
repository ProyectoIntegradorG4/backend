# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

# DB utils (usa los tuyos existentes)
from app.database.connection import (
    init_db,
    test_db_connection,
    ensure_database_exists,
)

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Vendedores Service",
    description="Microservicio de Registro y Gestión de Vendedores (JWT + RBAC)",
    version="1.0.1",
)


try:
    from app.routes.vendedores import router as vendedores_router
    app.include_router(vendedores_router)
    logger.info("Router de Vendedores montado")
except Exception as e:
    logger.warning(f"No se pudo montar router Vendedores: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


@app.on_event("startup")
async def startup_event():
    logger.info("Ensuring database exists...")
    try:
        ensure_database_exists()
    except Exception:
        logger.info("Sin credenciales admin; omitiendo creación de BD y continuando.")

    # Reintentos de conexión
    for attempt in range(5):
        if test_db_connection():
            logger.info("Conexión a BD establecida.")
            break
        logger.warning(f"Intento {attempt + 1}/5 fallido. Reintentando en 3s...")
        await asyncio.sleep(3)
    else:
        logger.error("No se pudo conectar a la BD. Continuando sin migraciones.")
        return

    try:
        init_db()
        logger.info("Migraciones/creación de tablas completadas.")
    except Exception as e:
        logger.error(f"Error en init_db(): {e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vendedor-service"}

if __name__ == "__main__":
    import uvicorn
    # workers=1 evita condiciones de carrera
    uvicorn.run(app, host="0.0.0.0", port=8014, workers=1, loop="asyncio")
