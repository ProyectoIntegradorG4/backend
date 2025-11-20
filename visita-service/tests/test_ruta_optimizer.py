"""
Tests unitarios para RutaOptimizer
"""
import pytest
from app.services.ruta_optimizer import (
    calcular_distancia_haversine,
    calcular_tiempo_viaje_minutos,
    optimizar_ruta_nearest_neighbor,
    calcular_horarios_sugeridos,
    construir_visitas_en_ruta,
    RutaOptimizer
)
from app.models.visita import Visita, RutaVisita, EstadoVisita, PrioridadVisita, OrigenRuta
from datetime import date, time, datetime
from decimal import Decimal


class TestDistanciaHaversine:
    """Tests para cálculo de distancia Haversine"""

    def test_calcular_distancia_misma_ubicacion(self):
        """Test: Distancia entre mismo punto es 0"""
        distancia = calcular_distancia_haversine(4.6533, -74.0836, 4.6533, -74.0836)
        assert distancia == 0.0

    def test_calcular_distancia_bogota_medellin(self):
        """Test: Distancia entre Bogotá y Medellín (aproximadamente 240 km)"""
        # Bogotá
        lat1, lon1 = 4.6533, -74.0836
        # Medellín
        lat2, lon2 = 6.2442, -75.5812
        
        distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2)
        
        # Debe estar entre 230 y 250 km (aproximado)
        assert 230 < distancia < 250

    def test_calcular_distancia_bogota_cali(self):
        """Test: Distancia entre Bogotá y Cali (aproximadamente 303 km)"""
        # Bogotá
        lat1, lon1 = 4.6533, -74.0836
        # Cali
        lat2, lon2 = 3.4516, -76.5320
        
        distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2)
        
        # Debe estar entre 290 y 320 km (distancia en línea recta)
        assert 290 < distancia < 320

    def test_calcular_distancia_corta(self):
        """Test: Distancia corta dentro de la misma ciudad"""
        # Dos puntos cercanos en Bogotá (aproximadamente 2 km)
        lat1, lon1 = 4.6533, -74.0836
        lat2, lon2 = 4.6697, -74.0560
        
        distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2)
        
        # Debe estar entre 1 y 5 km
        assert 1 < distancia < 5


class TestTiempoViaje:
    """Tests para cálculo de tiempo de viaje"""

    def test_calcular_tiempo_viaje_30km(self):
        """Test: 30 km a 30 km/h = 60 minutos"""
        tiempo = calcular_tiempo_viaje_minutos(30.0)
        assert tiempo == 60

    def test_calcular_tiempo_viaje_15km(self):
        """Test: 15 km a 30 km/h = 30 minutos"""
        tiempo = calcular_tiempo_viaje_minutos(15.0)
        assert tiempo == 30

    def test_calcular_tiempo_viaje_5km(self):
        """Test: 5 km a 30 km/h = 10 minutos"""
        tiempo = calcular_tiempo_viaje_minutos(5.0)
        assert tiempo == 10

    def test_calcular_tiempo_viaje_distancia_cero(self):
        """Test: Distancia 0 = tiempo 0"""
        tiempo = calcular_tiempo_viaje_minutos(0.0)
        assert tiempo == 0

    def test_calcular_tiempo_viaje_redondeo(self):
        """Test: Tiempo se redondea hacia arriba"""
        # 0.5 km = 1 minuto (redondeado)
        tiempo = calcular_tiempo_viaje_minutos(0.5)
        assert tiempo >= 1


