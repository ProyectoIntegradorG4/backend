from fastapi import FastAPI
from app.database.connection import init_db

app = FastAPI(
    title="Tax Service",
    description="Microservicio para gestión de impuestos",
    version="1.0.0"
)

# Las rutas se agregarán posteriormente
# app.include_router(taxes.router, prefix="/api/v1", tags=["taxes"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tax-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)