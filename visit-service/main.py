# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from app.database.session import init_db

from app.routes.visits import router as visits_router

app = FastAPI(title="visit-service", version="1.0.0")

# === CORS global ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta si luego quieres restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

# === Healthcheck ===
@app.get("/health")
async def health():
    return {"status": "ok"}

# === Rutas principales ===
app.include_router(visits_router)

# === Archivos estáticos (solo si backend NO es S3) ===
FILES_BACKEND = os.getenv("FILES_BACKEND", "local").lower()
if FILES_BACKEND != "s3":
    FILES_DIR = os.getenv("FILES_DIR", "/data/visits")
    os.makedirs(FILES_DIR, exist_ok=True)
    app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")