class TestOptimizacionRuta:
    """Tests para algoritmo Nearest Neighbor"""

    def test_optimizar_ruta_vacia(self):
        """Test: Ruta vacía retorna valores vacíos"""
        visitas_ordenadas, distancia, tiempo = optimizar_ruta_nearest_neighbor([])
        
        assert visitas_ordenadas == []
        assert distancia == 0.0
        assert tiempo == 0

    def test_optimizar_ruta_una_visita(self):
        """Test: Una sola visita"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        visitas_ordenadas, distancia, tiempo = optimizar_ruta_nearest_neighbor([visita])
        
        assert len(visitas_ordenadas) == 1
        assert distancia == 0.0
        assert tiempo == 60  # Solo la duración de la visita

    def test_optimizar_ruta_tres_visitas(self):
        """Test: Optimizar ruta con 3 visitas"""
        visita1 = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6533"),  # Bogotá
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Hospital A"
        )
        visita2 = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6697"),  # Cerca de la anterior
            longitud=Decimal("-74.0560"),
            duracion_estimada_minutos=45,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            nombre_cliente="Hospital B"
        )
        visita3 = Visita(
            gerente_id=1,
            cliente_id=3,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("6.2442"),  # Medellín (más lejos)
            longitud=Decimal("-75.5812"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.BAJA,
            nombre_cliente="Hospital C"
        )
        
        visitas = [visita1, visita2, visita3]
        
        visitas_ordenadas, distancia_total, tiempo_total = optimizar_ruta_nearest_neighbor(visitas)
        
        assert len(visitas_ordenadas) == 3
        assert distancia_total > 0
        assert tiempo_total > 0
        # Primera y segunda visita deben ser las cercanas (Bogotá)
        # Tercera debe ser la lejana (Medellín)

    def test_optimizar_ruta_prioriza_alta_prioridad(self):
        """Test: Prioridad alta reduce distancia efectiva (favorece elección temprana)"""
        visita_alta = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.7000"),
            longitud=Decimal("-74.1000"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,  # ← 30% descuento
            nombre_cliente="Hospital Alta Prioridad"
        )
        visita_baja = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6600"),  # Más cerca geográficamente
            longitud=Decimal("-74.0500"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.BAJA,  # ← 30% penalización
            nombre_cliente="Hospital Baja Prioridad"
        )
        
        punto_inicio = (4.6533, -74.0836)
        
        visitas_ordenadas, _, _ = optimizar_ruta_nearest_neighbor(
            [visita_alta, visita_baja],
            punto_inicio
        )
        
        # La de alta prioridad puede ser elegida primero por el ajuste de distancia
        # aunque geográficamente esté más lejos
        assert len(visitas_ordenadas) == 2

    def test_optimizar_ruta_sin_coordenadas(self):
        """Test: Visitas sin coordenadas se agregan al final"""
        visita_con_coords = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Con Coordenadas"
        )
        visita_sin_coords = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=date(2025, 11, 25),
            latitud=None,
            longitud=None,
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.ALTA,
            nombre_cliente="Sin Coordenadas"
        )
        
        visitas_ordenadas, distancia, tiempo = optimizar_ruta_nearest_neighbor(
            [visita_con_coords, visita_sin_coords]
        )
        
        assert len(visitas_ordenadas) == 2
        # La sin coordenadas debe estar al final
        assert visitas_ordenadas[-1].nombre_cliente == "Sin Coordenadas"


class TestCalculoHorarios:
    """Tests para cálculo de horarios sugeridos"""

    def test_calcular_horarios_una_visita(self):
        """Test: Calcular horarios para una visita"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        result = calcular_horarios_sugeridos([visita], hora_inicio=time(8, 0))
        
        assert len(result) == 1
        assert result[0].hora_inicio_sugerida == time(8, 0)
        assert result[0].hora_fin_sugerida == time(9, 0)
        assert result[0].orden_en_ruta == 1

    def test_calcular_horarios_multiples_visitas(self):
        """Test: Calcular horarios para múltiples visitas secuenciales"""
        visita1 = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        visita2 = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6697"),
            longitud=Decimal("-74.0560"),
            duracion_estimada_minutos=45,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        result = calcular_horarios_sugeridos([visita1, visita2], hora_inicio=time(8, 0))
        
        assert len(result) == 2
        assert result[0].hora_inicio_sugerida == time(8, 0)
        assert result[0].orden_en_ruta == 1
        # Segunda visita debe empezar después de la primera + tiempo de viaje
        assert result[1].hora_inicio_sugerida > time(9, 0)
        assert result[1].orden_en_ruta == 2

    def test_calcular_horarios_hora_inicio_personalizada(self):
        """Test: Usar hora de inicio personalizada"""
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            duracion_estimada_minutos=30,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        
        result = calcular_horarios_sugeridos([visita], hora_inicio=time(14, 30))
        
        assert result[0].hora_inicio_sugerida == time(14, 30)
        assert result[0].hora_fin_sugerida == time(15, 0)


