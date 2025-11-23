"""
Servicio de optimización de rutas VRP (Vehicle Routing Problem)
Implementación simplificada para MVP con validaciones de capacidad, 
cadena de frío y ventanas de tiempo.
"""
import math
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
import logging

from app.schemas.ruta import (
    GenerarRutasRequest, GenerarRutasResponse, RutaResponse,
    ParadaRutaResponse, UsoCapacidadResponse,
    RecalcularRutaRequest, RecalcularRutaResponse,
    PedidoRutaRequest, VehiculoRequest
)
from app.models.ruta import Vehiculo, Ruta, Parada, EstadoRuta
from app.models.pedido import Pedido

logger = logging.getLogger(__name__)

class OptimizadorRutas:
    """
    Optimizador de rutas simplificado para MVP.
    Usa algoritmo nearest neighbor con validaciones de restricciones.
    """
    
    # Velocidad promedio para estimaciones (km/h)
    VELOCIDAD_PROMEDIO_KMH = 30
    
    @staticmethod
    def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia entre dos puntos geográficos usando fórmula de Haversine.
        Retorna distancia en kilómetros.
        """
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distancia = R * c
        
        return distancia
    
    @staticmethod
    def calcular_tiempo_viaje(distancia_km: float, con_trafico: bool = False) -> int:
        """
        Calcula el tiempo de viaje en minutos.
        Si con_trafico=True, aplica un factor de congestión.
        """
        velocidad = OptimizadorRutas.VELOCIDAD_PROMEDIO_KMH
        if con_trafico:
            velocidad *= 0.7  # Reducir velocidad por tráfico
        
        tiempo_horas = distancia_km / velocidad
        tiempo_minutos = int(tiempo_horas * 60)
        return max(tiempo_minutos, 1)  # Mínimo 1 minuto
    
    @staticmethod
    def validar_ventana_tiempo(hora_llegada: str, ventana_inicio: str, ventana_fin: str) -> bool:
        """
        Valida si la hora de llegada está dentro de la ventana de tiempo.
        Formato: "HH:MM"
        """
        try:
            llegada = datetime.strptime(hora_llegada, "%H:%M")
            inicio = datetime.strptime(ventana_inicio, "%H:%M")
            fin = datetime.strptime(ventana_fin, "%H:%M")
            
            return inicio <= llegada <= fin
        except:
            return False
    
    @staticmethod
    def sumar_minutos_a_hora(hora: str, minutos: int) -> str:
        """
        Suma minutos a una hora en formato HH:MM.
        """
        try:
            hora_dt = datetime.strptime(hora, "%H:%M")
            nueva_hora = hora_dt + timedelta(minutes=minutos)
            return nueva_hora.strftime("%H:%M")
        except:
            return hora
    
    @staticmethod
    def calcular_matriz_distancias(
        depot: Dict[str, float],
        pedidos: List[PedidoRutaRequest]
    ) -> Dict[Tuple[str, str], float]:
        """
        Calcula matriz de distancias entre depot y todos los pedidos.
        Retorna diccionario con clave (origen_id, destino_id) -> distancia_km
        """
        matriz = {}
        
        # Distancias desde depot a cada pedido
        for pedido in pedidos:
            dist = OptimizadorRutas.calcular_distancia_haversine(
                depot['lat'], depot['lon'],
                pedido.lat, pedido.lon
            )
            matriz[('DEPOT', pedido.id)] = dist
            matriz[(pedido.id, 'DEPOT')] = dist
        
        # Distancias entre pedidos
        for i, p1 in enumerate(pedidos):
            for p2 in pedidos[i+1:]:
                dist = OptimizadorRutas.calcular_distancia_haversine(
                    p1.lat, p1.lon, p2.lat, p2.lon
                )
                matriz[(p1.id, p2.id)] = dist
                matriz[(p2.id, p1.id)] = dist
        
        return matriz
    
    @staticmethod
    def validar_restricciones_pedido(
        pedido: PedidoRutaRequest,
        vehiculo: VehiculoRequest,
        volumen_acumulado: float,
        peso_acumulado: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida si un pedido puede ser asignado a un vehículo.
        Retorna (válido, mensaje_error)
        """
        # Validar cadena de frío
        if pedido.requiere_frio and not vehiculo.cadena_frio:
            return False, f"Pedido {pedido.id} requiere cadena de frío pero vehículo {vehiculo.id} no la tiene"
        
        # Validar capacidad de volumen
        if volumen_acumulado + pedido.volumen > vehiculo.capacidad_volumen:
            return False, f"Capacidad de volumen excedida en vehículo {vehiculo.id}"
        
        # Validar capacidad de peso
        if peso_acumulado + pedido.peso > vehiculo.capacidad_peso:
            return False, f"Capacidad de peso excedida en vehículo {vehiculo.id}"
        
        return True, None
    
    @staticmethod
    def generar_ruta_nearest_neighbor(
        vehiculo: VehiculoRequest,
        pedidos_asignados: List[PedidoRutaRequest],
        matriz_distancias: Dict[Tuple[str, str], float],
        objetivo: str,
        con_trafico: bool = False
    ) -> Tuple[List[str], Dict[str, str], float, int, List[ParadaRutaResponse], List[str]]:
        """
        Genera una ruta usando algoritmo Nearest Neighbor.
        
        Retorna:
        - secuencia: lista de pedido_ids en orden
        - etas: diccionario {pedido_id: "HH:MM"}
        - distancia_total_km: float
        - duracion_total_minutos: int
        - paradas: lista de ParadaRutaResponse
        - warnings: lista de advertencias
        """
        if not pedidos_asignados:
            return [], {}, 0.0, 0, [], []
        
        warnings = []
        secuencia = []
        etas = {}
        paradas = []
        
        # Hora de inicio (asumimos 08:00)
        hora_actual = "08:00"
        posicion_actual = "DEPOT"
        
        pendientes = pedidos_asignados.copy()
        distancia_total = 0.0
        duracion_total = 0
        orden = 1
        
        # Algoritmo Nearest Neighbor
        while pendientes:
            # Encontrar el pedido más cercano
            mejor_pedido = None
            mejor_distancia = float('inf')
            
            for pedido in pendientes:
                clave = (posicion_actual, pedido.id)
                if clave in matriz_distancias:
                    dist = matriz_distancias[clave]
                    
                    # Si el objetivo es tiempo, considerar también ventanas
                    if objetivo == "min_tiempo":
                        # Penalizar si no cumple ventana
                        tiempo_viaje = OptimizadorRutas.calcular_tiempo_viaje(dist, con_trafico)
                        eta_estimado = OptimizadorRutas.sumar_minutos_a_hora(hora_actual, tiempo_viaje)
                        if not OptimizadorRutas.validar_ventana_tiempo(
                            eta_estimado, pedido.ventana_inicio, pedido.ventana_fin
                        ):
                            dist *= 1.5  # Penalización
                    
                    if dist < mejor_distancia:
                        mejor_distancia = dist
                        mejor_pedido = pedido
            
            if mejor_pedido is None:
                break
            
            # Agregar pedido a la secuencia
            pendientes.remove(mejor_pedido)
            secuencia.append(mejor_pedido.id)
            
            # Calcular tiempo de viaje
            tiempo_viaje = OptimizadorRutas.calcular_tiempo_viaje(mejor_distancia, con_trafico)
            hora_actual = OptimizadorRutas.sumar_minutos_a_hora(hora_actual, tiempo_viaje)
            
            # Validar ventana de tiempo
            cumple_ventana = OptimizadorRutas.validar_ventana_tiempo(
                hora_actual, mejor_pedido.ventana_inicio, mejor_pedido.ventana_fin
            )
            
            if not cumple_ventana:
                warnings.append(
                    f"Pedido {mejor_pedido.id}: ETA {hora_actual} fuera de ventana "
                    f"{mejor_pedido.ventana_inicio}-{mejor_pedido.ventana_fin}"
                )
            
            # Guardar ETA
            etas[mejor_pedido.id] = hora_actual
            
            # Crear parada
            parada = ParadaRutaResponse(
                pedido_id=mejor_pedido.id,
                orden=orden,
                eta=hora_actual,
                latitud=mejor_pedido.lat,
                longitud=mejor_pedido.lon,
                ventana_inicio=mejor_pedido.ventana_inicio,
                ventana_fin=mejor_pedido.ventana_fin,
                cumple_ventana=cumple_ventana,
                tiempo_servicio_minutos=mejor_pedido.tiempo_servicio_minutos
            )
            paradas.append(parada)
            
            # Actualizar posición y acumuladores
            posicion_actual = mejor_pedido.id
            distancia_total += mejor_distancia
            duracion_total += tiempo_viaje + mejor_pedido.tiempo_servicio_minutos
            hora_actual = OptimizadorRutas.sumar_minutos_a_hora(
                hora_actual, mejor_pedido.tiempo_servicio_minutos
            )
            orden += 1
        
        # Retorno al depot
        if posicion_actual != "DEPOT":
            clave = (posicion_actual, "DEPOT")
            if clave in matriz_distancias:
                dist_retorno = matriz_distancias[clave]
                tiempo_retorno = OptimizadorRutas.calcular_tiempo_viaje(dist_retorno, con_trafico)
                distancia_total += dist_retorno
                duracion_total += tiempo_retorno
        
        # Validar duración máxima
        if vehiculo.duracion_maxima_minutos and duracion_total > vehiculo.duracion_maxima_minutos:
            warnings.append(
                f"Vehículo {vehiculo.id}: duración {duracion_total} min excede máximo "
                f"{vehiculo.duracion_maxima_minutos} min"
            )
        
        return secuencia, etas, distancia_total, duracion_total, paradas, warnings

