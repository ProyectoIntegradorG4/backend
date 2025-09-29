"""
Tests de integración para Audit Service usando servicios reales
Estos tests se ejecutan en contenedores Docker con servicios activos
"""
import pytest
import asyncio
import httpx
from datetime import datetime, timezone
import uuid


class TestAuditServiceIntegration:
    """Tests de integración con servicios reales."""

    @pytest.mark.asyncio
    async def test_audit_service_health(self):
        """Test que verifica que el audit service esté funcionando."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://audit-service:8003/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "audit-service"

    @pytest.mark.asyncio
    async def test_audit_log_registration_success(self):
        """Test de registro exitoso de evento de auditoría."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Datos del evento de auditoría
            audit_data = {
                "event": "user_register",
                "request": {
                    "nombreusuario": "Usuario Test",
                    "useremail": "audit_test@test.com",
                    "nit": "901234567"
                },
                "outcome": "success",
                "action": "email",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auditid": str(uuid.uuid4())
            }
            
            # Registrar evento
            response = await client.post(
                "http://audit-service:8003/audit/register",
                json=audit_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["logged"] is True

    @pytest.mark.asyncio
    async def test_audit_log_registration_failure(self):
        """Test de registro de evento de auditoría de fallo."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Datos del evento de auditoría de fallo
            audit_data = {
                "event": "user_register",
                "request": {
                    "nombreusuario": "Usuario Test Fallo",
                    "useremail": "audit_fail_test@test.com",
                    "nit": "999999999"
                },
                "outcome": "fail",
                "action": "nit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auditid": str(uuid.uuid4())
            }
            
            # Registrar evento
            response = await client.post(
                "http://audit-service:8003/audit/register",
                json=audit_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["logged"] is True

    @pytest.mark.asyncio
    async def test_audit_log_validation_errors(self):
        """Test que verifica la validación de datos en audit service."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Test 1: Outcome inválido
            invalid_data = {
                "event": "test_event",
                "request": {
                    "nombreusuario": "Test",
                    "useremail": "test@test.com",
                    "nit": "123"
                },
                "outcome": "invalid_outcome",  # Valor inválido
                "action": "email",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auditid": str(uuid.uuid4())
            }
            
            response = await client.post(
                "http://audit-service:8003/audit/register",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422
            
            # Test 2: Action inválido
            invalid_data["outcome"] = "success"
            invalid_data["action"] = "invalid_action"  # Valor inválido
            
            response = await client.post(
                "http://audit-service:8003/audit/register",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_multiple_audit_logs(self):
        """Test de registro de múltiples eventos de auditoría."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Registrar múltiples eventos
            events = []
            for i in range(3):
                audit_data = {
                    "event": f"test_event_{i}",
                    "request": {
                        "nombreusuario": f"Usuario Test {i}",
                        "useremail": f"test_{i}@test.com",
                        "nit": "901234567"
                    },
                    "outcome": "success" if i % 2 == 0 else "fail",
                    "action": "email",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "auditid": str(uuid.uuid4())
                }
                
                response = await client.post(
                    "http://audit-service:8003/audit/register",
                    json=audit_data,
                    headers={"Content-Type": "application/json"}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["logged"] is True
                events.append(audit_data)
            
            # Verificar que todos los eventos fueron diferentes
            assert len(set(event["auditid"] for event in events)) == 3

    @pytest.mark.asyncio
    async def test_audit_with_complex_request_data(self):
        """Test de auditoría con datos de request complejos."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Datos de request más complejos
            complex_request = {
                "nombreusuario": "Hospital Complejo de Pruebas",
                "useremail": "complex.test@hospital.com",
                "nit": "901234567",
                "additional_data": {
                    "ip_address": "192.168.1.100",
                    "user_agent": "Test User Agent",
                    "timestamp_request": datetime.now(timezone.utc).isoformat()
                }
            }
            
            audit_data = {
                "event": "complex_user_register",
                "request": complex_request,
                "outcome": "success",
                "action": "other",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auditid": str(uuid.uuid4())
            }
            
            response = await client.post(
                "http://audit-service:8003/audit/register",
                json=audit_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["logged"] is True

    @pytest.mark.asyncio
    async def test_audit_service_concurrent_requests(self):
        """Test de concurrencia en el audit service."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            
            async def create_audit_log(index):
                audit_data = {
                    "event": f"concurrent_test_{index}",
                    "request": {
                        "nombreusuario": f"Concurrent User {index}",
                        "useremail": f"concurrent_{index}@test.com",
                        "nit": "901234567"
                    },
                    "outcome": "success",
                    "action": "email",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "auditid": str(uuid.uuid4())
                }
                
                response = await client.post(
                    "http://audit-service:8003/audit/register",
                    json=audit_data,
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code
            
            # Ejecutar múltiples requests concurrentes
            tasks = [create_audit_log(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            # Todos deben ser exitosos
            assert all(status == 201 for status in results)