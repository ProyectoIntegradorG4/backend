from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import proveedores
from app.database.connection import init_db
import os

app = FastAPI(
    title="Proveedor Service",
    description="Microservicio de gestión de proveedores médicos",
    version="1.0.2"
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
app.include_router(proveedores.router, prefix="/api/v1/proveedores", tags=["proveedores"])

# Debug: imprimir todas las rutas registradas
@app.on_event("startup")
async def print_routes():
    print("\nRegistered routes:")
    for route in app.routes:
        print(f"{route.methods} {route.path}")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "proveedor-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("PROVEEDOR_SERVICE_PORT", 8006)),
        workers=1,
        loop="asyncio",
        access_log=False,
        log_level="warning"
    )
