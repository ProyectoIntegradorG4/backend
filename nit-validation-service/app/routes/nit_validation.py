from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db, test_db_connection, test_redis_connection
from app.models.institucion import (
    NITValidationRequest,
    NITValidationResponse,
    InstitucionResponse,
    InstitucionCreateRequest,
    NITError,
    NITErrorCodes
)
from app.services.nit_validation_service import NITValidationService
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Instancia del servicio de validación
nit_service = NITValidationService()

@router.get("/health")
async def health_check():
    """Endpoint de health check con verificación de dependencias"""
    db_status = test_db_connection()
    redis_status = test_redis_connection()
    
    return {
        "status": "healthy" if db_status else "degraded",
        "service": "nit-validation-service",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": time.time()
    }

@router.post("/validate", response_model=NITValidationResponse)
async def validate_nit(
    request: NITValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validar un NIT contra la base de datos de instituciones asociadas
    
    - **nit**: NIT a validar (requerido)
    - **pais**: País para filtrar búsqueda (opcional)
    
    Retorna información de la institución si el NIT es válido y está activo.
    """
    try:
        start_time = time.time()
        
        # Validar NIT usando el servicio
        result = await nit_service.validate_nit(
            db=db, 
            nit=request.nit, 
            pais=request.pais
        )
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"NIT validation API completed in {processing_time:.2f}ms")
        
        # Si el NIT no es válido, retornar código de estado apropiado
        if not result.valid:
            return JSONResponse(
                status_code=404 if "no encontrado" in result.mensaje.lower() else 400,
                content=result.dict()
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_nit endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "codigo": NITErrorCodes.ERROR_INTERNO,
                "mensaje": "Error interno del servidor",
                "detalles": {"error": str(e)}
            }
        )

@router.get("/validate/{nit}", response_model=NITValidationResponse)
async def validate_nit_get(
    nit: str = Path(..., description="NIT a validar"),
    pais: Optional[str] = Query(None, description="País para filtrar búsqueda"),
    db: Session = Depends(get_db)
):
    """
    Validar un NIT usando método GET (para facilidad de uso)
    
    - **nit**: NIT a validar
    - **pais**: País para filtrar búsqueda (parámetro de consulta opcional)
    """
    try:
        # Crear request object
        request = NITValidationRequest(nit=nit, pais=pais)
        
        # Reutilizar la lógica del endpoint POST
        result = await nit_service.validate_nit(
            db=db, 
            nit=request.nit, 
            pais=request.pais
        )
        
        if not result.valid:
            return JSONResponse(
                status_code=404 if "no encontrado" in result.mensaje.lower() else 400,
                content=result.dict()
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_nit_get endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "codigo": NITErrorCodes.ERROR_INTERNO,
                "mensaje": "Error interno del servidor",
                "detalles": {"error": str(e)}
            }
        )

@router.get("/institution/{nit}", response_model=InstitucionResponse)
async def get_institution_details(
    nit: str = Path(..., description="NIT de la institución"),
    db: Session = Depends(get_db)
):
    """
    Obtener detalles completos de una institución por NIT
    
    - **nit**: NIT de la institución
    """
    try:
        institucion = await nit_service.get_institution_details(db, nit)
        
        if not institucion:
            raise HTTPException(
                status_code=404,
                detail={
                    "codigo": NITErrorCodes.NO_ENCONTRADO,
                    "mensaje": f"Institución con NIT {nit} no encontrada"
                }
            )
        
        return InstitucionResponse.model_validate(institucion)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institution details: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "codigo": NITErrorCodes.ERROR_INTERNO,
                "mensaje": "Error interno del servidor",
                "detalles": {"error": str(e)}
            }
        )

@router.delete("/cache/{nit}")
async def clear_nit_cache(
    nit: str = Path(..., description="NIT para limpiar del caché"),
    pais: Optional[str] = Query(None, description="País específico a limpiar del caché")
):
    """
    Limpiar caché para un NIT específico
    
    - **nit**: NIT a limpiar del caché
    - **pais**: País específico (opcional)
    """
    try:
        result = nit_service.clear_cache_for_nit(nit, pais)
        
        return {
            "success": result,
            "message": f"Caché limpiado para NIT {nit}" if result else "No se pudo limpiar el caché",
            "nit": nit,
            "pais": pais
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "codigo": NITErrorCodes.CACHE_ERROR,
                "mensaje": "Error limpiando caché",
                "detalles": {"error": str(e)}
            }
        )

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Obtener estadísticas del caché Redis
    """
    try:
        stats = nit_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "codigo": NITErrorCodes.CACHE_ERROR,
                "mensaje": "Error obteniendo estadísticas del caché",
                "detalles": {"error": str(e)}
            }
        )

@router.post("/institution", response_model=InstitucionResponse, status_code=201)
async def create_institution(
    institucion: InstitucionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva institución asociada con NIT válido

    - **nit**: NIT de la institución (8-20 caracteres)
    - **nombre_institucion**: Nombre de la institución
    - **pais**: País de la institución
    - **activo**: Estado activo de la institución (por defecto True)
    """
    try:
        from app.models.institucion import InstitucionAsociada
        from datetime import datetime

        # Verificar si el NIT ya existe
        existing = db.query(InstitucionAsociada).filter(
            InstitucionAsociada.nit == institucion.nit
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "codigo": "NIT_YA_EXISTE",
                    "mensaje": f"El NIT {institucion.nit} ya está registrado",
                    "detalles": {"nit": institucion.nit}
                }
            )

        # Crear nueva institución
        nueva_institucion = InstitucionAsociada(
            nit=institucion.nit,
            nombre_institucion=institucion.nombre_institucion,
            pais=institucion.pais,
            fecha_registro=datetime.now(),
            activo=institucion.activo
        )

        db.add(nueva_institucion)
        db.commit()
        db.refresh(nueva_institucion)

        # Limpiar caché si existe
        nit_service.clear_cache_for_nit(institucion.nit, institucion.pais)

        logger.info(f"Nueva institución creada: NIT {institucion.nit}")

        return InstitucionResponse.model_validate(nueva_institucion)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating institution: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "codigo": NITErrorCodes.ERROR_INTERNO,
                "mensaje": "Error interno del servidor",
                "detalles": {"error": str(e)}
            }
        )