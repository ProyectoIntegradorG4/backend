"""
Servicio de optimización de rutas de visitas
Implementa algoritmo Nearest Neighbor para MVP
"""

import math
from typing import List, Tuple, Optional
from app.models.visita import Visita, VisitaEnRuta, RutaVisita, OrigenRuta
from datetime import time, datetime, timedelta
import logging

logger = logging.getLogger("uvicorn")

# Constantes para cálculos
VELOCIDAD_PROMEDIO_KMH = 30  # Velocidad promedio en ciudad (km/h)
RADIO_TIERRA_KM = 6371  # Radio de la Tierra en kilómetros


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcular distancia entre dos puntos geográficos usando la fórmula de Haversine.
    
    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto
        
    Returns:
        Distancia en kilómetros
    """
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Fórmula de Haversine
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distancia = RADIO_TIERRA_KM * c
    return distancia


def calcular_tiempo_viaje_minutos(distancia_km: float) -> int:
    """
    Calcular tiempo estimado de viaje basado en distancia.
    
    Args:
        distancia_km: Distancia en kilómetros
        
    Returns:
        Tiempo en minutos
    """
    if distancia_km <= 0:
        return 0
    
    tiempo_horas = distancia_km / VELOCIDAD_PROMEDIO_KMH
    tiempo_minutos = int(math.ceil(tiempo_horas * 60))
    
    return tiempo_minutos


def optimizar_ruta_nearest_neighbor(
    visitas: List[Visita],
    punto_inicio: Optional[Tuple[float, float]] = None
) -> Tuple[List[Visita], float, int]:
    """
    Optimizar ruta de visitas usando algoritmo Nearest Neighbor (Vecino más Cercano).
    
    Este es un algoritmo greedy que siempre elige la siguiente visita más cercana.
    No es óptimo pero es rápido y proporciona resultados razonables para MVP.
    
    Args:
        visitas: Lista de visitas a optimizar
        punto_inicio: Tupla (lat, lng) del punto de inicio. Si no se proporciona, usa la primera visita.
        
    Returns:
        Tuple con:
        - Lista de visitas ordenadas
        - Distancia total en km
        - Tiempo total en minutos
    """
    if not visitas:
        return [], 0.0, 0
    
    # Filtrar visitas sin coordenadas
    visitas_con_coords = [v for v in visitas if v.latitud and v.longitud]
    
    if not visitas_con_coords:
        logger.warning("No hay visitas con coordenadas para optimizar")
        return visitas, 0.0, 0
    
    # Si no tenemos punto de inicio, usar la primera visita con coordenadas
    if not punto_inicio:
        punto_inicio = (float(visitas_con_coords[0].latitud), float(visitas_con_coords[0].longitud))
    
    # Algoritmo Nearest Neighbor
    ruta_optimizada = []
    visitas_pendientes = visitas_con_coords.copy()
    posicion_actual = punto_inicio
    distancia_total = 0.0
    tiempo_total = 0
    
    while visitas_pendientes:
        # Encontrar la visita más cercana a la posición actual
        visita_mas_cercana = None
        distancia_minima = float('inf')
        
        for visita in visitas_pendientes:
            distancia = calcular_distancia_haversine(
                posicion_actual[0], posicion_actual[1],
                float(visita.latitud), float(visita.longitud)
            )
            
            # Ajustar por prioridad: visitas de alta prioridad tienen un "descuento" en distancia
            if visita.prioridad.value == "alta":
                distancia *= 0.7  # 30% menos distancia efectiva
            elif visita.prioridad.value == "media":
                distancia *= 1.0  # Sin cambio
            else:  # baja
                distancia *= 1.3  # 30% más distancia efectiva
            
            if distancia < distancia_minima:
                distancia_minima = distancia
                visita_mas_cercana = visita
        
        if visita_mas_cercana:
            # Calcular distancia real (sin ajuste de prioridad)
            distancia_real = calcular_distancia_haversine(
                posicion_actual[0], posicion_actual[1],
                float(visita_mas_cercana.latitud), float(visita_mas_cercana.longitud)
            )
            
            distancia_total += distancia_real
            tiempo_viaje = calcular_tiempo_viaje_minutos(distancia_real)
            tiempo_total += tiempo_viaje + visita_mas_cercana.duracion_estimada_minutos
            
            ruta_optimizada.append(visita_mas_cercana)
            visitas_pendientes.remove(visita_mas_cercana)
            posicion_actual = (float(visita_mas_cercana.latitud), float(visita_mas_cercana.longitud))
    
    # Agregar visitas sin coordenadas al final
    visitas_sin_coords = [v for v in visitas if not (v.latitud and v.longitud)]
    ruta_optimizada.extend(visitas_sin_coords)
    
    logger.info(f"✅ Ruta optimizada: {len(ruta_optimizada)} visitas, {distancia_total:.2f} km, {tiempo_total} min")
    
    return ruta_optimizada, distancia_total, tiempo_total


def calcular_horarios_sugeridos(
    visitas_ordenadas: List[Visita],
    hora_inicio: time = time(8, 0)
) -> List[Visita]:
    """
    Calcular horarios sugeridos para cada visita basados en el orden y tiempos de viaje.
    
    Args:
        visitas_ordenadas: Lista de visitas ya ordenadas
        hora_inicio: Hora de inicio de la jornada
        
    Returns:
        Lista de visitas con horarios actualizados
    """
    if not visitas_ordenadas:
        return []
    
    hora_actual = datetime.combine(datetime.today(), hora_inicio)
    posicion_anterior = None
    
    for i, visita in enumerate(visitas_ordenadas):
        # Calcular tiempo de viaje desde visita anterior
        if i > 0 and posicion_anterior and visita.latitud and visita.longitud:
            distancia = calcular_distancia_haversine(
                posicion_anterior[0], posicion_anterior[1],
                float(visita.latitud), float(visita.longitud)
            )
            tiempo_viaje = calcular_tiempo_viaje_minutos(distancia)
            hora_actual += timedelta(minutes=tiempo_viaje)
        
        # Asignar horarios
        visita.hora_inicio_sugerida = hora_actual.time()
        hora_actual += timedelta(minutes=visita.duracion_estimada_minutos)
        visita.hora_fin_sugerida = hora_actual.time()
        visita.orden_en_ruta = i + 1
        
        # Actualizar posición
        if visita.latitud and visita.longitud:
            posicion_anterior = (float(visita.latitud), float(visita.longitud))
    
    return visitas_ordenadas


def construir_visitas_en_ruta(visitas_ordenadas: List[Visita]) -> List[VisitaEnRuta]:
    """
    Construir lista de VisitaEnRuta con información de distancias y tiempos entre visitas.
    
    Args:
        visitas_ordenadas: Lista de visitas ya ordenadas con horarios
        
    Returns:
        Lista de VisitaEnRuta con metadatos de distancia/tiempo
    """
    if not visitas_ordenadas:
        return []
    
    visitas_en_ruta = []
    posicion_anterior = None
    
    for visita in visitas_ordenadas:
        distancia_desde_anterior = None
        tiempo_viaje_desde_anterior = None
        
        # Calcular distancia y tiempo desde visita anterior
        if posicion_anterior and visita.latitud and visita.longitud:
            distancia_desde_anterior = calcular_distancia_haversine(
                posicion_anterior[0], posicion_anterior[1],
                float(visita.latitud), float(visita.longitud)
            )
            tiempo_viaje_desde_anterior = calcular_tiempo_viaje_minutos(distancia_desde_anterior)
        
        visita_en_ruta = VisitaEnRuta(
            visita_id=visita.visita_id,
            cliente_id=visita.cliente_id,
            nombre_cliente=visita.nombre_cliente,
            direccion_cliente=visita.direccion_cliente,
            latitud=float(visita.latitud) if visita.latitud else None,
            longitud=float(visita.longitud) if visita.longitud else None,
            hora_inicio_sugerida=visita.hora_inicio_sugerida,
            hora_fin_sugerida=visita.hora_fin_sugerida,
            duracion_estimada_minutos=visita.duracion_estimada_minutos,
            orden_en_ruta=visita.orden_en_ruta,
            prioridad=visita.prioridad,
            distancia_desde_anterior_km=round(distancia_desde_anterior, 2) if distancia_desde_anterior else None,
            tiempo_viaje_desde_anterior_min=tiempo_viaje_desde_anterior
        )
        
        visitas_en_ruta.append(visita_en_ruta)
        
        # Actualizar posición anterior
        if visita.latitud and visita.longitud:
            posicion_anterior = (float(visita.latitud), float(visita.longitud))
    
    return visitas_en_ruta


class RutaOptimizer:
    """
    Clase principal para optimización de rutas
    """
    
    @staticmethod
    def optimizar_y_guardar_ruta(
        db_session,
        gerente_id: int,
        fecha_ruta,
        visitas: List[Visita],
        punto_inicio: Optional[Tuple[float, float]] = None,
        origen: OrigenRuta = OrigenRuta.RECALCULADA
    ) -> RutaVisita:
        """
        Optimizar ruta y guardarla en la base de datos.
        
        Args:
            db_session: Sesión de SQLAlchemy
            gerente_id: ID del gerente
            fecha_ruta: Fecha de la ruta
            visitas: Lista de visitas a optimizar
            punto_inicio: Punto de inicio opcional
            origen: Origen de la ruta
            
        Returns:
            RutaVisita creada y guardada
        """
        # Optimizar ruta
        visitas_ordenadas, distancia_total, tiempo_total = optimizar_ruta_nearest_neighbor(
            visitas, punto_inicio
        )
        
        # Calcular horarios sugeridos
        visitas_con_horarios = calcular_horarios_sugeridos(visitas_ordenadas)
        
        # Desactivar rutas anteriores
        db_session.query(RutaVisita).filter(
            RutaVisita.gerente_id == gerente_id,
            RutaVisita.fecha_ruta == fecha_ruta,
            RutaVisita.activa == True
        ).update({"activa": False})
        
        # Obtener versión siguiente
        ultima_ruta = db_session.query(RutaVisita).filter(
            RutaVisita.gerente_id == gerente_id,
            RutaVisita.fecha_ruta == fecha_ruta
        ).order_by(RutaVisita.version_ruta.desc()).first()
        
        version_siguiente = (ultima_ruta.version_ruta + 1) if ultima_ruta else 1
        
        # Calcular horarios de inicio y fin
        hora_inicio = visitas_con_horarios[0].hora_inicio_sugerida if visitas_con_horarios else None
        hora_fin = visitas_con_horarios[-1].hora_fin_sugerida if visitas_con_horarios else None
        
        # Crear nueva ruta
        ruta = RutaVisita(
            gerente_id=gerente_id,
            fecha_ruta=fecha_ruta,
            version_ruta=version_siguiente,
            distancia_total_km=round(distancia_total, 2),
            tiempo_total_minutos=tiempo_total,
            hora_inicio_sugerida=hora_inicio,
            hora_fin_sugerida=hora_fin,
            origen_ruta=origen,
            activa=True
        )
        
        db_session.add(ruta)
        db_session.flush()  # Para obtener ruta_id
        
        # Asociar visitas a la ruta
        for visita in visitas_con_horarios:
            visita.ruta_id = ruta.ruta_id
        
        db_session.commit()
        db_session.refresh(ruta)
        
        logger.info(f"✅ Ruta {ruta.ruta_id} v{ruta.version_ruta} guardada para gerente {gerente_id}")
        
        return ruta

