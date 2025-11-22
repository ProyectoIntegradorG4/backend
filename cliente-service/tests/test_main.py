import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock


class TestMain:
    """Tests para main.py"""

    def test_health_check(self):
        """Test: Health check endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cliente-service"
        assert data["version"] == "1.0.3"

    @patch('main.ensure_database_exists')
    @patch('main.test_db_connection')
    @patch('main.init_db')
    @patch('main.SessionLocal')
    def test_startup_event_exitoso(
        self, 
        mock_session_local,
        mock_init_db,
        mock_test_db_connection,
        mock_ensure_database_exists
    ):
        """Test: Startup event ejecuta correctamente"""
        mock_ensure_database_exists.return_value = True
        mock_test_db_connection.return_value = True
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        
        from main import startup_event
        import asyncio
        
        # Ejecutar startup event
        asyncio.run(startup_event())
        
        mock_ensure_database_exists.assert_called_once()
        mock_test_db_connection.assert_called()
        mock_init_db.assert_called_once()

    @patch('main.ensure_database_exists')
    @patch('main.test_db_connection')
    def test_startup_event_sin_conexion_db(
        self,
        mock_test_db_connection,
        mock_ensure_database_exists
    ):
        """Test: Startup event maneja falta de conexión a DB"""
        mock_ensure_database_exists.return_value = True
        mock_test_db_connection.return_value = False
        
        from main import startup_event
        import asyncio
        
        # Ejecutar startup event
        asyncio.run(startup_event())
        
        mock_ensure_database_exists.assert_called_once()
        # Debe intentar conectar 5 veces
        assert mock_test_db_connection.call_count == 5

