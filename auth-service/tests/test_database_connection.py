import pytest
from app.database import connection
from sqlalchemy.engine.base import Engine

def test_engine_is_created():
    assert isinstance(connection.engine, Engine)
    assert connection.engine.pool.size() == 20
    assert connection.engine.pool._max_overflow == 40

def test_session_local():
    session = connection.SessionLocal()
    try:
        assert session.bind == connection.engine
    finally:
        session.close()

def test_get_db_generator():
    gen = connection.get_db()
    db = next(gen)
    assert db.bind == connection.engine
    gen.close()

def test_init_db_runs():
    # Solo verifica que no lance excepción
    import asyncio
    asyncio.run(connection.init_db())
