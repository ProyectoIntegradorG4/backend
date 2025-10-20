"""
Tests unitarios para AuditClient
"""
import pytest
from app.services.audit_client import AuditClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_log_user_event_success():
    client = AuditClient()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.text = ""
        result = await client.log_user_event(
            event="user_register",
            user_data={"nombre": "Test", "email": "test@test.com", "nit": "123"},
            outcome="success",
            action="email"
        )
        assert result is True

@pytest.mark.asyncio
async def test_log_user_event_failure():
    client = AuditClient()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"
        result = await client.log_user_event(
            event="user_register",
            user_data={"nombre": "Test", "email": "test@test.com", "nit": "123"},
            outcome="fail",
            action="email"
        )
        assert result is False

@pytest.mark.asyncio
async def test_log_user_register_success():
    client = AuditClient()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.text = ""
        result = await client.log_user_register_success(
            user_data={"nombre": "Test", "email": "test@test.com", "nit": "123"},
            user_id=1,
            institucion_id=2
        )
        assert result is True

@pytest.mark.asyncio
async def test_log_user_register_error():
    client = AuditClient()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.text = ""
        result = await client.log_user_register_error(
            user_data={"nombre": "Test", "email": "test@test.com", "nit": "123"},
            error_type="duplicado",
            error_details="El usuario ya existe",
            action="email"
        )
        assert result is True
