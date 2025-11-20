"""
Tests simplificados de integración para endpoints de visitas
Usan mocks completos para evitar problemas de sesión de BD
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.models.visita import (
    Visita, RutaVisita, EstadoVisita, PrioridadVisita, OrigenRuta,
    VisitaResponse, VisitaListResponse, RutaVisitaResponse, VisitaEnRuta
)
from datetime import date, time, datetime, timezone
from decimal import Decimal


class TestVisitasAPISimple:
    """Tests simplificados de API con mocks completos"""

    def test_health_check(self, client):
        """Test del endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_visitas_por_fecha_mock(self, client):
        """Test: Listar visitas por fecha (con mock)"""
        fecha = date(2025, 11, 25)
        now = datetime.now(timezone.utc)
        
        # Mock de respuesta del servicio
        mock_visitas = [
            Visita(
                visita_id=1,
                gerente_id=1,
                cliente_id=1,
                fecha_visita=fecha,
                duracion_estimada_minutos=60,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.MEDIA,
                fecha_registro=now,
                fecha_actualizacion=now
            ),
            Visita(
                visita_id=2,
                gerente_id=1,
                cliente_id=2,
                fecha_visita=fecha,
                duracion_estimada_minutos=45,
                estado=EstadoVisita.PROGRAMADA,
                prioridad=PrioridadVisita.ALTA,
                fecha_registro=now,
                fecha_actualizacion=now
            )
        ]
        
        with patch('app.services.visita_service.VisitaService.get_visitas_by_gerente_fecha', return_value=mock_visitas):
            response = client.get(f"/api/v1/visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["visitas"]) == 2

    def test_get_ruta_mock_sin_visitas(self, client):
        """Test: Consultar ruta sin visitas (con mock)"""
        fecha = date(2025, 11, 25)
        
        # Mock de servicio que retorna None (no hay ruta)
        with patch('app.services.visita_service.VisitaService.get_ruta_by_gerente_fecha', return_value=None):
            # Mock de get_visitas que retorna lista vacía
            with patch('app.services.visita_service.VisitaService.get_visitas_by_gerente_fecha', return_value=[]):
                # Mock de crear_ruta_vacia
                mock_ruta = RutaVisita(
                    ruta_id=1,
                    gerente_id=1,
                    fecha_ruta=fecha,
                    version_ruta=1,
                    activa=True,
                    origen_ruta=OrigenRuta.PLANIFICADA,
                    fecha_calculo=datetime.now(timezone.utc)
                )
                with patch('app.services.visita_service.VisitaService.crear_ruta_vacia', return_value=mock_ruta):
                    response = client.get(f"/api/v1/rutas-visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cantidad_visitas"] == 0
        assert data["visitas"] == []

    def test_recalcular_ruta_sin_visitas(self, client):
        """Test: Recalcular ruta sin visitas retorna error 404"""
        fecha = date(2025, 11, 30)
        
        # Mock que no hay visitas
        with patch('app.services.visita_service.VisitaService.get_visitas_by_gerente_fecha', return_value=[]):
            request_data = {
                "fecha": str(fecha),
                "gerente_id": 1
            }
            
            response = client.post("/api/v1/rutas-visitas/recalcular", json=request_data)
        
        assert response.status_code == 404
        assert "No hay visitas" in response.json()["detail"]

