from fastapi import FastAPI
from app.routes import nit_validation
from app.database.connection import init_db

app = FastAPI(
    title="NIT Validation Service",
    description="Microservicio para validación de NIT contra instituciones asociadas",
    version="1.0.0"
)

# Incluir rutas
app.include_router(nit_validation.router, prefix="/api/v1", tags=["nit-validation"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nit-validation-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)