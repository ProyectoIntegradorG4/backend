"""
Configuración de pytest para tests de integración del audit-service
"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop para toda la sesión de tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Configuración para tests de integración que usan servicios reales
pytest_plugins = []