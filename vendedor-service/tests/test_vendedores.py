# tests/test_vendedores.py
import pytest

BASE = "/api/vendedores"

def test_listar_vacio(client):
    r = client.get(f"{BASE}")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []

def test_crear_vendedor_ok(client):
    payload = {
        "nombres": "Laura",
        "apellidos": "González",
        "tipoDocumento": "CC",
        "numeroDocumento": "1032456789",
        "email": "laura.gonzalez@empresa.com",
        "telefono": "+57 3001234567",
        "pais": "Colombia",
        "territorioId": "TERR-BOG-NORTE"
    }
    r = client.post(BASE, json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["vendedorId"].startswith("VEN-")
    assert body["estado"] == "ACTIVO"
    assert body["territorioId"] == "TERR-BOG-NORTE"
    assert body["password_generada"] is False

def test_crear_vendedor_duplicado_documento(client):
    # Primero creamos uno
    payload = {
        "nombres": "Ana",
        "apellidos": "Lopez",
        "tipoDocumento": "CC",
        "numeroDocumento": "999",
        "email": "ana@example.com",
        "telefono": None,
        "pais": "Colombia",
        "territorioId": "TERR-BOG-SUR"
    }
    r1 = client.post(BASE, json=payload)
    assert r1.status_code == 201

    # Intentamos duplicar documento
    payload2 = {
        **payload,
        "email": "otro@example.com"
    }
    r2 = client.post(BASE, json=payload2)
    assert r2.status_code == 409

def test_crear_vendedor_duplicado_email(client):
    payload = {
        "nombres": "Carlos",
        "apellidos": "Pardo",
        "tipoDocumento": "CC",
        "numeroDocumento": "888",
        "email": "carlos@example.com",
        "telefono": None,
        "pais": "Colombia",
        "territorioId": "TERR-MED"
    }
    r1 = client.post(BASE, json=payload)
    assert r1.status_code == 201

    # Duplicar email con documento distinto
    payload2 = {
        **payload,
        "numeroDocumento": "777"
    }
    r2 = client.post(BASE, json=payload2)
    assert r2.status_code == 409

def test_listar_con_filtros_orden_y_paginacion(client):
    # Crea algunos vendedores
    datos = [
        {
            "nombres": "Laura",
            "apellidos": "González",
            "tipoDocumento": "CC",
            "numeroDocumento": "100",
            "email": "laura@example.com",
            "telefono": None,
            "pais": "Colombia",
            "territorioId": "TERR-BOG-NORTE"
        },
        {
            "nombres": "Andrés",
            "apellidos": "Zapata",
            "tipoDocumento": "CC",
            "numeroDocumento": "101",
            "email": "andres@example.com",
            "telefono": None,
            "pais": "Colombia",
            "territorioId": "TERR-BOG-NORTE"
        },
        {
            "nombres": "Beatriz",
            "apellidos": "Ríos",
            "tipoDocumento": "CC",
            "numeroDocumento": "102",
            "email": "beatriz@example.com",
            "telefono": None,
            "pais": "Perú",
            "territorioId": "TERR-LIM"
        },
    ]
    for d in datos:
        assert client.post(BASE, json=d).status_code == 201

    # Filtro por país y territorio, orden descendente por nombres
    r = client.get(
        f"{BASE}?pais=Colombia&territorioId=TERR-BOG-NORTE&sort=nombres&order=desc&page=1&page_size=10"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 2
    items = body["items"]
    assert len(items) >= 2
    # nombres en desc (Andrés, Laura) -> Laura debería venir primero
    assert items[0]["nombres"] >= items[1]["nombres"]

def test_detalle_404(client):
    r = client.get(f"{BASE}/VEN-NO-EXISTE")
    assert r.status_code == 404

def test_detalle_ok(client):
    # crea uno y luego pídelo
    payload = {
        "nombres": "Mario",
        "apellidos": "Cano",
        "tipoDocumento": "CC",
        "numeroDocumento": "555",
        "email": "mario@example.com",
        "telefono": None,
        "pais": "Colombia",
        "territorioId": "TERR-CAL"
    }
    r1 = client.post(BASE, json=payload)
    assert r1.status_code == 201
    vid = r1.json()["vendedorId"]

    r2 = client.get(f"{BASE}/{vid}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["vendedorId"] == vid
    assert body["nombres"] == "Mario"
