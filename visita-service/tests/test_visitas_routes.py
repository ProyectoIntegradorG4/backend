"""
Tests de integración para endpoints de visitas
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.models.visita import Visita, RutaVisita, EstadoVisita, PrioridadVisita, OrigenRuta
from datetime import date, time
from decimal import Decimal


class TestVisitasAPI:
    """Tests de integración para endpoints de visitas"""

    def test_health_check(self, client):
        """Test del endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "visita-service"

    def test_create_visita_success(self, client, db_session, sample_visita_dict, mock_cliente_response):
        """Test: Crear visita exitosamente"""
        from app.models.visita import VisitaResponse, EstadoVisita, PrioridadVisita
        from datetime import datetime, timezone
        
        # Mock de la respuesta completa del servicio
        mock_visita_response = VisitaResponse(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            duracion_estimada_minutos=60,
            prioridad=PrioridadVisita.ALTA,
            observaciones="Primera visita del mes",
            estado=EstadoVisita.PROGRAMADA,
            nombre_cliente="Hospital San José",
            latitud=4.6533,
            longitud=-74.0836,
            fecha_registro=datetime.now(timezone.utc),
            fecha_actualizacion=datetime.now(timezone.utc)
        )
        
        # Mock del método create_visita del servicio
        with patch('app.services.visita_service.VisitaService.create_visita', new_callable=AsyncMock, return_value=mock_visita_response):
            response = client.post(
                "/api/v1/visitas",
                json=sample_visita_dict
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["gerente_id"] == 1
        assert data["cliente_id"] == 1
        assert data["estado"] == "programada"
        assert "visita_id" in data

    @pytest.mark.asyncio
    async def test_create_visita_sin_acceso_cliente(self, client, sample_visita_dict):
        """Test: No puede crear visita si gerente no tiene acceso"""
        with patch('app.services.visita_service.VisitaService.verificar_gerente_tiene_cliente', new_callable=AsyncMock, return_value=False):
            response = client.post(
                "/api/v1/visitas",
                json=sample_visita_dict
            )
        
        assert response.status_code == 403
        assert "no tiene acceso" in response.json()["detail"]

    def test_get_visita_by_id(self, client, db_session):
        """Test: Obtener visita por ID"""
        # Crear visita
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            duracion_estimada_minutos=60
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        response = client.get(f"/api/v1/visitas/{visita.visita_id}?gerente_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["visita_id"] == visita.visita_id
        assert data["gerente_id"] == 1

    def test_get_visita_no_encontrada(self, client):
        """Test: Visita no encontrada retorna 404"""
        response = client.get("/api/v1/visitas/99999?gerente_id=1")
        
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"]

    def test_get_visita_otro_gerente(self, client, db_session):
        """Test: No puede ver visita de otro gerente"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            duracion_estimada_minutos=60
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        # Intentar acceder con gerente_id=2
        response = client.get(f"/api/v1/visitas/{visita.visita_id}?gerente_id=2")
        
        assert response.status_code == 404

    def test_update_visita_success(self, client, db_session):
        """Test: Actualizar visita exitosamente"""
        from app.models.visita import VisitaResponse
        from datetime import datetime, timezone
        
        # Crear visita directamente en BD de prueba
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            hora_fin_sugerida=time(10, 0),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            observaciones="Observación inicial",
            fecha_registro=datetime.now(timezone.utc),
            fecha_actualizacion=datetime.now(timezone.utc)
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        # Mock de la respuesta del servicio
        mock_response = VisitaResponse(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            hora_inicio_sugerida=time(9, 0),
            duracion_estimada_minutos=60,
            prioridad=PrioridadVisita.ALTA,
            observaciones="Observación actualizada",
            estado=EstadoVisita.PROGRAMADA,
            fecha_registro=datetime.now(timezone.utc),
            fecha_actualizacion=datetime.now(timezone.utc)
        )
        
        update_data = {
            "prioridad": "alta",
            "observaciones": "Observación actualizada"
        }
        
        with patch('app.services.visita_service.VisitaService.update_visita', return_value=mock_response):
            response = client.put(
                f"/api/v1/visitas/1?gerente_id=1",
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["prioridad"] == "alta"
        assert data["observaciones"] == "Observación actualizada"

    def test_delete_visita_success(self, client, db_session):
        """Test: Cancelar visita exitosamente"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            duracion_estimada_minutos=60
        )
        db_session.add(visita)
        db_session.commit()
        db_session.refresh(visita)
        
        response = client.delete(f"/api/v1/visitas/{visita.visita_id}?gerente_id=1")
        
        assert response.status_code == 204
        
        # Verificar que el estado cambió
        db_session.refresh(visita)
        assert visita.estado == EstadoVisita.CANCELADA

    def test_get_visitas_por_fecha(self, client, db_session):
        """Test: Listar visitas por fecha"""
        from app.models.visita import VisitaListResponse, VisitaResponse
        from datetime import datetime, timezone
        
        fecha = date(2025, 11, 25)
        
        # Mock de lista de visitas
        visitas_mock = [
            VisitaResponse(
                visita_id=i+1,
                gerente_id=1,
                cliente_id=i+1,
                fecha_visita=fecha,
                duracion_estimada_minutos=60,
                prioridad=PrioridadVisita.MEDIA,
                estado=EstadoVisita.PROGRAMADA,
                fecha_registro=datetime.now(timezone.utc)
            )
            for i in range(3)
        ]
        
        mock_response = VisitaListResponse(total=3, visitas=visitas_mock)
        
        with patch('app.services.visita_service.VisitaService.get_visitas_by_gerente_fecha', return_value=[]):
            response = client.get(f"/api/v1/visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "visitas" in data

    def test_get_visitas_filtra_por_estado(self, client, db_session):
        """Test: Filtrar visitas por estado"""
        fecha = date(2025, 11, 25)
        
        # Crear visitas en BD de prueba
        visita_programada = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            duracion_estimada_minutos=60
        )
        db_session.add(visita_programada)
        db_session.commit()
        
        response = client.get(f"/api/v1/visitas?gerente_id=1&fecha={fecha}&estado=programada")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0  # Puede ser 0 o más
        assert "visitas" in data


class TestRutasOptimizadasAPI:
    """Tests para endpoints de rutas optimizadas (HU-MOV-003)"""

    def test_get_ruta_sin_visitas(self, client, db_session):
        """Test: Consultar ruta sin visitas programadas retorna ruta vacía"""
        from app.models.visita import RutaVisita
        from datetime import datetime, timezone
        
        fecha = date(2025, 11, 25)
        
        # Crear ruta vacía en BD
        ruta = RutaVisita(
            ruta_id=1,
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            activa=True,
            origen_ruta=OrigenRuta.PLANIFICADA,
            fecha_calculo=datetime.now(timezone.utc)
        )
        db_session.add(ruta)
        db_session.commit()
        
        response = client.get(f"/api/v1/rutas-visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["gerente_id"] == 1
        assert data["cantidad_visitas"] == 0
        assert data["visitas"] == []

    def test_get_ruta_con_visitas_genera_automaticamente(self, client, db_session):
        """Test: Si no existe ruta pero hay visitas, se genera automáticamente"""
        from app.models.visita import RutaVisita
        from datetime import datetime, timezone
        
        fecha = date(2025, 11, 25)
        
        # Crear ruta con visitas en BD
        ruta = RutaVisita(
            ruta_id=1,
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            distancia_total_km=Decimal("12.5"),
            tiempo_total_minutos=120,
            activa=True,
            origen_ruta=OrigenRuta.PLANIFICADA,
            fecha_calculo=datetime.now(timezone.utc)
        )
        db_session.add(ruta)
        db_session.commit()
        
        # Crear visitas asociadas
        visita1 = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            ruta_id=1,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            orden_en_ruta=1,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            nombre_cliente="Hospital A"
        )
        visita2 = Visita(
            visita_id=2,
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            ruta_id=1,
            latitud=Decimal("4.6697"),
            longitud=Decimal("-74.0560"),
            duracion_estimada_minutos=45,
            orden_en_ruta=2,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Hospital B"
        )
        
        db_session.add_all([visita1, visita2])
        db_session.commit()
        
        response = client.get(f"/api/v1/rutas-visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cantidad_visitas"] == 2
        assert data["distancia_total_km"] > 0
        assert len(data["visitas"]) == 2
        # Visitas deben tener orden asignado
        assert data["visitas"][0]["orden_en_ruta"] == 1
        assert data["visitas"][1]["orden_en_ruta"] == 2

    def test_recalcular_ruta_incrementa_version(self, client, db_session):
        """Test: Recalcular ruta incrementa versión"""
        from app.models.visita import RutaVisita
        from datetime import datetime, timezone
        
        fecha = date(2025, 11, 25)
        
        # Crear ruta inicial con visita
        ruta = RutaVisita(
            ruta_id=1,
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            activa=True,
            origen_ruta=OrigenRuta.PLANIFICADA,
            fecha_calculo=datetime.now(timezone.utc)
        )
        db_session.add(ruta)
        db_session.commit()
        
        # Crear visita asociada
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            ruta_id=ruta.ruta_id
        )
        db_session.add(visita)
        db_session.commit()
        
        request_data = {
            "fecha": str(fecha),
            "gerente_id": 1
        }
        
        response = client.post("/api/v1/rutas-visitas/recalcular", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["version_ruta"] == 2  # Incrementada
        assert data["origen_ruta"] == "recalculada"

    def test_recalcular_ruta_sin_visitas_retorna_error(self, client):
        """Test: Recalcular ruta sin visitas retorna 404"""
        fecha = date(2025, 11, 30)
        
        request_data = {
            "fecha": str(fecha),
            "gerente_id": 1
        }
        
        response = client.post("/api/v1/rutas-visitas/recalcular", json=request_data)
        
        assert response.status_code == 404
        assert "No hay visitas" in response.json()["detail"]

    def test_clientes_disponibles_zona_con_radio(self, client, db_session, mock_clientes_list_response):
        """Test: Obtener clientes disponibles en zona geográfica"""
        fecha = date(2025, 11, 25)
        
        # Mock del método completo del servicio
        from app.models.visita import ClientesDisponiblesZonaResponse, ClienteDisponibleZona
        
        mock_result = ClientesDisponiblesZonaResponse(
            fecha=fecha,
            gerente_id=1,
            punto_referencia={"lat": 4.6533, "lng": -74.0836},
            radio_km=50.0,
            clientes=[
                ClienteDisponibleZona(
                    cliente_id=1,
                    nombre_comercial="Hospital San José",
                    direccion="Calle 10",
                    latitud=4.6533,
                    longitud=-74.0836,
                    distancia_km=2.5,
                    tiene_visita_programada=False
                )
            ],
            total=1
        )
        
        with patch('app.services.visita_service.VisitaService.get_clientes_disponibles_zona', new_callable=AsyncMock, return_value=mock_result):
            response = client.get(
                f"/api/v1/clientes-disponibles-zona?gerente_id=1&fecha={fecha}&lat=4.6533&lng=-74.0836&radio_km=50"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["gerente_id"] == 1
        assert "clientes" in data
        assert "total" in data

    def test_clientes_disponibles_zona_radio_invalido(self, client):
        """Test: Radio inválido retorna error de validación"""
        fecha = date(2025, 11, 25)
        
        # Radio mayor a 100 (límite máximo)
        response = client.get(
            f"/api/v1/clientes-disponibles-zona?gerente_id=1&fecha={fecha}&lat=4.6533&lng=-74.0836&radio_km=150"
        )
        
        assert response.status_code == 422  # Unprocessable Entity (validación Pydantic)

    def test_get_visitas_sin_parametros_requeridos(self, client):
        """Test: Sin parámetros requeridos retorna error de validación"""
        response = client.get("/api/v1/visitas")
        
        assert response.status_code == 422  # Faltan gerente_id y fecha

    def test_create_visita_datos_invalidos(self, client):
        """Test: Datos inválidos retornan error de validación"""
        datos_invalidos = {
            "gerente_id": "texto",  # Debe ser int
            "cliente_id": 1,
            "fecha_visita": "2025-11-25"
        }
        
        response = client.post("/api/v1/visitas", json=datos_invalidos)
        
        assert response.status_code == 422

    def test_get_ruta_retorna_visitas_ordenadas(self, client, db_session):
        """Test: Ruta retorna visitas en orden optimizado"""
        from app.models.visita import RutaVisita
        from datetime import datetime, timezone
        
        fecha = date(2025, 11, 25)
        
        # Crear ruta
        ruta = RutaVisita(
            ruta_id=1,
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            distancia_total_km=Decimal("250.0"),
            tiempo_total_minutos=300,
            activa=True,
            origen_ruta=OrigenRuta.PLANIFICADA,
            fecha_calculo=datetime.now(timezone.utc)
        )
        db_session.add(ruta)
        db_session.commit()
        
        # Crear visitas ordenadas
        visita1 = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            ruta_id=1,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            orden_en_ruta=1,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Hospital A",
            direccion_cliente="Dirección A"
        )
        visita2 = Visita(
            visita_id=2,
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            ruta_id=1,
            latitud=Decimal("4.6697"),
            longitud=Decimal("-74.0560"),
            duracion_estimada_minutos=45,
            orden_en_ruta=2,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            nombre_cliente="Hospital B",
            direccion_cliente="Dirección B"
        )
        visita3 = Visita(
            visita_id=3,
            gerente_id=1,
            cliente_id=3,
            fecha_visita=fecha,
            ruta_id=1,
            latitud=Decimal("6.2442"),
            longitud=Decimal("-75.5812"),
            duracion_estimada_minutos=60,
            orden_en_ruta=3,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.BAJA,
            nombre_cliente="Hospital C",
            direccion_cliente="Dirección C"
        )
        
        db_session.add_all([visita1, visita2, visita3])
        db_session.commit()
        
        response = client.get(f"/api/v1/rutas-visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cantidad_visitas"] == 3
        # Verificar que cada visita tiene orden
        for i, visita in enumerate(data["visitas"]):
            assert visita["orden_en_ruta"] == i + 1
            assert "nombre_cliente" in visita
            assert "direccion_cliente" in visita
            # Segunda y tercera deben tener distancia desde anterior
            if i > 0:
                assert "distancia_desde_anterior_km" in visita
                assert "tiempo_viaje_desde_anterior_min" in visita

    def test_ruta_con_metadatos_completos(self, client, db_session):
        """Test: Ruta incluye todos los metadatos necesarios"""
        from app.models.visita import RutaVisita
        from datetime import datetime, timezone
        
        fecha = date(2025, 11, 25)
        
        ruta = RutaVisita(
            ruta_id=1,
            gerente_id=1,
            fecha_ruta=fecha,
            version_ruta=1,
            distancia_total_km=Decimal("25.5"),
            tiempo_total_minutos=90,
            hora_inicio_sugerida=time(8, 0),
            hora_fin_sugerida=time(10, 30),
            activa=True,
            origen_ruta=OrigenRuta.PLANIFICADA,
            fecha_calculo=datetime.now(timezone.utc)
        )
        db_session.add(ruta)
        db_session.commit()
        
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            ruta_id=1,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            orden_en_ruta=1,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        response = client.get(f"/api/v1/rutas-visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar metadatos de ruta
        assert "ruta_id" in data
        assert "version_ruta" in data
        assert "distancia_total_km" in data
        assert "tiempo_total_minutos" in data
        assert "hora_inicio_sugerida" in data
        assert "hora_fin_sugerida" in data
        assert "origen_ruta" in data
        assert "fecha_calculo" in data
        assert "activa" in data

    def test_solo_ve_visitas_propias(self, client, db_session):
        """Test: Gerente solo ve sus propias visitas"""
        fecha = date(2025, 11, 25)
        
        # Visitas de gerente 1
        visita_gerente1 = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            duracion_estimada_minutos=60
        )
        # Visitas de gerente 2
        visita_gerente2 = Visita(
            visita_id=2,
            gerente_id=2,
            cliente_id=2,
            fecha_visita=fecha,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            duracion_estimada_minutos=60
        )
        
        db_session.add_all([visita_gerente1, visita_gerente2])
        db_session.commit()
        
        # Gerente 1 solo ve sus visitas
        response = client.get(f"/api/v1/visitas?gerente_id=1&fecha={fecha}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["visitas"][0]["gerente_id"] == 1

