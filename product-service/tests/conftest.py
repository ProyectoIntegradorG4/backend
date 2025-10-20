# tests/conftest.py
import os
from importlib import reload
from fastapi.testclient import TestClient

# Asegura que el import sea desde app.main (no desde main suelto)
from app.main import app

# ------------ FIX: cliente único ------------
client = TestClient(app)

def listar_rutas():
    return [r.path for r in app.router.routes]

def descubrir_endpoint_creacion():
    """
    Busca la ruta POST de creación de productos inspeccionando el router,
    para no depender de un prefijo hardcodeado.
    """
    candidates = []
    for r in app.router.routes:
        # FastAPI define el método en .methods y el path en .path
        if getattr(r, "methods", None) and "POST" in r.methods:
            path = getattr(r, "path", "")
            # heurística: termina con /productos
            if path.endswith("/productos"):
                candidates.append(path)
    # Si hay varias, toma la primera por simplicidad
    return candidates[0] if candidates else None
