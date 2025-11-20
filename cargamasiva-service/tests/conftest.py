# tests/conftest.py
import os
import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# BD temporal para tests (sin tocar tu .env real)
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.database.session import Base, engine, SessionLocal  # noqa: E402
# Importa modelos para registrar metadata antes de create_all
from app.models.product import Producto  # noqa: F401,E402
from app.models.category import CategoriaProducto  # noqa: F401,E402

@pytest.fixture(autouse=True, scope="session")
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
