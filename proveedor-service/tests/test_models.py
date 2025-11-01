"""
Tests para los modelos
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.models.idempotency import IdempotencyKey


def test_idempotency_key_creation():
    """Test creación básica de IdempotencyKey"""
    key = "test-key"
    response = {"status": "success", "data": {"id": 1}}
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    idempotency = IdempotencyKey(
        key=key,
        response=response,
        expires_at=expires_at
    )
    
    assert idempotency.key == key
    assert idempotency.response == response
    assert idempotency.expires_at == expires_at
    # created_at se setea por default, pero no en instancias no guardadas


def test_calculate_expiry():
    """Test método calculate_expiry"""
    now = datetime.now(timezone.utc)
    expiry = IdempotencyKey.calculate_expiry(30)
    
    expected = now + timedelta(minutes=30)
    # Verificar que la diferencia sea menor a 1 segundo (debido a tiempo de ejecución)
    assert abs((expiry - expected).total_seconds()) < 1
    
    # Test con minutos diferentes
    expiry_60 = IdempotencyKey.calculate_expiry(60)
    expected_60 = now + timedelta(minutes=60)
    assert abs((expiry_60 - expected_60).total_seconds()) < 1