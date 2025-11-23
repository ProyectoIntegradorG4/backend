"""
Rutas API para gestión de rutas de entrega (HU-WEB-012)
Endpoints para Supervisor de Logística
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database.connection import get_db
from app.schemas.ruta import (
    GenerarRutasRequest, GenerarRutasResponse,
    RecalcularRutaRequest, RecalcularRutaResponse,
    CrearVehiculoRequest, VehiculoResponse,
    ListarVehiculosResponse
)
from app.services.rutas import RutasService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/logistica", tags=["Rutas de Entrega"])

# ==================== Validación RBAC ====================

async def require_supervisor_logistica(
    rol_usuario: str = Header(..., alias="rol-usuario"),
    usuario_id: Optional[str] = Header(None, alias="usuario-id"),
    nit_usuario: Optional[str] = Header(None, alias="nit-usuario")
):
    """
    Dependency para validar que el usuario tiene rol admin o gerente_cuenta.
    """
    roles_permitidos = ["admin", "gerente_cuenta"]
    
    if rol_usuario not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acceso denegado. Se requiere rol 'admin' o 'gerente_cuenta', pero se recibió '{rol_usuario}'"
        )
    
    # Retornar datos del usuario para uso en endpoints
    try:
        usuario_id_int = int(usuario_id) if usuario_id else None
    except:
        usuario_id_int = None
    
    return {
        "usuario_id": usuario_id_int,
        "rol": rol_usuario,
        "nit": nit_usuario
    }

# ==================== Endpoints de Generación de Rutas ====================

@router.post(
    "/rutas/generar",
    response_model=GenerarRutasResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar rutas optimizadas",
    description="""
    Genera rutas optimizadas para los pedidos y vehículos especificados.
    
    **Restricciones del MVP:**
    - Máximo 10 vehículos
    - Máximo 100 pedidos
    - SLA: ≤ 3 segundos
    
    **Algoritmo:** Nearest Neighbor con validaciones de:
    - Capacidad de volumen y peso
    - Cadena de frío
    - Ventanas de tiempo
    - Duración máxima de ruta
    
    **Acceso:** Requiere rol "admin" o "gerente_cuenta"
    """
)
async def generar_rutas(
    request: GenerarRutasRequest,
    usuario_auth: dict = Depends(require_supervisor_logistica),
    db: Session = Depends(get_db)
):
    """
    Endpoint principal para generar rutas optimizadas.
    
    Valida restricciones hard (capacidad, cadena frío) y retorna warnings para soft constraints.
    """
    try:
        logger.info(
            f"Usuario {usuario_auth['usuario_id']} generando rutas: "
            f"{len(request.vehiculos)} vehículos, {len(request.pedidos)} pedidos, "
            f"objetivo={request.objetivo}"
        )
        
        resultado = await RutasService.generar_rutas(
            request=request,
            usuario_id=usuario_auth['usuario_id'],
            db=db
        )
        
        logger.info(
            f"Rutas generadas exitosamente: {len(resultado.rutas)} rutas, "
            f"{resultado.tiempo_calculo_ms}ms"
        )
        
        return resultado
        
    except ValueError as e:
        logger.warning(f"Error de validación en generación de rutas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error inesperado en generación de rutas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar rutas. Contacte al administrador."
        )

@router.post(
    "/rutas/recalcular",
    response_model=RecalcularRutaResponse,
    status_code=status.HTTP_200_OK,
    summary="Recalcular ruta con nueva secuencia",
    description="""
    Recalcula una ruta existente tras ajuste manual de la secuencia de pedidos.
    
    **Validaciones:**
    - La nueva secuencia debe contener exactamente los mismos pedidos
    - Las ventanas de tiempo deben seguir cumpliéndose (hard constraint)
    - La duración máxima no debe excederse (hard constraint)
    
    **SLA:** ≤ 1 segundo
    
    **Acceso:** Requiere rol "admin" o "gerente_cuenta"
    """
)
async def recalcular_ruta(
    request: RecalcularRutaRequest,
    usuario_auth: dict = Depends(require_supervisor_logistica),
    db: Session = Depends(get_db)
):
    """
    Endpoint para recalcular ruta tras drag-and-drop en UI.
    
    Bloquea cambios que violen ventanas de tiempo o duración máxima.
    """
    try:
        logger.info(
            f"Usuario {usuario_auth['usuario_id']} recalculando ruta {request.ruta_id}: "
            f"nueva secuencia {request.nueva_secuencia}"
        )
        
        resultado = await RutasService.recalcular_ruta(
            request=request,
            usuario_id=usuario_auth['usuario_id'],
            db=db
        )
        
        logger.info(
            f"Ruta {request.ruta_id} recalculada exitosamente: "
            f"{resultado.tiempo_calculo_ms}ms"
        )
        
        return resultado
        
    except ValueError as e:
        logger.warning(f"Error de validación en recálculo de ruta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error inesperado en recálculo de ruta: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al recalcular ruta. Contacte al administrador."
        )

# ==================== Endpoints de Gestión de Vehículos ====================

@router.post(
    "/vehiculos",
    response_model=VehiculoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo vehículo",
    description="Registra un nuevo vehículo en el sistema. Requiere rol admin o gerente_cuenta."
)
async def crear_vehiculo(
    request: CrearVehiculoRequest,
    usuario_auth: dict = Depends(require_supervisor_logistica),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo vehículo para planificación de rutas.
    """
    try:
        logger.info(
            f"Usuario {usuario_auth['usuario_id']} creando vehículo {request.vehiculo_id}"
        )
        
        vehiculo = RutasService.crear_vehiculo(request, db)
        
        logger.info(f"Vehículo {vehiculo.vehiculo_id} creado exitosamente")
        
        return VehiculoResponse(
            vehiculo_id=vehiculo.vehiculo_id,
            nombre=vehiculo.nombre,
            capacidad_volumen=vehiculo.capacidad_volumen,
            capacidad_peso=vehiculo.capacidad_peso,
            cadena_frio=vehiculo.cadena_frio,
            depot_latitud=vehiculo.depot_latitud,
            depot_longitud=vehiculo.depot_longitud,
            depot_direccion=vehiculo.depot_direccion,
            duracion_maxima_minutos=vehiculo.duracion_maxima_minutos,
            activo=vehiculo.activo
        )
        
    except Exception as e:
        logger.error(f"Error al crear vehículo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear vehículo"
        )

