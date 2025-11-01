from fastapi.testclient import TestClient
from app.main import app

def test_upload_csv_processing_error(monkeypatch):
    # Fuerza error al leer CSV para cubrir el except de "Error al procesar el CSV"
    import app.utils as utils
    def boom(_):
        raise ValueError("Error al leer el CSV: ruptura controlada")
    monkeypatch.setattr("app.main.read_csv", boom)

    client = TestClient(app)
    files = {"file": ("test.csv", b"sku,name\nA1,Prod", "text/csv")}
    r = client.post("/upload-csv", files=files)
    assert r.status_code == 500
    assert "Error al procesar el CSV" in r.text

def test_upload_csv_insert_error_duplicate_sku(client):
    # Inserta dos veces el mismo SKU para provocar la ruta de rollback (500)
    data = (
        "sku,name,description,category,manufacturer,storage_type,"
        "min_shelf_life_months,expiration_date,batch_number,cold_chain_required,"
        "certifications,commercialization_auth,country_regulations,unit_price,"
        "purchase_conditions,delivery_time_hours,external_code,import_id\n"
        "SKU-DUP,Prod,Desc,Cat,Man,Type,6,2025-01-01,B123,false,"
        "Cert,Auth,Reg,100.50,Cond,24,EXT-1,\n"
    )
    files = {"file": ("test.csv", data, "text/csv")}
    c = TestClient(app)

    r1 = c.post("/upload-csv", files=files)
    assert r1.status_code == 201

    r2 = c.post("/upload-csv", files=files)
    assert r2.status_code == 500   # viola unique(sku) -> cubre except de inserción
