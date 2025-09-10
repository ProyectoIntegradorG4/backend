from fastapi import FastAPI
from app.routes import users
from app.database.connection import init_db

app = FastAPI(
    title="User Service",
    description="Microservicio para gestión de usuarios",
    version="1.0.0"
)

# Incluir rutas
app.include_router(users.router, prefix="/api/v1", tags=["users"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)