# tests/test_visits.py
from fastapi import status


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"status": "ok"}


def test_create_visit_success(client):
    payload = {
        "client_id": 987,
        "visit_datetime": "2025-11-08T10:30:00",
        "title": "Visita inicial",
        "notes": "Se revisaron condiciones de la visita",
    }

    resp = client.post("/visits", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert "id" in data
    assert data["message"] == "Visita registrada exitosamente"


def test_create_visit_missing_client_id(client):
    payload = {
        "visit_datetime": "2025-11-08T10:30:00",
        "title": "Sin cliente",
    }

    resp = client.post("/visits", json=payload)
    # Falta client_id -> tu código lanza HTTP 422
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_visit_with_date_and_time(client):
    payload = {
        "client_id": 123,
        "date": "2025-11-08",
        "time": "10:30",
        "title": "Visita con fecha/hora separados",
    }

    resp = client.post("/visits", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert "id" in data


def test_upload_evidence_image_success(client):
    # 1) Crear visita primero
    payload = {
        "client_id": 999,
        "visit_datetime": "2025-11-08T11:00:00",
        "title": "Visita con evidencia",
        "notes": "Se tomaron fotos",
    }
    resp_visit = client.post("/visits", json=payload)
    assert resp_visit.status_code == status.HTTP_201_CREATED

    visit_id = resp_visit.json()["id"]

    # 2) Subir evidencia como imagen (parametro 'image' del endpoint)
    files = {
        "image": ("imagen.jpg", b"fake-image-content", "image/jpeg")
    }

    resp = client.post(f"/visits/{visit_id}/evidence", files=files)
    assert resp.status_code == status.HTTP_201_CREATED

    data = resp.json()
    assert "items" in data
    assert data["count"] == 1
    item = data["items"][0]
    assert item["filename"].endswith(".jpg")
    assert item["content_type"].startswith("image/")


def test_upload_evidence_no_files(client):
    # 1) Crear visita
    payload = {
        "client_id": 555,
        "visit_datetime": "2025-11-08T12:00:00",
        "title": "Sin evidencias",
    }
    resp_visit = client.post("/visits", json=payload)
    assert resp_visit.status_code == status.HTTP_201_CREATED
    visit_id = resp_visit.json()["id"]

    # 2) Llamar al endpoint sin archivos
    resp = client.post(f"/visits/{visit_id}/evidence")
    # según tu código, si no hay inputs, devuelve 422
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_visits_by_client(client):
    client_id = 777

    payload1 = {
        "client_id": client_id,
        "visit_datetime": "2025-11-08T09:00:00",
        "title": "Visita 1",
    }
    payload2 = {
        "client_id": client_id,
        "visit_datetime": "2025-11-08T10:00:00",
        "title": "Visita 2",
    }

    resp1 = client.post("/visits", json=payload1)
    resp2 = client.post("/visits", json=payload2)

    assert resp1.status_code == status.HTTP_201_CREATED
    assert resp2.status_code == status.HTTP_201_CREATED

    # Ruta real según tu router:
    # @router.get("/api/v1/visits/client/{client_id}", ...)
    resp_list = client.get(f"/api/v1/visits/client/{client_id}")
    assert resp_list.status_code == status.HTTP_200_OK

    data = resp_list.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_get_visit_not_found(client):
    # Ruta real según tu router:
    # @router.get("/api/v1/visits/{visit_id}", ...)
    resp = client.get("/api/v1/visits/999999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
