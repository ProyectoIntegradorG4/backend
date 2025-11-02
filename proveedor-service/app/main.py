from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import proveedores

app = FastAPI(
    title="Proveedor Service",
    description="API para gestión de proveedores",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy"})

app.include_router(proveedores.router, prefix="/api/proveedores")