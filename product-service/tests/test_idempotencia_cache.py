# tests/test_idempotencia_cache.py
import json
from types import SimpleNamespace
from tests.conftest import client, descubrir_endpoint_creacion

def _fake_entity():
    return SimpleNamespace(
        productoId="11111111-1111-1111-1111-111111111111",
        nombre="Vacuna",
        descripcion="",
        categoriaId="CAT-IMM-001",
        subcategoria=None,
        laboratorio=None,
        principioActivo=None,
        concentracion=None,
        formaFarmaceutica="suspension_inyectable",
        registroSanitario="INVIMA 2025M-000123-R1",
        requierePrescripcion=False,
        codigoBarras="7701234567897",
    )

VALID_PAYLOAD = {
    "nombre": "Vacuna XYZ 10ml",
    "descripcion": "Suspensión inyectable...",
    "categoriaId": "CAT-IMM-001",
    "subcategoria": "Vacunas pediátricas",
    "laboratorio": "BioPharma LATAM",
    "principioActivo": "Antígeno X",
    "concentracion": "10 ml",
    "formaFarmaceutica": "suspension_inyectable",
    "registroSanitario": "INVIMA 2025M-000123-R1",
    "requierePrescripcion": True,
    "codigoBarras": "7701234567897",
}

def test_idempotencia_cache_hit(monkeypatch):
    create_path = descubrir_endpoint_creacion()
    assert create_path, "No pude inferir el endpoint de creación."

    class FakeRedis:
        def __init__(self): self.data = {}
        def get(self, k): return self.data.get(k)
        def set(self, k, v, ex=None): self.data[k] = v
        def setex(self, k, ttl, v): self.data[k] = v  # <- necesario para la ruta

    import app.routes.products as routes
    fake_r = FakeRedis()
    monkeypatch.setattr(routes, "redis_client", fake_r, raising=True)

    calls = {"n": 0}
    import app.service.product_service as ps
    def fake_crear(_db, _data):
        calls["n"] += 1
        return _fake_entity(), True
    monkeypatch.setattr(ps.ProductoService, "crear_producto", staticmethod(fake_crear))

    headers = {"X-User-Role": "Administrador de Compras", "X-Idempotency-Key": "k1"}

    r1 = client.post(create_path, json=VALID_PAYLOAD, headers=headers)
    r2 = client.post(create_path, json=VALID_PAYLOAD, headers=headers)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert calls["n"] == 1  # la segunda debe salir del cache

def test_error_400_en_creacion(monkeypatch):
    create_path = descubrir_endpoint_creacion()
    assert create_path, "No pude inferir el endpoint de creación."

    import app.service.product_service as ps
    def fake_bad(_db, _data):
        # fuerza que la ruta responda 400 (manejada en products.py)
        raise ValueError("Datos inválidos")
    monkeypatch.setattr(ps.ProductoService, "crear_producto", staticmethod(fake_bad))

    headers = {"X-User-Role": "Administrador de Compras"}

    # Enviamos payload VÁLIDO para evitar 422 por validación
    r = client.post(create_path, json=VALID_PAYLOAD, headers=headers)
    assert r.status_code == 400

