import os
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ---------- utilidades ----------
def _listar_rutas():
    rutas = []
    for r in app.router.routes:
        try:
            methods = sorted(getattr(r, "methods", []))
            path = getattr(r, "path", "")
            rutas.append(f"{methods} {path}")
        except Exception:
            pass
    return "\n".join(rutas)

def _descubrir_endpoint_creacion():
    preferido = os.getenv("PRODUCTS_BASE_PATH")
    if preferido:
        return preferido.rstrip("/")
    candidatos = []
    for r in app.router.routes:
        methods = getattr(r, "methods", set())
        path = getattr(r, "path", "")
        if not methods or "POST" not in methods:
            continue
        if "{" in path or "}" in path:
            continue
        low = path.lower()
        if "producto" in low or "product" in low:
            candidatos.append(path)
    if candidatos:
        return candidatos[0].rstrip("/")
    return "/api/productos"   # fallback común

# ---------- test ----------
def test_creacion_exitosa_producto(monkeypatch):
    create_path = _descubrir_endpoint_creacion()
    assert create_path, f"No pude inferir el endpoint de creación.\nRutas:\n{_listar_rutas()}"

    # Parchear la capa de servicio para NO ir a la DB
    import app.service.product_service as ps

    def fake_crear_producto(db, data: dict):
        entity = SimpleNamespace(
            # 👇 UUID válido en vez de "9999"
            productoId="11111111-1111-1111-1111-111111111111",
            nombre=data.get("nombre"),
            descripcion=data.get("descripcion"),
            categoriaId=data.get("categoriaId"),
            subcategoria=data.get("subcategoria"),
            laboratorio=data.get("laboratorio"),
            principioActivo=data.get("principioActivo"),
            concentracion=data.get("concentracion"),
            formaFarmaceutica=data.get("formaFarmaceutica"),
            registroSanitario=data.get("registroSanitario"),
            requierePrescripcion=data.get("requierePrescripcion", False),
            codigoBarras=data.get("codigoBarras"),
        )
        requiere_cadena_frio = True
        return entity, requiere_cadena_frio
    
    def test_error_en_creacion(monkeypatch):
        import app.service.product_service as ps

        def fake_crear_producto(db, data: dict):
            raise ValueError("Categoría inválida")

        monkeypatch.setattr(ps.ProductoService, "crear_producto", staticmethod(fake_crear_producto))

        payload = {
            "nombre": "Vacuna DEF",
            "descripcion": "Prueba de error",
            "categoriaId": "INVALIDA",
        }
        headers = {"X-User-Role": "Administrador de Compras"}
        resp = client.post("/api/productos", json=payload, headers=headers)
        assert resp.status_code == 400
        assert "Categoría inválida" in resp.text

    def test_falla_por_rol_incorrecto():
        payload = {"nombre": "Producto sin permisos"}
        headers = {"X-User-Role": "Analista de Cartera"}
        resp = client.post("/api/productos", json=payload, headers=headers)
        assert resp.status_code == 403
    
    def test_idempotencia(monkeypatch):
        import app.service.product_service as ps
        from types import SimpleNamespace

        def fake_crear_producto(db, data):
            return SimpleNamespace(productoId="11111111-1111-1111-1111-111111111111"), True

        monkeypatch.setattr(ps.ProductoService, "crear_producto", staticmethod(fake_crear_producto))

        headers = {
            "X-User-Role": "Administrador de Compras",
            "X-Idempotency-Key": "idemp-1",
        }
        payload = {"nombre": "Vacuna repetida"}
        r1 = client.post("/api/productos", json=payload, headers=headers)
        r2 = client.post("/api/productos", json=payload, headers=headers)
        assert r1.status_code == 201
        assert r2.status_code in (200, 201)


    monkeypatch.setattr(ps.ProductoService, "crear_producto", staticmethod(fake_crear_producto))

    payload = {
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
        "codigoBarras": "7701234567896",
    }

    headers = {
        "X-User-Role": "Administrador de Compras",  # literal que valida tu servicio
        "X-Idempotency-Key": "abc-123",
    }

    resp = client.post(create_path, json=payload, headers=headers)

    assert resp.status_code == 201, (
        f"{resp.status_code} => {resp.text}\n"
        f"Intenté: {create_path}\n"
        f"Rutas disponibles:\n{_listar_rutas()}"
    )

    data = resp.json()
    # Aserciones mínimas acordadas
    assert data["categoriaId"] == "CAT-IMM-001"
    assert data.get("requiereCadenaFrio") is True
    assert data.get("sku_visible", "").startswith("PROD-")