class RutasService:
    """Servicio de gestión de rutas de entrega"""
    
    @staticmethod
    async def generar_rutas(
        request: GenerarRutasRequest,
        usuario_id: Optional[int],
        db: Session
    ) -> GenerarRutasResponse:
        """
        Genera rutas óptimas para los pedidos y vehículos especificados.
        
        SLA: ≤ 3 segundos para ≤10 vehículos y ≤100 pedidos
        """
        inicio = time.time()
        
        # Validar tamaño del problema
        if len(request.vehiculos) > 10 or len(request.pedidos) > 100:
            raise ValueError(
                "Excede límite del MVP: máximo 10 vehículos y 100 pedidos. "
                "Para problemas más grandes, considere proceso asíncrono."
            )
        
        warnings_globales = []
        rutas_generadas = []
        
        # Asignar pedidos a vehículos (estrategia simple: FIFO por capacidad)
        pedidos_pendientes = request.pedidos.copy()
        
        for vehiculo in request.vehiculos:
            if not pedidos_pendientes:
                break
            
            # Filtrar pedidos que pueden ir en este vehículo
            pedidos_compatibles = []
            volumen_acum = 0.0
            peso_acum = 0.0
            
            for pedido in pedidos_pendientes[:]:
                valido, error_msg = OptimizadorRutas.validar_restricciones_pedido(
                    pedido, vehiculo, volumen_acum, peso_acum
                )
                
                if valido:
                    pedidos_compatibles.append(pedido)
                    pedidos_pendientes.remove(pedido)
                    volumen_acum += pedido.volumen
                    peso_acum += pedido.peso
                elif error_msg and pedido.requiere_frio:
                    # Advertencia específica de cadena de frío
                    warnings_globales.append(error_msg)
            
            if not pedidos_compatibles:
                continue
            
            # Calcular matriz de distancias
            depot_dict = {'lat': vehiculo.depot.lat, 'lon': vehiculo.depot.lon}
            matriz = OptimizadorRutas.calcular_matriz_distancias(depot_dict, pedidos_compatibles)
            
            # Generar ruta con Nearest Neighbor
            secuencia, etas, distancia, duracion, paradas, warnings = \
                OptimizadorRutas.generar_ruta_nearest_neighbor(
                    vehiculo=vehiculo,
                    pedidos_asignados=pedidos_compatibles,
                    matriz_distancias=matriz,
                    objetivo=request.objetivo,
                    con_trafico=request.limites.considerar_trafico if request.limites else False
                )
            
            warnings_globales.extend(warnings)
            
            # Calcular uso de capacidad
            volumen_total = sum(p.volumen for p in pedidos_compatibles)
            peso_total = sum(p.peso for p in pedidos_compatibles)
            porcentaje_vol = (volumen_total / vehiculo.capacidad_volumen) * 100
            porcentaje_peso = (peso_total / vehiculo.capacidad_peso) * 100
            porcentaje = max(porcentaje_vol, porcentaje_peso)
            
            uso_capacidad = UsoCapacidadResponse(
                volumen=volumen_total,
                peso=peso_total,
                porcentaje=round(porcentaje, 2)
            )
            
            # Crear respuesta de ruta
            ruta_resp = RutaResponse(
                vehiculo_id=vehiculo.id,
                orden=["DEPOT"] + secuencia + ["DEPOT"],
                paradas=paradas,
                distancia_km=round(distancia, 2),
                duracion_minutos=duracion,
                uso_capacidad=uso_capacidad
            )
            
            rutas_generadas.append(ruta_resp)
        
        # Advertir sobre pedidos no asignados
        if pedidos_pendientes:
            ids_pendientes = [p.id for p in pedidos_pendientes]
            warnings_globales.append(
                f"No se pudieron asignar {len(pedidos_pendientes)} pedidos: {', '.join(ids_pendientes[:5])}..."
            )
        
        # Calcular tiempo de ejecución
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        # Validar SLA
        if tiempo_ms > 3000:
            warnings_globales.append(f"Tiempo de cálculo ({tiempo_ms}ms) excede SLA de 3000ms")
        
        logger.info(f"Rutas generadas en {tiempo_ms}ms: {len(rutas_generadas)} rutas para {len(request.pedidos)} pedidos")
        
        # ==================== GUARDAR RUTAS EN BD ====================
        # Crear entrada principal de Ruta con la primera ruta generada
        ruta_id = None
        if rutas_generadas:
            ruta_id = str(uuid.uuid4())
            
            # Crear registro principal de Ruta (usando la primera ruta como principal)
            primera_ruta = rutas_generadas[0]
            ruta_bd = Ruta(
                ruta_id=ruta_id,
                vehiculo_id=primera_ruta.vehiculo_id,
                estado=EstadoRuta.BORRADOR,
                distancia_total_km=primera_ruta.distancia_km,
                duracion_total_minutos=primera_ruta.duracion_minutos,
                volumen_utilizado=primera_ruta.uso_capacidad.volumen,
                peso_utilizado=primera_ruta.uso_capacidad.peso,
                porcentaje_capacidad=primera_ruta.uso_capacidad.porcentaje,
                secuencia_pedidos=primera_ruta.orden,
                etas={p.pedido_id: p.eta for p in primera_ruta.paradas if p.pedido_id != "DEPOT"},
                advertencias=warnings_globales if warnings_globales else None,
                usuario_creador_id=usuario_id
            )
            db.add(ruta_bd)
            
            # Crear registros de Parada para cada parada
            for idx, parada in enumerate(primera_ruta.paradas):
                parada_bd = Parada(
                    ruta_id=ruta_id,
                    pedido_id=parada.pedido_id,
                    orden=idx,
                    eta=parada.eta,
                    latitud=parada.latitud,
                    longitud=parada.longitud,
                    ventana_inicio=parada.ventana_inicio,
                    ventana_fin=parada.ventana_fin,
                    cumple_ventana=parada.cumple_ventana,
                    tiempo_servicio_minutos=parada.tiempo_servicio_minutos
                )
                db.add(parada_bd)
            
            try:
                db.commit()
                logger.info(f"Ruta {ruta_id} guardada en BD con {len(primera_ruta.paradas)} paradas")
            except Exception as e:
                db.rollback()
                logger.error(f"Error al guardar ruta en BD: {str(e)}", exc_info=True)
                ruta_id = None  # Si falla el guardado, no retornar ruta_id
        
        return GenerarRutasResponse(
            ruta_id=ruta_id,
            rutas=rutas_generadas,
            warnings=warnings_globales,
            tiempo_calculo_ms=tiempo_ms
        )
    
    @staticmethod
    async def recalcular_ruta(
        request: RecalcularRutaRequest,
        usuario_id: Optional[int],
        db: Session
    ) -> RecalcularRutaResponse:
        """
        Recalcula una ruta tras ajuste manual de la secuencia.
        
        SLA: ≤ 1 segundo
        """
        inicio = time.time()
        
        # Obtener ruta existente
        ruta = db.query(Ruta).filter(Ruta.ruta_id == request.ruta_id).first()
        if not ruta:
            raise ValueError(f"Ruta {request.ruta_id} no encontrada")
        
        # Obtener paradas actuales
        paradas_actuales = db.query(Parada).filter(
            Parada.ruta_id == request.ruta_id
        ).all()
        
        # Validar que la nueva secuencia contenga los mismos pedidos
        pedidos_actuales = {str(p.pedido_id) for p in paradas_actuales}
        pedidos_nuevos = set(request.nueva_secuencia)
        
        if pedidos_actuales != pedidos_nuevos:
            raise ValueError(
                "La nueva secuencia debe contener exactamente los mismos pedidos que la ruta original"
            )
        
        # Obtener datos de pedidos desde BD
        pedidos_dict = {}
        for parada in paradas_actuales:
            pedidos_dict[str(parada.pedido_id)] = parada
        
        # Obtener vehículo
        vehiculo = ruta.vehiculo
        
        warnings = []
        paradas_recalculadas = []
        distancia_total = 0.0
        duracion_total = 0
        hora_actual = "08:00"
        
        # Recalcular con nueva secuencia
        depot_dict = {
            'lat': vehiculo.depot_latitud,
            'lon': vehiculo.depot_longitud
        }
        
        posicion_actual_lat = vehiculo.depot_latitud
        posicion_actual_lon = vehiculo.depot_longitud
        
        for orden, pedido_id in enumerate(request.nueva_secuencia, start=1):
            parada_orig = pedidos_dict[pedido_id]
            
            # Calcular distancia desde posición actual
            dist = OptimizadorRutas.calcular_distancia_haversine(
                posicion_actual_lat, posicion_actual_lon,
                parada_orig.latitud, parada_orig.longitud
            )
            
            # Calcular tiempo de viaje
            tiempo_viaje = OptimizadorRutas.calcular_tiempo_viaje(dist, False)
            hora_actual = OptimizadorRutas.sumar_minutos_a_hora(hora_actual, tiempo_viaje)
            
            # Validar ventana
            cumple_ventana = OptimizadorRutas.validar_ventana_tiempo(
                hora_actual,
                parada_orig.ventana_inicio or "00:00",
                parada_orig.ventana_fin or "23:59"
            )
            
            if not cumple_ventana:
                # BLOQUEAR el cambio si viola ventana de tiempo
                raise ValueError(
                    f"Pedido {pedido_id}: nueva secuencia viola ventana de tiempo. "
                    f"ETA {hora_actual} fuera de {parada_orig.ventana_inicio}-{parada_orig.ventana_fin}"
                )
            
            # Crear parada recalculada
            parada_resp = ParadaRutaResponse(
                pedido_id=pedido_id,
                orden=orden,
                eta=hora_actual,
                latitud=parada_orig.latitud,
                longitud=parada_orig.longitud,
                ventana_inicio=parada_orig.ventana_inicio,
                ventana_fin=parada_orig.ventana_fin,
                cumple_ventana=cumple_ventana,
                tiempo_servicio_minutos=parada_orig.tiempo_servicio_minutos
            )
            paradas_recalculadas.append(parada_resp)
            
            # Actualizar acumuladores
            distancia_total += dist
            duracion_total += tiempo_viaje + parada_orig.tiempo_servicio_minutos
            hora_actual = OptimizadorRutas.sumar_minutos_a_hora(
                hora_actual, parada_orig.tiempo_servicio_minutos
            )
            
            # Actualizar posición
            posicion_actual_lat = parada_orig.latitud
            posicion_actual_lon = parada_orig.longitud
        
        # Retorno al depot
        dist_retorno = OptimizadorRutas.calcular_distancia_haversine(
            posicion_actual_lat, posicion_actual_lon,
            vehiculo.depot_latitud, vehiculo.depot_longitud
        )
        tiempo_retorno = OptimizadorRutas.calcular_tiempo_viaje(dist_retorno, False)
        distancia_total += dist_retorno
        duracion_total += tiempo_retorno
        
        # Validar duración máxima
        if vehiculo.duracion_maxima_minutos and duracion_total > vehiculo.duracion_maxima_minutos:
            # BLOQUEAR si excede duración máxima
            raise ValueError(
                f"Nueva secuencia excede duración máxima: {duracion_total} min > "
                f"{vehiculo.duracion_maxima_minutos} min"
            )
        
        # Calcular uso de capacidad (no cambia con reordenamiento)
        volumen_total = sum(p.latitud for p in paradas_actuales)  # Placeholder, debería venir de pedido
        peso_total = ruta.peso_utilizado or 0
        porcentaje = ruta.porcentaje_capacidad or 0
        
        uso_capacidad = UsoCapacidadResponse(
            volumen=ruta.volumen_utilizado or 0,
            peso=peso_total,
            porcentaje=porcentaje
        )
        
        # Crear respuesta
        ruta_resp = RutaResponse(
            vehiculo_id=vehiculo.vehiculo_id,
            orden=["DEPOT"] + request.nueva_secuencia + ["DEPOT"],
            paradas=paradas_recalculadas,
            distancia_km=round(distancia_total, 2),
            duracion_minutos=duracion_total,
            uso_capacidad=uso_capacidad
        )
        
        # Actualizar BD
        ruta.secuencia_pedidos = request.nueva_secuencia
        ruta.distancia_total_km = distancia_total
        ruta.duracion_total_minutos = duracion_total
        ruta.advertencias = warnings
        
        # Actualizar paradas
        for i, parada_resp in enumerate(paradas_recalculadas):
            parada_db = next(p for p in paradas_actuales if str(p.pedido_id) == parada_resp.pedido_id)
            parada_db.orden = parada_resp.orden
            parada_db.eta = parada_resp.eta
            parada_db.cumple_ventana = parada_resp.cumple_ventana
        
        db.commit()
        
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        # Validar SLA
        if tiempo_ms > 1000:
            warnings.append(f"Tiempo de recálculo ({tiempo_ms}ms) excede SLA de 1000ms")
        
        logger.info(f"Ruta {request.ruta_id} recalculada en {tiempo_ms}ms")
        
        return RecalcularRutaResponse(
            ruta=ruta_resp,
            warnings=warnings,
            tiempo_calculo_ms=tiempo_ms
        )
    
    @staticmethod
    def crear_vehiculo(request, db: Session) -> Vehiculo:
        """Crea un nuevo vehículo"""
        vehiculo = Vehiculo(**request.dict())
        db.add(vehiculo)
        db.commit()
        db.refresh(vehiculo)
        return vehiculo
    
    @staticmethod
    def listar_vehiculos(db: Session, solo_activos: bool = True):
        """Lista todos los vehículos"""
        query = db.query(Vehiculo)
        if solo_activos:
            query = query.filter(Vehiculo.activo == True)
        return query.all()
    
    @staticmethod
    def listar_rutas(
        db: Session, 
        estado: Optional[str] = None,
        vehiculo_id: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limit: int = 100
    ):
        """
        Lista rutas de entrega con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            estado: Filtrar por estado (borrador, confirmada, en_proceso, completada, cancelada)
            vehiculo_id: Filtrar por ID de vehículo
            fecha_desde: Filtrar rutas desde esta fecha (YYYY-MM-DD)
            fecha_hasta: Filtrar rutas hasta esta fecha (YYYY-MM-DD)
            limit: Número máximo de resultados (default 100)
        
        Returns:
            Lista de rutas con sus paradas
        """
        query = db.query(Ruta).order_by(Ruta.fecha_creacion.desc())
        
        # Aplicar filtros
        if estado:
            query = query.filter(Ruta.estado == estado)
        
        if vehiculo_id:
            query = query.filter(Ruta.vehiculo_id == vehiculo_id)
        
        if fecha_desde:
            query = query.filter(Ruta.fecha_creacion >= fecha_desde)
        
        if fecha_hasta:
            from datetime import datetime, timedelta
            # Incluir todo el día de fecha_hasta
            fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Ruta.fecha_creacion < fecha_hasta_dt)
        
        return query.limit(limit).all()
