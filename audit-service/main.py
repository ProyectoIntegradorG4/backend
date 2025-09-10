from fastapi import FastAPI
# from app.routes import audits
from app.database.connection import init_db

app = FastAPI(
    title="Audit Service",
    description="Microservicio para auditoría y logs del sistema",
    version="1.0.0"
)

# Solo incluir health check por ahora
# app.include_router(audits.router, prefix="/api/v1", tags=["audits"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "audit-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)