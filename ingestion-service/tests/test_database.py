# tests/test_database.py
import os
import importlib
import pytest
from sqlalchemy import text

def test_get_database_url_raises_when_missing_env(monkeypatch):
    # No recargues el módulo; solo llama a la función para validar el raise
    from app import database
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        database.get_database_url()

def test_get_engine_uses_sqlite_connect_args(monkeypatch):
    # Fuerza sqlite y valida que el engine conecta y ejecuta un SELECT
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./tmp_cov.db")
    from app import database
    importlib.reload(database)  # recarga con el env fijo
    eng = database.get_engine()
    with eng.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1
