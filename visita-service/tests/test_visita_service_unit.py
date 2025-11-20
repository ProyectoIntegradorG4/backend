"""
Tests unitarios para VisitaService
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.visita_service import VisitaService
from app.models.visita import (
    Visita, RutaVisita, VisitaCreate, VisitaUpdate, 
    EstadoVisita, PrioridadVisita, OrigenRuta
)
from fastapi import HTTPException
from datetime import date, time, datetime, timezone, timedelta
from decimal import Decimal


class TestVisitaService:
    """Tests unitarios para VisitaService"""

    @pytest.mark.asyncio
    async def test_create_visita_success(self, db_session, sample_visita_data, mock_cliente_response, mock_cliente_ids_response):
        """Test: Crear visita exitosamente"""
        service = VisitaService(db_session)
        
        # Mock de verificación de acceso del gerente al cliente
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=True):
            # Mock de obtención de info del cliente
            with patch.object(service, 'get_cliente_info', new_callable=AsyncMock, return_value=mock_cliente_response):
                visita_create = VisitaCreate(**sample_visita_data)
                result = await service.create_visita(visita_create)
        
        assert result.visita_id is not None
        assert result.gerente_id == 1
        assert result.cliente_id == 1
        assert result.estado == EstadoVisita.PROGRAMADA
        assert result.nombre_cliente == "Hospital San José"
        assert result.latitud == 4.6533

    @pytest.mark.asyncio
    async def test_create_visita_sin_acceso_cliente(self, db_session, sample_visita_data):
        """Test: No puede crear visita si gerente no tiene acceso al cliente"""
        service = VisitaService(db_session)
        
        # Mock de verificación que retorna False
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=False):
            visita_create = VisitaCreate(**sample_visita_data)
            
            with pytest.raises(HTTPException) as exc_info:
                await service.create_visita(visita_create)
            
            assert exc_info.value.status_code == 403
            assert "no tiene acceso" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_visita_cliente_no_encontrado(self, db_session, sample_visita_data):
        """Test: Error si cliente no existe"""
        service = VisitaService(db_session)
        
        # Mock de verificación de acceso exitosa pero cliente no existe
        with patch.object(service, 'verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=True):
            with patch.object(service, 'get_cliente_info', new_callable=AsyncMock, return_value=None):
                visita_create = VisitaCreate(**sample_visita_data)
                
                with pytest.raises(HTTPException) as exc_info:
                    await service.create_visita(visita_create)
                
                assert exc_info.value.status_code == 404
                assert "no encontrado" in exc_info.value.detail

    def test_get_visitas_by_gerente_fecha(self, db_session):
        """Test: Obtener visitas de un gerente para una fecha"""
        # Crear visitas de prueba
        fecha = date(2025, 11, 25)
        
        visita1 = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            hora_inicio_sugerida=time(9, 0),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA
        )
        visita2 = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            hora_inicio_sugerida=time(11, 0),
            duracion_estimada_minutos=45,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        # Visita de otro gerente (no debe aparecer)
        visita3 = Visita(
            gerente_id=2,
            cliente_id=3,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.BAJA
        )
        
        db_session.add_all([visita1, visita2, visita3])
        db_session.commit()
        
        service = VisitaService(db_session)
        result = service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=fecha)
        
        assert len(result) == 2
        assert all(v.gerente_id == 1 for v in result)
        assert all(v.fecha_visita == fecha for v in result)

    def test_get_visitas_filtrando_canceladas(self, db_session):
        """Test: Por defecto no se retornan visitas canceladas"""
        fecha = date(2025, 11, 25)
        
        visita_activa = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA
        )
        visita_cancelada = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            estado=EstadoVisita.CANCELADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        db_session.add_all([visita_activa, visita_cancelada])
        db_session.commit()
        
        service = VisitaService(db_session)
        result = service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=fecha)
        
        assert len(result) == 1
        assert result[0].estado == EstadoVisita.PROGRAMADA

    def test_get_visita_by_id_existente(self, db_session):
        """Test: Obtener visita por ID existente"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        service = VisitaService(db_session)
        result = service.get_visita_by_id(visita.visita_id, gerente_id=1)
        
        assert result is not None
        assert result.visita_id == visita.visita_id

    def test_get_visita_by_id_otro_gerente(self, db_session):
        """Test: No puede obtener visita de otro gerente"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        service = VisitaService(db_session)
        result = service.get_visita_by_id(visita.visita_id, gerente_id=2)
        
        assert result is None

    def test_update_visita_success(self, db_session):
        """Test: Actualizar visita exitosamente"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        service = VisitaService(db_session)
        
        # Actualizar prioridad y observaciones
        update_data = VisitaUpdate(
            prioridad=PrioridadVisita.ALTA,
            observaciones="Cliente muy importante"
        )
        
        result = service.update_visita(visita.visita_id, gerente_id=1, visita_update=update_data)
        
        assert result.prioridad == PrioridadVisita.ALTA
        assert result.observaciones == "Cliente muy importante"

    def test_update_visita_recalcula_horarios(self, db_session):
        """Test: Actualizar hora de inicio recalcula hora de fin"""
        visita = Visita(
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
        
        service = VisitaService(db_session)
        
        # Actualizar hora de inicio
        update_data = VisitaUpdate(
            hora_inicio_sugerida=time(10, 30)
        )
        
        result = service.update_visita(visita.visita_id, gerente_id=1, visita_update=update_data)
        
        assert result.hora_inicio_sugerida == time(10, 30)
        assert result.hora_fin_sugerida == time(11, 30)

    def test_delete_visita_soft_delete(self, db_session):
        """Test: Cancelar visita (soft delete)"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        service = VisitaService(db_session)
        result = service.delete_visita(visita.visita_id, gerente_id=1)
        
        assert result is True
        
        # Verificar que el estado cambió a CANCELADA
        db_session.refresh(visita)
        assert visita.estado == EstadoVisita.CANCELADA

    def test_delete_visita_otro_gerente(self, db_session):
        """Test: No puede cancelar visita de otro gerente"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        service = VisitaService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_visita(visita.visita_id, gerente_id=2)
        
        assert exc_info.value.status_code == 404

    def test_get_ruta_by_gerente_fecha_existente(self, db_session):
        """Test: Obtener ruta existente"""
        fecha = date(2025, 11, 25)
        
        ruta = RutaVisita(
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            activa=True
        )
        db_session.add(ruta)
        db_session.commit()
        db_session.refresh(ruta)
        
        service = VisitaService(db_session)
        result = service.get_ruta_by_gerente_fecha(gerente_id=1, fecha=fecha)
        
        assert result is not None
        assert result.gerente_id == 1
        assert result.fecha_ruta == fecha

    def test_get_ruta_by_gerente_fecha_no_existe(self, db_session):
        """Test: Retorna None si no hay ruta"""
        service = VisitaService(db_session)
        result = service.get_ruta_by_gerente_fecha(gerente_id=1, fecha=date(2025, 11, 25))
        
        assert result is None

    def test_crear_ruta_vacia(self, db_session):
        """Test: Crear ruta vacía"""
        fecha = date(2025, 11, 25)
        
        service = VisitaService(db_session)
        ruta = service.crear_ruta_vacia(gerente_id=1, fecha=fecha)
        
        assert ruta.gerente_id == 1
        assert ruta.fecha_ruta == fecha
        assert ruta.version_ruta == 1
        assert ruta.activa is True

    def test_crear_ruta_vacia_desactiva_anterior(self, db_session):
        """Test: Crear ruta desactiva la ruta anterior"""
        fecha = date(2025, 11, 25)
        
        # Crear ruta inicial
        ruta_anterior = RutaVisita(
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            activa=True
        )
        db_session.add(ruta_anterior)
        db_session.commit()
        
        service = VisitaService(db_session)
        ruta_nueva = service.crear_ruta_vacia(gerente_id=1, fecha=fecha)
        
        # Verificar que la anterior se desactivó
        db_session.refresh(ruta_anterior)
        assert ruta_anterior.activa is False
        assert ruta_nueva.activa is True

    @pytest.mark.asyncio
    async def test_get_clientes_disponibles_zona(self, db_session, mock_clientes_list_response):
        """Test: Obtener clientes disponibles en zona"""
        service = VisitaService(db_session)
        fecha = date(2025, 11, 25)
        
        # Crear una visita programada para uno de los clientes
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        # Mock del cliente HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_clientes_list_response
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            result = await service.get_clientes_disponibles_zona(
                gerente_id=1,
                fecha=fecha,
                lat=4.6533,
                lng=-74.0836,
                radio_km=50
            )
        
        assert result.total > 0
        assert result.gerente_id == 1
        assert result.fecha == fecha
        # Verificar que cliente 1 tiene visita programada
        cliente_1 = next((c for c in result.clientes if c.cliente_id == 1), None)
        if cliente_1:
            assert cliente_1.tiene_visita_programada is True

    def test_get_visitas_ordenadas_por_hora(self, db_session):
        """Test: Visitas se retornan ordenadas por hora y orden_en_ruta"""
        fecha = date(2025, 11, 25)
        
        visita1 = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            hora_inicio_sugerida=time(11, 0),
            orden_en_ruta=2,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        visita2 = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            hora_inicio_sugerida=time(9, 0),
            orden_en_ruta=1,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA
        )
        
        db_session.add_all([visita1, visita2])
        db_session.commit()
        
        service = VisitaService(db_session)
        result = service.get_visitas_by_gerente_fecha(gerente_id=1, fecha=fecha)
        
        # Deben estar ordenadas por orden_en_ruta primero
        assert len(result) == 2
        assert result[0].orden_en_ruta == 1
        assert result[1].orden_en_ruta == 2

    def test_filtrar_visitas_por_estado(self, db_session):
        """Test: Filtrar visitas por estado específico"""
        fecha = date(2025, 11, 25)
        
        visita_programada = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA
        )
        visita_completada = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            estado=EstadoVisita.COMPLETADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        db_session.add_all([visita_programada, visita_completada])
        db_session.commit()
        
        service = VisitaService(db_session)
        
        # Filtrar solo programadas
        result = service.get_visitas_by_gerente_fecha(
            gerente_id=1, 
            fecha=fecha, 
            estado=EstadoVisita.PROGRAMADA
        )
        
        assert len(result) == 1
        assert result[0].estado == EstadoVisita.PROGRAMADA

    @pytest.mark.asyncio
    async def test_verificar_gerente_tiene_cliente(self, db_session, mock_cliente_ids_response):
        """Test: Verificar que gerente tiene acceso a cliente"""
        service = VisitaService(db_session)
        
        # Mock del cliente HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_cliente_ids_response
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            # Cliente 1 está en la lista
            result = await service.verificar_gerente_tiene_cliente(gerente_id=1, cliente_id=1)
            assert result is True
            
            # Cliente 99 no está en la lista
            result = await service.verificar_gerente_tiene_cliente(gerente_id=1, cliente_id=99)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_cliente_info_success(self, db_session, mock_cliente_response):
        """Test: Obtener información de cliente exitosamente"""
        service = VisitaService(db_session)
        
        # Mock del cliente HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_cliente_response
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            result = await service.get_cliente_info(cliente_id=1)
        
        assert result is not None
        assert result["cliente_id"] == 1
        assert result["nombre_comercial"] == "Hospital San José"
        assert result["latitud"] == 4.6533

    @pytest.mark.asyncio
    async def test_get_cliente_info_no_encontrado(self, db_session):
        """Test: Cliente no encontrado retorna None"""
        service = VisitaService(db_session)
        
        # Mock del cliente HTTP con 404
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(service, 'get_http_client', new_callable=AsyncMock) as mock_http:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client
            
            result = await service.get_cliente_info(cliente_id=999)
        
        assert result is None

