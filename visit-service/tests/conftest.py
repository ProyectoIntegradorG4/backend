# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ======================================
# 1) Configuración de la BD de pruebas
# ======================================

TEST_DB_URL = "sqlite:///./test_visits.db"

# Definir variables de entorno ANTES de importar main
os.environ.setdefault("VISIT_DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("FILES_DIR", "./test_files")

from main import app  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.services.rbac import (  # noqa: E402
    require_auth_token,
    require_role_admincompras_header,
    require_role_admincompras,
)

# Engine y Session para SQLite de pruebas
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ======================================
# 2) Esquema mínimo para las tablas
# ======================================

def init_db():
    """
    Crea el esquema mínimo para los tests, alineado con app/models/visit.py,
    sin tocar nada del código del microservicio.
    """
    with engine.begin() as conn:
        # Limpiar por si ya existía
        conn.exec_driver_sql("DROP TABLE IF EXISTS clients_visits_evidence")
        conn.exec_driver_sql("DROP TABLE IF EXISTS clients_visits")

        conn.exec_driver_sql(
            """
            CREATE TABLE clients_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                account_mgr_id INTEGER NOT NULL,
                visit_datetime DATETIME NOT NULL,
                title VARCHAR(120),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
            """
        )

        conn.exec_driver_sql(
            """
            CREATE TABLE clients_visits_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                size_bytes INTEGER NOT NULL,
                storage_key VARCHAR(512) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY(visit_id) REFERENCES clients_visits(id) ON DELETE CASCADE
            )
            """
        )


# ======================================
# 3) Override de get_db para tests
# ======================================

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ======================================
# 4) Overrides de RBAC para tests
# ======================================

class DummyCurrentUser:
    def __init__(self, user_id: int = 1):
        self.user_id = user_id


# require_auth_token normalmente es async → lo mantenemos async
async def override_require_auth_token():
    """
    Simula un usuario autenticado con id=1.
    """
    return DummyCurrentUser(user_id=1)


def override_require_role_admincompras_header():
    """
    En producción valida header/rol.
    En tests, simplemente no bloquea.
    """
    return None


def override_require_role_admincompras():
    """
    En producción valida rol ADMINCOMPRAS (u otro).
    En tests, simplemente no bloquea.
    """
    return None


# Aplicar overrides solo en el contexto de pruebas
app.dependency_overrides[require_auth_token] = override_require_auth_token
app.dependency_overrides[require_role_admincompras_header] = override_require_role_admincompras_header
app.dependency_overrides[require_role_admincompras] = override_require_role_admincompras


# ======================================
# 5) Fixtures de pytest
# ======================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Se ejecuta una vez por sesión de tests.
    Crea test_visits.db y el esquema necesario.
    """
    # Empezar siempre limpio
    if os.path.exists("test_visits.db"):
        os.remove("test_visits.db")

    files_dir = os.environ.get("FILES_DIR", "./test_files")
    os.makedirs(files_dir, exist_ok=True)

    init_db()
    yield

    # Si quieres borrar al final, descomenta:
    # if os.path.exists("test_visits.db"):
    #     os.remove("test_visits.db")


@pytest.fixture
def client():
    """
    Cliente de pruebas para usar en los tests.
    """
    return TestClient(app)
