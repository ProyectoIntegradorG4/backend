import pandas as pd
import io
import json

CSV_HEADERS = (
    "sku,name,description,category,manufacturer,storage_type,"
    "min_shelf_life_months,expiration_date,batch_number,cold_chain_required,"
    "certifications,commercialization_auth,country_regulations,unit_price,"
    "purchase_conditions,delivery_time_hours,external_code,import_id\n"
)

CSV_ROW = (
    "SKU-1,Test Prod,Desc,Cat,Man,Type,6,2025-01-01,B123,false,"
    "Cert,Auth,Reg,100.50,Cond,24,EXT-1,\n"
)


def test_upload_csv_success(client):
    data = CSV_HEADERS + CSV_ROW
    files = {"file": ("test.csv", data, "text/csv")}

    resp = client.post("/upload-csv", files=files)
    assert resp.status_code == 201

    body = resp.json()
    assert body["summary"]["total_products"] == 1
    assert "categories_count" in body["summary"]
    assert "cold_chain_required_count" in body["summary"]
    assert "avg_unit_price" in body["summary"]


def test_upload_missing_column(client):
    data = "sku,name\nA1,Product Test"
    files = {"file": ("test.csv", data, "text/csv")}

    resp = client.post("/upload-csv", files=files)
    assert resp.status_code == 400