@router.get(
    "/vehiculos",
    response_model=ListarVehiculosResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar vehículos",
    description="Lista todos los vehículos disponibles. Requiere rol admin o gerente_cuenta."
)
async def listar_vehiculos(
    solo_activos: bool = Query(True, description="Filtrar solo vehículos activos"),
    usuario_auth: dict = Depends(require_supervisor_logistica),
    db: Session = Depends(get_db)
):
    """
    Lista todos los vehículos del sistema.
    """
    try:
        vehiculos = RutasService.listar_vehiculos(db, solo_activos=solo_activos)
        
        vehiculos_response = [
            VehiculoResponse(
                vehiculo_id=v.vehiculo_id,
                nombre=v.nombre,
                capacidad_volumen=v.capacidad_volumen,
                capacidad_peso=v.capacidad_peso,
                cadena_frio=v.cadena_frio,
                depot_latitud=v.depot_latitud,
                depot_longitud=v.depot_longitud,
                depot_direccion=v.depot_direccion,
                duracion_maxima_minutos=v.duracion_maxima_minutos,
                activo=v.activo
            )
            for v in vehiculos
        ]
        
        return ListarVehiculosResponse(
            total=len(vehiculos_response),
            vehiculos=vehiculos_response
        )
        
    except Exception as e:
        logger.error(f"Error al listar vehículos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar vehículos"
        )

# ==================== Health Check ====================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check del módulo de rutas",
    tags=["Health"]
)
async def health_check():
    """
    Verifica que el módulo de rutas está operativo.
    """
    return {
        "status": "healthy",
        "service": "rutas-logistica",
        "version": "1.0.0"
    }