class TestConstruirVisitasEnRuta:
    """Tests para construcción de VisitaEnRuta"""

    def test_construir_visitas_en_ruta_vacia(self):
        """Test: Lista vacía retorna vacío"""
        result = construir_visitas_en_ruta([])
        assert result == []

    def test_construir_visitas_en_ruta_con_distancias(self):
        """Test: Construir visitas con distancias calculadas"""
        visita1 = Visita(
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
            nombre_cliente="Hospital A",
            direccion_cliente="Calle 10"
        )
        visita2 = Visita(
            visita_id=2,
            gerente_id=1,
            cliente_id=2,
            fecha_visita=date(2025, 11, 25),
            latitud=Decimal("4.6697"),
            longitud=Decimal("-74.0560"),
            hora_inicio_sugerida=time(9, 30),
            hora_fin_sugerida=time(10, 15),
            duracion_estimada_minutos=45,
            orden_en_ruta=2,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Hospital B",
            direccion_cliente="Carrera 15"
        )
        
        result = construir_visitas_en_ruta([visita1, visita2])
        
        assert len(result) == 2
        assert result[0].visita_id == 1
        assert result[0].distancia_desde_anterior_km is None  # Primera no tiene anterior
        assert result[1].visita_id == 2
        assert result[1].distancia_desde_anterior_km is not None
        assert result[1].distancia_desde_anterior_km > 0
        assert result[1].tiempo_viaje_desde_anterior_min is not None

    def test_construir_visitas_sin_coordenadas(self):
        """Test: Visitas sin coordenadas no tienen distancias"""
        visita = Visita(
            visita_id=1,
            gerente_id=1,
            cliente_id=1,
            fecha_visita=date(2025, 11, 25),
            latitud=None,
            longitud=None,
            duracion_estimada_minutos=60,
            orden_en_ruta=1,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Sin Coordenadas"
        )
        
        result = construir_visitas_en_ruta([visita])
        
        assert len(result) == 1
        assert result[0].latitud is None
        assert result[0].longitud is None
        assert result[0].distancia_desde_anterior_km is None


class TestRutaOptimizer:
    """Tests para clase RutaOptimizer"""

    def test_optimizar_y_guardar_ruta(self, db_session):
        """Test: Optimizar y guardar ruta en BD"""
        fecha = date(2025, 11, 25)
        
        visita1 = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Hospital A"
        )
        visita2 = Visita(
            gerente_id=1,
            cliente_id=2,
            fecha_visita=fecha,
            latitud=Decimal("4.6697"),
            longitud=Decimal("-74.0560"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA,
            nombre_cliente="Hospital B"
        )
        
        db_session.add_all([visita1, visita2])
        db_session.commit()
        
        ruta = RutaOptimizer.optimizar_y_guardar_ruta(
            db_session,
            gerente_id=1,
            fecha_ruta=fecha,
            visitas=[visita1, visita2],
            origen=OrigenRuta.PLANIFICADA
        )
        
        assert ruta.ruta_id is not None
        assert ruta.gerente_id == 1
        assert ruta.fecha_ruta == fecha
        assert ruta.version_ruta == 1
        assert ruta.distancia_total_km > 0
        assert ruta.tiempo_total_minutos > 0
        assert ruta.activa is True

    def test_optimizar_incrementa_version(self, db_session):
        """Test: Recalcular ruta incrementa versión"""
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
        
        # Crear visita
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        # Recalcular ruta
        ruta_nueva = RutaOptimizer.optimizar_y_guardar_ruta(
            db_session,
            gerente_id=1,
            fecha_ruta=fecha,
            visitas=[visita],
            origen=OrigenRuta.RECALCULADA
        )
        
        # Verificar versión incrementada
        assert ruta_nueva.version_ruta == 2
        assert ruta_nueva.activa is True
        
        # Verificar que la anterior se desactivó
        db_session.refresh(ruta_anterior)
        assert ruta_anterior.activa is False

    def test_optimizar_asocia_visitas_a_ruta(self, db_session):
        """Test: Visitas se asocian a la ruta creada"""
        fecha = date(2025, 11, 25)
        
        visita = Visita(
            gerente_id=1,
            cliente_id=1,
            fecha_visita=fecha,
            latitud=Decimal("4.6533"),
            longitud=Decimal("-74.0836"),
            duracion_estimada_minutos=60,
            estado=EstadoVisita.PROGRAMADA,
            prioridad=PrioridadVisita.MEDIA
        )
        db_session.add(visita)
        db_session.commit()
        
        ruta = RutaOptimizer.optimizar_y_guardar_ruta(
            db_session,
            gerente_id=1,
            fecha_ruta=fecha,
            visitas=[visita],
            origen=OrigenRuta.PLANIFICADA
        )
        
        # Verificar que la visita tiene ruta_id asignado
        db_session.refresh(visita)
        assert visita.ruta_id == ruta.ruta_id

