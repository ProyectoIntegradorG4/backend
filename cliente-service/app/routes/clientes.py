from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.cliente_service import ClienteService
from app.models.cliente import (
    ClienteListResponse, ClienteResponse, TiposInstitucionResponse
)
from typing import Optional
import logging

logger = logging.getLogger("uvicorn")

router = APIRouter()


@router.get("/tipos-institucion", response_model=TiposInstitucionResponse)
async def get_tipos_institucion(
    db: Session = Depends(get_db)
):
    """
    Obtener lista de tipos de institución disponibles para filtros.
    
    Retorna lista de tipos de institución válidos:
    - Hospital
    - Clínica
    - IPS
    - EPS
    - Laboratorio Clínico
    - Centro de Salud
    
    **No requiere autenticación** (modo desarrollo)
    """
    try:
        cliente_service = ClienteService(db)
        tipos = cliente_service.get_tipos_institucion()
        
        logger.info(f"✅ Tipos de institución retornados")
        return tipos
        
    except Exception as e:
        logger.error(f"Error en get_tipos_institucion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener tipos de institución"
        )


@router.get("/mis-clientes", response_model=ClienteListResponse)
async def get_mis_clientes(
    gerente_id: Optional[int] = Query(None, description="ID del gerente (para pruebas)"),
    pais: Optional[str] = Query(None, description="Filtrar por país (Colombia, Peru, Mexico, Ecuador)"),
    tipo_institucion: Optional[str] = Query(None, description="Filtrar por tipo de institución"),
    search: Optional[str] = Query(None, description="Buscar por nombre o ubicación"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Elementos por página"),
    activo: bool = Query(True, description="Filtrar solo clientes activos"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de clientes con filtros opcionales.
    
    - **gerente_id**: ID del gerente para filtrar por asignaciones (opcional, para pruebas)
    - **pais**: Filtrar por país (Colombia, Peru, Mexico, Ecuador) - Opcional
    - **tipo_institucion**: Filtro opcional por tipo (Hospital, Clínica, IPS, etc.)
    - **search**: Búsqueda por nombre comercial, razón social, ciudad o dirección
    - **page**: Número de página (default: 1)
    - **limit**: Elementos por página (default: 50, max: 100)
    - **activo**: Solo clientes activos (default: true)
    
    **No requiere autenticación** (modo desarrollo)
    
    Si se especifica gerente_id, retorna solo los clientes asignados a ese gerente.
    Si no, retorna todos los clientes (con filtros opcionales de país).
    """
    try:
        cliente_service = ClienteService(db)
        
        # Si se especifica gerente_id, usar asignaciones
        if gerente_id:
            # Obtener país del gerente
            gerente_pais = cliente_service.get_gerente_pais(gerente_id)
            
            if not gerente_pais:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se pudo determinar el país del gerente {gerente_id}"
                )
            
            # Obtener clientes asignados al gerente
            result = cliente_service.get_clientes_asignados_a_gerente(
                gerente_id=gerente_id,
                gerente_pais=gerente_pais,
                tipo_institucion=tipo_institucion,
                search=search,
                page=page,
                limit=limit,
                activo=activo
            )
            
            logger.info(f"✅ Retornando {len(result.clientes)} clientes asignados al gerente {gerente_id}")
        else:
            # Obtener todos los clientes con filtros simples
            result = cliente_service.get_clientes_simple(
                pais=pais,
                tipo_institucion=tipo_institucion,
                search=search,
                page=page,
                limit=limit,
                activo=activo
            )
            
            logger.info(f"✅ Retornando {len(result.clientes)} clientes de {result.total} total")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en get_mis_clientes: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener lista de clientes"
        )


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente_detail(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener detalle completo de un cliente específico.
    
    - **cliente_id**: ID del cliente a consultar
    
    **No requiere autenticación** (modo desarrollo)
    
    Retorna 404 si el cliente no existe.
    """
    try:
        cliente_service = ClienteService(db)
        
        # Obtener detalle del cliente
        cliente = cliente_service.get_cliente_detail_simple(cliente_id=cliente_id)
        
        logger.info(f"✅ Detalle de cliente {cliente_id} retornado")
        return cliente
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en get_cliente_detail: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener detalle del cliente"
        )



