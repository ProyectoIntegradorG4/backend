"""
Tests para manejo de errores y casos edge
Diseñados para aumentar cobertura de código a >80%
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.visita_service import VisitaService
from app.models.visita import (
    Visita, RutaVisita, VisitaCreate, VisitaUpdate,
    EstadoVisita, PrioridadVisita, OrigenRuta
)
from fastapi import HTTPException
from datetime import date, time, datetime, timezone
from decimal import Decimal
import httpx


class TestErrorHandling:
    """Tests de manejo de errores para aumentar cobertura"""

    @pytest.mark.asyncio
    async def test_get_cliente_info_error_500(self, db_session):
        """Test: Manejo de error 500 de cliente-service"""
        service = VisitaService(db_session)
        
        # Mock de respuesta con código 500
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            result = await service.get_cliente_info(cliente_id=1)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cliente_info_exception(self, db_session):
        """Test: Manejo de excepción de conexión"""
        service = VisitaService(db_session)
        
        # Mock que lanza excepción
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_http.return_value = mock_client
            
            result = await service.get_cliente_info(cliente_id=1)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verificar_gerente_tiene_cliente_error_500(self, db_session):
        """Test: Error al verificar acceso del gerente"""
        service = VisitaService(db_session)
        
        # Mock de respuesta con código 500
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            result = await service.verificar_gerente_tiene_cliente(gerente_id=1, cliente_id=1)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_verificar_gerente_tiene_cliente_exception(self, db_session):
        """Test: Excepción al verificar acceso"""
        service = VisitaService(db_session)
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_http.return_value = mock_client
            
            result = await service.verificar_gerente_tiene_cliente(gerente_id=1, cliente_id=1)
        
        assert result is False

    def test_get_visita_by_id_exception(self, db_session):
        """Test: Manejo de excepción al obtener visita"""
        service = VisitaService(db_session)
        
        # Forzar excepción en la query
        with patch.object(db_session, 'query', side_effect=Exception("Database error")):
            result = service.get_visita_by_id(visita_id=1, gerente_id=1)
        
        assert result is None

    def test_update_visita_no_encontrada(self, db_session):
        """Test: Actualizar visita que no existe"""
        service = VisitaService(db_session)
        
        update_data = VisitaUpdate(prioridad=PrioridadVisita.ALTA)
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_visita(visita_id=99999, gerente_id=1, visita_update=update_data)
        
        assert exc_info.value.status_code == 404

    def test_update_visita_exception(self, db_session):
        """Test: Excepción al actualizar visita"""
        service = VisitaService(db_session)
        
        # Crear visita
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        update_data = VisitaUpdate(prioridad=PrioridadVisita.ALTA)
        
        # Forzar excepción en commit
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises(HTTPException) as exc_info:
                service.update_visita(visita_id=1, gerente_id=1, visita_update=update_data)
            
            assert exc_info.value.status_code == 500

    def test_delete_visita_exception(self, db_session):
        """Test: Excepción al cancelar visita"""
        service = VisitaService(db_session)
        
        # Crear visita
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        # Forzar excepción
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises(HTTPException) as exc_info:
                service.delete_visita(visita_id=1, gerente_id=1)
            
            assert exc_info.value.status_code == 500

    def test_get_ruta_by_gerente_fecha_exception(self, db_session):
        """Test: Manejo de excepción al obtener ruta"""
        service = VisitaService(db_session)
        
        with patch.object(db_session, 'query', side_effect=Exception("Database error")):
            result = service.get_ruta_by_gerente_fecha(gerente_id=1, fecha=date(2025, 11, 25))
        
        assert result is None

    def test_crear_ruta_vacia_exception(self, db_session):
        """Test: Excepción al crear ruta vacía"""
        service = VisitaService(db_session)
        
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises(HTTPException) as exc_info:
                service.crear_ruta_vacia(gerente_id=1, fecha=date(2025, 11, 25))
            
            assert exc_info.value.status_code == 500

    def test_get_visitas_by_gerente_fecha_exception(self, db_session):
        """Test: Excepción al obtener visitas"""
        service = VisitaService(db_session)
        
        with patch.object(db_session, 'query', side_effect=Exception("Database error")):
            with pytest.raises(HTTPException) as exc_info:
                service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=date(2025, 11, 25))
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_create_visita_exception_general(self, db_session, sample_visita_data):
        """Test: Excepción general al crear visita"""
        service = VisitaService(db_session)
        
        # Mock de verificación exitosa
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=True):
            # Mock de cliente info exitoso
            with patch.object(service, 'get_cliente_info', new_callable=AsyncMock, return_value={"cliente_id": 1, "nombre_comercial": "Test"}):
                # Forzar excepción en add
                with patch.object(db_session, 'add', side_effect=Exception("Database error")):
                    visita_create = VisitaCreate(**sample_visita_data)
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await service.create_visita(visita_create)
                    
                    assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_clientes_disponibles_zona_error_cliente_service(self, db_session):
        """Test: Error al consultar cliente-service para zona"""
        service = VisitaService(db_session)
        
        # Mock de respuesta con error
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc_info:
                await service.get_clientes_disponibles_zona(
                    gerente_id=1,
                    fecha=date(2025, 11, 25),
                    lat=4.6533,
                    lng=-74.0836,
                    radio_km=20
                )
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_clientes_disponibles_zona_exception(self, db_session):
        """Test: Excepción general en clientes disponibles zona"""
        service = VisitaService(db_session)
        
        with patch.object(service, 'get_http_client', side_effect=Exception("Network error")):
            with pytest.raises(HTTPException) as exc_info:
                await service.get_clientes_disponibles_zona(
                    gerente_id=1,
                    fecha=date(2025, 11, 25),
                    lat=4.6533,
                    lng=-74.0836,
                    radio_km=20
                )
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_create_visita_sin_hora_inicio(self, db_session, mock_cliente_response):
        """Test: Crear visita sin hora de inicio (no calcula hora_fin)"""
        service = VisitaService(db_session)
        
        visita_data = VisitaCreate(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=None,  # Sin hora de inicio
            duracion_estimada_minutos=60,
            prioridad=PrioridadVisita.MEDIA
        )
        
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=True):
            with patch.object(service, 'get_cliente_info', new_callable=AsyncMock, return_value=mock_cliente_response):
                result = await service.create_visita(visita_data)
        
        assert result.hora_inicio_sugerida is None
        assert result.hora_fin_sugerida is None

    def test_update_visita_sin_recalculo_horarios(self, db_session):
        """Test: Actualizar visita sin cambiar hora ni duración (no recalcula)"""
        service = VisitaService(db_session)
        
        # Crear visita
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            hora_fin_sugerida=time(10, 0),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        # Actualizar solo prioridad (no recalcula horarios)
        update_data = VisitaUpdate(prioridad=PrioridadVisita.ALTA)
        
        result = service.update_visita(visita_id=1, gerente_id=1, visita_update=update_data)
        
        assert result.prioridad == PrioridadVisita.ALTA
        assert result.hora_fin_sugerida == time(10, 0)  # No cambió

    def test_update_visita_con_nueva_duracion(self, db_session):
        """Test: Actualizar duración recalcula hora_fin"""
        service = VisitaService(db_session)
        
        # Crear visita
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            hora_fin_sugerida=time(10, 0),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        # Actualizar duración a 90 minutos
        update_data = VisitaUpdate(duracion_estimada_minutos=90)
        
        result = service.update_visita(visita_id=1, gerente_id=1, visita_update=update_data)
        
        assert result.duracion_estimada_minutos == 90
        assert result.hora_fin_sugerida == time(10, 30)  # 9:00 + 90 min


class TestRutasEndpointsErrors:
    """Tests de errores en endpoints de rutas"""

    def test_get_visita_endpoint_exception(self, client, db_session):
        """Test: Excepción interna en endpoint get_visita"""
        # Crear visita
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        # Forzar excepción en get_visita_by_id
        with patch('app.services.visita_service.VisitaService.get_visita_by_id', side_effect=Exception("Unexpected error")):
            response = client.get("/api/v1/visitas/1?gerente_id=1")
        
        assert response.status_code == 500

    def test_update_visita_endpoint_exception(self, client, db_session):
        """Test: Excepción interna en endpoint update_visita"""
        update_data = {
            "prioridad": "alta"
        }
        
        with patch('app.services.visita_service.VisitaService.update_visita', side_effect=Exception("Unexpected error")):
            response = client.put("/api/v1/visitas/1?gerente_id=1", json=update_data)
        
        assert response.status_code == 500

    def test_delete_visita_endpoint_exception(self, client):
        """Test: Excepción interna en endpoint delete_visita"""
        with patch('app.services.visita_service.VisitaService.delete_visita', side_effect=Exception("Unexpected error")):
            response = client.delete("/api/v1/visitas/1?gerente_id=1")
        
        assert response.status_code == 500

    def test_get_visitas_endpoint_exception(self, client):
        """Test: Excepción interna en endpoint get_visitas"""
        fecha = date(2025, 11, 25)
        
        with patch('app.services.visita_service.VisitaService.get_visitas_by_gerente_fecha', side_effect=Exception("Unexpected error")):
            response = client.get(f"/api/v1/visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 500

    def test_get_ruta_visitas_exception(self, client):
        """Test: Excepción interna en endpoint get_ruta_visitas"""
        fecha = date(2025, 11, 25)
        
        with patch('app.services.visita_service.VisitaService.get_ruta_by_gerente_fecha', side_effect=Exception("Unexpected error")):
            response = client.get(f"/api/v1/rutas-visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 500

    def test_recalcular_ruta_exception(self, client):
        """Test: Excepción interna en endpoint recalcular"""
        request_data = {
            "fecha": "2025-11-25",
            "gerente_id": 1
        }
        
        with patch('app.services.visita_service.VisitaService.get_visitas_by_gerente_fecha', side_effect=Exception("Unexpected error")):
            response = client.post("/api/v1/rutas-visitas/recalcular", json=request_data)
        
        assert response.status_code == 500

    def test_clientes_disponibles_zona_exception(self, client):
        """Test: Excepción interna en endpoint clientes disponibles"""
        fecha = date(2025, 11, 25)
        
        with patch('app.services.visita_service.VisitaService.get_clientes_disponibles_zona', side_effect=Exception("Unexpected error")):
            response = client.get(
                f"/api/v1/clientes-disponibles-zona?gerente_id=1&fecha={fecha}&lat=4.6533&lng=-74.0836&radio_km=20"
            )
        
        assert response.status_code == 500


class TestCasosEdge:
    """Tests de casos edge para aumentar cobertura"""

    @pytest.mark.asyncio
    async def test_create_visita_con_duracion_minima(self, db_session, mock_cliente_response):
        """Test: Crear visita con duración mínima (15 minutos)"""
        service = VisitaService(db_session)
        
        visita_data = VisitaCreate(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            duracion_estimada_minutos=15,  # Mínimo
            prioridad=PrioridadVisita.BAJA
        )
        
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=True):
            with patch.object(service, 'get_cliente_info', new_callable=AsyncMock, return_value=mock_cliente_response):
                result = await service.create_visita(visita_data)
        
        assert result.duracion_estimada_minutos == 15

    @pytest.mark.asyncio
    async def test_create_visita_con_duracion_maxima(self, db_session, mock_cliente_response):
        """Test: Crear visita con duración máxima (480 minutos = 8 horas)"""
        service = VisitaService(db_session)
        
        visita_data = VisitaCreate(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(8, 0),
            duracion_estimada_minutos=480,  # Máximo (8 horas)
            prioridad=PrioridadVisita.ALTA
        )
        
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=True):
            with patch.object(service, 'get_cliente_info', new_callable=AsyncMock, return_value=mock_cliente_response):
                result = await service.create_visita(visita_data)
        
        assert result.duracion_estimada_minutos == 480
        assert result.hora_fin_sugerida == time(16, 0)  # 8:00 + 8 horas

    def test_get_visitas_con_diferentes_estados(self, db_session):
        """Test: Obtener visitas con diferentes estados"""
        service = VisitaService(db_session)
        fecha = date(2025, 11, 25)
        
        # Crear visitas con todos los estados
        estados = [EstadoVisita.PROGRAMADA, EstadoVisita.EN_CURSO, EstadoVisita.COMPLETADA]
        
        for i, estado in enumerate(estados):
            visita = Visita(
                visita_id=i+1,
                gerente_id=1,
                cliente_id=i+1,
                fecha_visita=fecha,
                duracion_estimada_minutos=60,
                estado=estado,
                prioridad=PrioridadVisita.MEDIA
            )
            db_session.add(visita)
        db_session.commit()
        
        # Obtener solo programadas
        result = service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=fecha, estado=EstadoVisita.PROGRAMADA)
        assert len(result) == 1
        
        # Obtener solo en curso
        result = service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=fecha, estado=EstadoVisita.EN_CURSO)
        assert len(result) == 1
        
        # Obtener solo completadas
        result = service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=fecha, estado=EstadoVisita.COMPLETADA)
        assert len(result) == 1

    def test_update_visita_cambia_estado(self, db_session):
        """Test: Actualizar estado de visita"""
        service = VisitaService(db_session)
        
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        # Cambiar a EN_CURSO
        update_data = VisitaUpdate(estado=EstadoVisita.EN_CURSO)
        result = service.update_visita(visita_id=1, gerente_id=1, visita_update=update_data)
        
        assert result.estado == EstadoVisita.EN_CURSO

    def test_update_visita_cambia_fecha(self, db_session):
        """Test: Actualizar fecha de visita"""
        service = VisitaService(db_session)
        
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        # Cambiar fecha
        nueva_fecha = date(2025, 11, 26)
        update_data = VisitaUpdate(fecha_visita=nueva_fecha)
        result = service.update_visita(visita_id=1, gerente_id=1, visita_update=update_data)
        
        assert result.fecha_visita == nueva_fecha


class TestRutaOptimizerEdgeCases:
    """Tests de casos edge del optimizador"""

    def test_optimizar_ruta_todas_sin_coordenadas(self):
        """Test: Optimizar ruta donde ninguna visita tiene coordenadas"""
        from app.services.ruta_optimizer import optimizar_ruta_nearest_neighbor
        
        visita1 = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=None,
            longitud=None,
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Sin coordenadas 1"
        )
        visita2 = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=date(2025, 11, 25),
            latitud=None,
            longitud=None,
            duracion_estimada_minutos=45,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            nombre_cliente="Sin coordenadas 2"
        )
        
        visitas_ordenadas, distancia, tiempo = optimizar_ruta_nearest_neighbor([visita1, visita2])
        
        assert len(visitas_ordenadas) == 2
        assert distancia == 0.0  # Sin coordenadas, sin distancia
        assert tiempo == 0  # Sin distancia, sin tiempo de viaje

    def test_calcular_horarios_sin_posicion_anterior(self):
        """Test: Calcular horarios cuando visitas no tienen coordenadas"""
        from app.services.ruta_optimizer import calcular_horarios_sugeridos
        
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=None,
            longitud=None,
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        result = calcular_horarios_sugeridos([visita], hora_inicio=time(9, 0))
        
        assert len(result) == 1
        assert result[0].hora_inicio_sugerida == time(9, 0)
        assert result[0].orden_en_ruta == 1

    def test_construir_visitas_primera_sin_anterior(self):
        """Test: Primera visita no tiene distancia_desde_anterior"""
        from app.services.ruta_optimizer import construir_visitas_en_ruta
        
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            hora_inicio_sugerida=time(8, 0),
            hora_fin_sugerida=time(9, 0),
            duracion_estimada_minutos=60,
            orden_en_ruta=1,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            nombre_cliente="Primera"
        )
        
        result = construir_visitas_en_ruta([visita])
        
        assert len(result) == 1
        assert result[0].distancia_desde_anterior_km is None  # Primera no tiene anterior
        assert result[0].tiempo_viaje_desde_anterior_min is None

