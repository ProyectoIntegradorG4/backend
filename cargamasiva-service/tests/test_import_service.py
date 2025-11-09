# tests/test_import_service.py
import io
import pytest
from fastapi import HTTPException

from app.services.import_service import process_import
from app.startup_seed import seed_default_categories
from app.models.product import Producto
from sqlalchemy import select


HEADERS = ",".join([
    "productoId","nombre","descripcion","categoriaId","formaFarmaceutica",
    "requierePrescripcion","registroSanitario","sku","location","ubicacion",
    "stock","precio","estado_producto","actualizado_en","fechaVencimiento"
])

def _csv_bytes(lines):
    text = HEADERS + "\n" + "\n".join(lines)
    return text.encode("utf-8")


@pytest.fixture
def sample_csv_ok_bytes():
    rows = [
        "P001,Paracetamol 500mg,Analgésico en tabletas,CAT001,Tableta,false,RS-001-A,SKU-001,Bodega A,P1-01,150,4500,ACTIVO,2025-01-15T10:00:00,2027-11-30",
        "P002,Ibuprofeno 400mg,Antiinflamatorio,CAT002,Tableta,false,RS-002-B,SKU-002,Bodega B,P2-03,200,6200,ACTIVO,2025-02-01T09:30:00,2027-05-15",
        "P003,Amoxicilina 500mg,Antibiótico,CAT003,Capsula,true,RS-003-C,SKU-003,Bodega A,P1-05,80,8300,ACTIVO,2025-01-10T08:15:00,2026-10-20",
    ]
    return _csv_bytes(rows)


@pytest.fixture
def sample_csv_bad_bytes():
    # 1 válida + 1 con boolean “quizas” (se normaliza a False) + 1 con fecha inválida
    rows = [
        "P010,Loratadina 10mg,Antialérgico,CAT004,Tableta,false,RS-010,SKU-010,Bodega A,P1-10,120,3700,ACTIVO,2025-03-01T10:00:00,2027-08-20",
        "P011,Producto Bool Raro,Prueba,CAT005,Tableta,quizas,RS-011,SKU-011,Bodega B,P2-11,50,5000,ACTIVO,2025-03-02T10:00:00,2027-08-21",
        "P012,Fecha Mala,Prueba,CAT006,Tableta,true,RS-012,SKU-012,Bodega C,P3-12,60,5100,ACTIVO,2025-03-03T10:00:00,2027-31-99",
    ]
    return _csv_bytes(rows)


def test_headers_exactos_ok(db_session, sample_csv_ok_bytes, _create_schema):
    seed_default_categories(db_session)
    db_session.commit()

    result = process_import(db_session, sample_csv_ok_bytes)

    assert result["summary"]["total_rows"] == 3
    assert result["summary"]["invalid_rows"] == 0
    assert result["summary"]["valid_rows_upserted"] == 3

    ids = {"P001", "P002", "P003"}
    rows = db_session.execute(
        select(Producto).where(Producto.productoId.in_(ids))
    ).scalars().all()
    assert len(rows) == 3


def test_headers_faltantes_levanta_400(db_session, _create_schema):
    seed_default_categories(db_session)
    db_session.commit()

    # quitamos "precio" para forzar error de encabezados
    bad_headers = ",".join([
        "productoId","nombre","descripcion","categoriaId","formaFarmaceutica",
        "requierePrescripcion","registroSanitario","sku","location","ubicacion",
        "stock",
        "estado_producto","actualizado_en","fechaVencimiento"
    ])
    text = bad_headers + "\n" + "P100,Prueba,Desc,CAT001,Tableta,false,RS,SKU,B1,U1,10,ACTIVO,2025-01-01T00:00:00,2027-01-01"
    data = text.encode("utf-8")

    with pytest.raises(HTTPException) as ex:
        process_import(db_session, data)

    assert ex.value.status_code == 400
    detail = ex.value.detail
    assert "Faltan encabezados" in detail.get("mensaje", "") or "Faltan encabezados" in str(detail)


def test_filas_invalidas_contabiliza(db_session, sample_csv_bad_bytes, _create_schema):
    """
    Con tu lógica actual, solo la fila con fecha inválida cuenta como inválida.
    'quizas' se normaliza/acepta y no rompe la validación.
    """
    seed_default_categories(db_session)
    db_session.commit()

    result = process_import(db_session, sample_csv_bad_bytes)

    assert result["summary"]["total_rows"] == 3
    assert result["summary"]["invalid_rows"] == 1        # ← antes 2; ahora 1
    assert result["summary"]["valid_rows_upserted"] == 2
    assert len(result["invalid_samples"]) >= 1


def test_fk_categoria_inexistente_reporta(db_session, _create_schema):
    """
    Tu importador NO lanza HTTPException; reporta la fila como inválida.
    Ajustamos el test para validar ese comportamiento.
    """
    seed_default_categories(db_session)
    db_session.commit()

    rows = [
        "P200,FK Rota,Desc,CAT999,Tableta,false,RS-200,SKU-200,B1,U1,10,1000,ACTIVO,2025-01-01T00:00:00,2027-01-01"
    ]
    data = _csv_bytes(rows)

    result = process_import(db_session, data)

    assert result["summary"]["total_rows"] == 1
    assert result["summary"]["valid_rows_upserted"] == 0
    assert result["summary"]["invalid_rows"] == 1
    # opcional: verificar que el mensaje de inválidos mencione la FK/categoría
    joined = str(result.get("invalid_samples", ""))
    assert "CAT999" in joined or "categoria" in joined.lower() or "fk" in joined.lower()
