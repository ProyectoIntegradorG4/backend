from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.orm import Session
from typing import List
import logging
from time import time
from app.models.proveedor import (
    ProveedorCreate, ProveedorResponse, 
    ProveedorExistsResponse, ProveedorListResponse
)

from app.database.connection import get_db
from app.services.proveedor_service import ProveedorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")

@router.get("/exists", response_model=ProveedorExistsResponse)
async def verificar_existencia(
    nit: str = Query(..., description="NIT del proveedor a verificar"),
    db: Session = Depends(get_db)
):
    """
    Verificar si existe un proveedor por NIT y validar el NIT

    - **nit**: NIT del proveedor a verificar (requerido)
    """
    try:
        service = ProveedorService(db)
        return await service.check_exists(nit)
    
    except Exception as e:
        logger.error(f"Error en verificar_existencia: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno", "detalles": {"message": str(e)}}
        )

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProveedorResponse)
async def crear_proveedor(
    proveedor: ProveedorCreate,
    idempotency_key: str = Header(alias="X-Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo proveedor.
    
    El NIT debe ser único, si ya existe se retornará un error 409 Conflict.
    
    - **razon_social**: Razón social del proveedor (requerido)
    - **nit**: NIT único del proveedor (requerido, debe ser único)
    - **tipo_proveedor**: laboratorio, distribuidor o importador
    - **email**: Email único (requerido)
    - **telefono**: Teléfono de contacto
    - **direccion**: Dirección física
    - **ciudad**: Ciudad
    - **pais**: País (colombia, peru, ecuador, mexico)
    - **certificaciones**: Lista de certificaciones (opcional)
    - **estado**: activo, inactivo o suspendido
    - **calificacion**: Calificación 0-5 (opcional)
    - **tiempo_entrega_promedio**: Días promedio de entrega (opcional)
    """
    try:
        service = ProveedorService(db)
        success_response, error_response = await service.create_proveedor(proveedor, idempotency_key)
        
        if success_response:
            return success_response
        
        if error_response:
            if error_response.error == "NIT duplicado":
                raise HTTPException(status_code=409, detail=error_response.model_dump())
            else:
                raise HTTPException(status_code=422, detail=error_response.model_dump())
        
        raise HTTPException(status_code=500, detail={"error": "Error interno"})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en crear_proveedor: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno", "detalles": {"message": str(e)}}
        )

@router.get("/", response_model=ProveedorListResponse)
async def listar_proveedores(
    db: Session = Depends(get_db)
):
    """
    Obtener lista de todos los proveedores
    """
    try:
        service = ProveedorService(db)
        return await service.list_proveedores()
    except Exception as e:
        logger.error(f"Error en listar_proveedores: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno", "detalles": {"message": str(e)}}
        )
