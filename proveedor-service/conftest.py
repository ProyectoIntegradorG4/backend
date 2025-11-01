"""
Configuración de pytest para las pruebas
"""
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Crear un event loop para pytest-asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
