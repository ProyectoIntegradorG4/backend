import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.database.connection import get_db, init_db

def test_get_db():
    db = next(get_db())
    assert isinstance(db, Session)
    db.close()

@pytest.mark.asyncio
async def test_init_db():
    with patch('app.models.proveedor.Base.metadata.create_all') as mock_create_all:
        await init_db()
        mock_create_all.assert_called_once()