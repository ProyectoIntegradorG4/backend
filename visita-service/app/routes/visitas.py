from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.visita_service import VisitaService
from app.services.ruta_optimizer import RutaOptimizer, construir_visitas_en_ruta
from app.models.visita import (
    VisitaCreate, VisitaUpdate, VisitaResponse, VisitaListResponse,
    RutaVisitaResponse, RecalcularRutaRequest, ClientesDisponiblesZonaResponse,
    EstadoVisita, VisitaEnRuta, OrigenRuta
)
from typing import Optional
from datetime import date
import logging

logger = logging.getLogger("uvicorn")

router = APIRouter()


@router.post("/visitas", response_model=VisitaResponse, status_code=201)
async def create_visita(
    visita_data: VisitaCreate,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva visita programada.
    
    - **gerente_id**: ID del gerente responsable
    - **cliente_id**: ID del cliente a visitar
    - **fecha_visita**: Fecha programada (YYYY-MM-DD)
    - **hora_inicio_sugerida**: Hora sugerida de inicio (HH:MM:SS)
    - **duracion_estimada_minutos**: Duración en minutos (default: 60)
    - **prioridad**: alta, media o baja (default: media)
    - **observaciones**: Notas opcionales
    
    Valida que el gerente tenga acceso al cliente y obtiene automáticamente
    las coordenadas y datos del cliente desde cliente-service.
    """
    try:
        visita_service = VisitaService(db)
        visita = await visita_service.create_visita(visita_data)
        
        logger.info(f"✅ Visita {visita.visita_id} creada exitosamente")
        return visita
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear visita: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al crear visita")


@router.get("/visitas/{visita_id}", response_model=VisitaResponse)
async def get_visita(
    visita_id: int,
    gerente_id: int = Query(..., description="ID del gerente (validación)"),
    db: Session = Depends(get_db)
):
    """
    Obtener detalle de una visita específica.
    
    Valida que la visita pertenezca al gerente solicitante.
    """
    try:
        visita_service = VisitaService(db)
        visita = visita_service.get_visita_by_id(visita_id, gerente_id)
        
        if not visita:
            raise HTTPException(
                status_code=404,
                detail=f"Visita {visita_id} no encontrada o no pertenece al gerente {gerente_id}"
            )
        
        return VisitaResponse.model_validate(visita)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener visita {visita_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al obtener visita")


@router.put("/visitas/{visita_id}", response_model=VisitaResponse)
async def update_visita(
    visita_id: int,
    visita_update: VisitaUpdate,
    gerente_id: int = Query(..., description="ID del gerente (validación)"),
    db: Session = Depends(get_db)
):
    """
    Actualizar visita existente.
    
    Permite actualizar fecha, hora, duración, prioridad, estado y observaciones.
    Valida que la visita pertenezca al gerente.
    """
    try:
        visita_service = VisitaService(db)
        visita = visita_service.update_visita(visita_id, gerente_id, visita_update)
        
        logger.info(f"✅ Visita {visita_id} actualizada")
        return visita
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar visita {visita_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar visita")


@router.delete("/visitas/{visita_id}", status_code=204)
async def delete_visita(
    visita_id: int,
    gerente_id: int = Query(..., description="ID del gerente (validación)"),
    db: Session = Depends(get_db)
):
    """
    Cancelar visita (soft delete).
    
    Cambia el estado de la visita a 'cancelada'.
    Valida que la visita pertenezca al gerente.
    """
    try:
        visita_service = VisitaService(db)
        visita_service.delete_visita(visita_id, gerente_id)
        
        logger.info(f"✅ Visita {visita_id} cancelada")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al cancelar visita {visita_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al cancelar visita")


@router.get("/visitas", response_model=VisitaListResponse)
async def get_visitas(
    gerente_id: int = Query(..., description="ID del gerente"),
    fecha: date = Query(..., description="Fecha de las visitas (YYYY-MM-DD)"),
    estado: Optional[EstadoVisita] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de visitas programadas para un gerente en una fecha.
    
    Retorna visitas sin optimización, solo ordenadas por hora de inicio.
    Para ver la ruta optimizada, usar `/rutas-visitas`.
    """
    try:
        visita_service = VisitaService(db)
        visitas = visita_service.get_visitas_by_gerente_fecha(gerente_id, fecha, estado)
        
        visitas_response = [VisitaResponse.model_validate(v) for v in visitas]
        
        logger.info(f"✅ {len(visitas)} visitas retornadas para gerente {gerente_id} en {fecha}")
        
        return VisitaListResponse(
            total=len(visitas_response),
            visitas=visitas_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener visitas: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al obtener visitas")


@router.get("/rutas-visitas", response_model=RutaVisitaResponse)
async def get_ruta_visitas(
    gerente_id: int = Query(..., description="ID del gerente"),
    fecha: date = Query(..., description="Fecha de la ruta (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    **[HU-MOV-003] Obtener ruta optimizada de visitas para una fecha.**
    
    Retorna la ruta optimizada con:
    - Lista ordenada de visitas
    - Orden recomendado de ejecución
    - Tiempos estimados entre visitas
    - Distancias calculadas
    - Horarios sugeridos
    
    Si no existe ruta calculada, genera una automáticamente.
    Si no hay visitas programadas, retorna ruta vacía.
    """
    try:
        visita_service = VisitaService(db)
        
        # Buscar ruta existente
        ruta = visita_service.get_ruta_by_gerente_fecha(gerente_id, fecha)
        
        # Si no hay ruta, obtener visitas y optimizar
        if not ruta:
            visitas = visita_service.get_visitas_by_gerente_fecha(gerente_id, fecha)
            
            if not visitas:
                # No hay visitas programadas - retornar ruta vacía
                ruta = visita_service.crear_ruta_vacia(gerente_id, fecha)
                
                return RutaVisitaResponse(
                    ruta_id=ruta.ruta_id,
                    gerente_id=ruta.gerente_id,
                    fecha_ruta=ruta.fecha_ruta,
                    version_ruta=ruta.version_ruta,
                    distancia_total_km=0,
                    tiempo_total_minutos=0,
                    hora_inicio_sugerida=None,
                    hora_fin_sugerida=None,
                    origen_ruta=ruta.origen_ruta,
                    fecha_calculo=ruta.fecha_calculo,
                    activa=ruta.activa,
                    visitas=[],
                    cantidad_visitas=0
                )
            
            # Optimizar y guardar ruta
            ruta = RutaOptimizer.optimizar_y_guardar_ruta(
                db,
                gerente_id,
                fecha,
                visitas,
                origen=OrigenRuta.PLANIFICADA
            )
        
        # Construir respuesta con visitas en ruta
        visitas_en_ruta = construir_visitas_en_ruta(ruta.visitas)
        
        response = RutaVisitaResponse(
            ruta_id=ruta.ruta_id,
            gerente_id=ruta.gerente_id,
            fecha_ruta=ruta.fecha_ruta,
            version_ruta=ruta.version_ruta,
            distancia_total_km=float(ruta.distancia_total_km) if ruta.distancia_total_km else 0,
            tiempo_total_minutos=ruta.tiempo_total_minutos or 0,
            hora_inicio_sugerida=ruta.hora_inicio_sugerida,
            hora_fin_sugerida=ruta.hora_fin_sugerida,
            origen_ruta=ruta.origen_ruta,
            fecha_calculo=ruta.fecha_calculo,
            activa=ruta.activa,
            visitas=visitas_en_ruta,
            cantidad_visitas=len(visitas_en_ruta)
        )
        
        logger.info(f"✅ Ruta {ruta.ruta_id} retornada para gerente {gerente_id} en {fecha}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener ruta: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error interno al obtener ruta")


@router.post("/rutas-visitas/recalcular", response_model=RutaVisitaResponse)
async def recalcular_ruta(
    request: RecalcularRutaRequest,
    db: Session = Depends(get_db)
):
    """
    **[HU-MOV-003] Recalcular ruta optimizada.**
    
    Fuerza el recálculo de la ruta para una fecha específica.
    Incrementa la versión de la ruta para tracking de cambios.
    
    Útil cuando:
    - Se agregan/eliminan visitas
    - Cambian prioridades
    - Se requiere reoptimización
    """
    try:
        visita_service = VisitaService(db)
        
        # Obtener visitas para la fecha
        visitas = visita_service.get_visitas_by_gerente_fecha(request.gerente_id, request.fecha)
        
        if not visitas:
            raise HTTPException(
                status_code=404,
                detail=f"No hay visitas programadas para {request.fecha}"
            )
        
        # Recalcular ruta
        ruta = RutaOptimizer.optimizar_y_guardar_ruta(
            db,
            request.gerente_id,
            request.fecha,
            visitas,
            origen=OrigenRuta.RECALCULADA
        )
        
        # Construir respuesta
        visitas_en_ruta = construir_visitas_en_ruta(ruta.visitas)
        
        response = RutaVisitaResponse(
            ruta_id=ruta.ruta_id,
            gerente_id=ruta.gerente_id,
            fecha_ruta=ruta.fecha_ruta,
            version_ruta=ruta.version_ruta,
            distancia_total_km=float(ruta.distancia_total_km) if ruta.distancia_total_km else 0,
            tiempo_total_minutos=ruta.tiempo_total_minutos or 0,
            hora_inicio_sugerida=ruta.hora_inicio_sugerida,
            hora_fin_sugerida=ruta.hora_fin_sugerida,
            origen_ruta=ruta.origen_ruta,
            fecha_calculo=ruta.fecha_calculo,
            activa=ruta.activa,
            visitas=visitas_en_ruta,
            cantidad_visitas=len(visitas_en_ruta)
        )
        
        logger.info(f"✅ Ruta {ruta.ruta_id} v{ruta.version_ruta} recalculada")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al recalcular ruta: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al recalcular ruta")


@router.get("/clientes-disponibles-zona", response_model=ClientesDisponiblesZonaResponse)
async def get_clientes_disponibles_zona(
    gerente_id: int = Query(..., description="ID del gerente"),
    fecha: date = Query(..., description="Fecha para verificar visitas (YYYY-MM-DD)"),
    lat: float = Query(..., description="Latitud del punto de referencia"),
    lng: float = Query(..., description="Longitud del punto de referencia"),
    radio_km: float = Query(20.0, ge=1, le=100, description="Radio de búsqueda en km"),
    db: Session = Depends(get_db)
):
    """
    **[HU-MOV-003] Obtener clientes disponibles en una zona geográfica.**
    
    Retorna clientes asignados al gerente dentro de un radio específico.
    Útil cuando no hay visitas programadas para mostrar opciones de clientes cercanos.
    
    - Filtra por radio desde punto de referencia
    - Indica si ya tienen visita programada para la fecha
    - Ordena por distancia (más cercanos primero)
    """
    try:
        visita_service = VisitaService(db)
        
        resultado = await visita_service.get_clientes_disponibles_zona(
            gerente_id, fecha, lat, lng, radio_km
        )
        
        logger.info(f"✅ {resultado.total} clientes en zona retornados para gerente {gerente_id}")
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener clientes en zona: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al obtener clientes")

