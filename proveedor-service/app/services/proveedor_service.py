import logging
import json
from typing import Optional, Tuple, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import httpx
import redis.asyncio as redis

from fastapi import HTTPException
from app.models.proveedor import (
    Proveedor, ProveedorCreate, ProveedorResponse,
    ErrorDetail, ProveedorExistsResponse, ProveedorListResponse
)

logger = logging.getLogger(__name__)

class ProveedorService:
    def __init__(self, db: Session):
        self.db = db
        self.nit_service_url = "http://nit-validation-service:8002/api/v1"
        self.timeout = 5.0
        self._http_client = None
        # Inicializar Redis
        self.redis = redis.from_url("redis://redis-cache:6379", decode_responses=True)
    
    async def get_http_client(self):
        """Obtener cliente HTTP reutilizable"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client
        
    async def create_proveedor(
        self, 
        proveedor_data: ProveedorCreate,
        idempotency_key: str
    ) -> Tuple[Optional[ProveedorResponse], Optional[ErrorDetail]]:
        """Crear un nuevo proveedor con validaciones e idempotency"""
        try:
            # Verificar idempotency: si la key existe, retornar respuesta previa
            cached_response = await self.redis.get(f"idempotency:{idempotency_key}")
            if cached_response:
                logger.info(f"Idempotency hit for key: {idempotency_key}")
                if cached_response.startswith('{"error":'):
                    return None, ErrorDetail.model_validate_json(cached_response)
                else:
                    return ProveedorResponse.model_validate_json(cached_response), None

            # 1. Verificar NIT único
            proveedor_existente = self.db.query(Proveedor).filter(Proveedor.nit == proveedor_data.nit).first()
            if proveedor_existente:
                error = ErrorDetail(
                    error="NIT duplicado",
                    detalles={"nit": f"El NIT {proveedor_data.nit} ya existe en el sistema"}
                )
                # Cachear la respuesta de error
                await self.redis.setex(f"idempotency:{idempotency_key}", 3600, error.model_dump_json())
                return None, error

            # 2. Crear instancia de Proveedor
            nuevo_proveedor = Proveedor(
                razon_social=proveedor_data.razon_social,
                nit=proveedor_data.nit,
                tipo_proveedor=proveedor_data.tipo_proveedor,
                email=proveedor_data.email,
                telefono=proveedor_data.telefono,
                direccion=proveedor_data.direccion,
                ciudad=proveedor_data.ciudad,
                pais=proveedor_data.pais,
                certificaciones=proveedor_data.certificaciones or [],
                estado=proveedor_data.estado,
                calificacion=proveedor_data.calificacion,
                tiempo_entrega_promedio=proveedor_data.tiempo_entrega_promedio,
                version=0
            )

            # 3. Guardar en BD
            self.db.add(nuevo_proveedor)
            self.db.commit()
            self.db.refresh(nuevo_proveedor)

            success_response = ProveedorResponse.model_validate(nuevo_proveedor)
            # Cachear la respuesta exitosa
            await self.redis.setex(f"idempotency:{idempotency_key}", 3600, success_response.model_dump_json())

            logger.info(f"Proveedor creado exitosamente: {nuevo_proveedor.proveedor_id}")
            return success_response, None

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error de integridad al crear proveedor: {str(e)}")
            error = ErrorDetail(
                error="Error de integridad",
                detalles={"message": "Datos duplicados o inválidos"}
            )
            # Cachear la respuesta de error
            await self.redis.setex(f"idempotency:{idempotency_key}", 3600, error.model_dump_json())
            return None, error
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error inesperado al crear proveedor: {str(e)}")
            error = ErrorDetail(
                error="Error interno",
                detalles={"message": str(e)}
            )
            # Cachear la respuesta de error
            await self.redis.setex(f"idempotency:{idempotency_key}", 3600, error.model_dump_json())
            return None, error

    async def check_exists(self, nit: str) -> ProveedorExistsResponse:
        """
        Verificar si existe un proveedor por NIT en la base de datos.
        """
        try:
            # Verificar existencia en BD
            proveedor = self.db.query(Proveedor).filter(Proveedor.nit == nit).first()
            return ProveedorExistsResponse(exists=proveedor is not None)

        except Exception as e:
            logger.error(f"Error al verificar existencia de proveedor: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Error interno", "detalles": {"message": str(e)}}
            )

    async def list_proveedores(self) -> ProveedorListResponse:
        """Listar todos los proveedores"""
        try:
            proveedores = self.db.query(Proveedor).all()
            return ProveedorListResponse(
                skip=0,
                limit=len(proveedores),
                total=len(proveedores),
                data=[ProveedorResponse.model_validate(p) for p in proveedores]
            )
        except Exception as e:
            logger.error(f"Error al listar proveedores: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Error interno", "detalles": {"message": str(e)}}
            )

    async def close(self):
        """Cerrar conexiones"""
        if self._http_client:
            await self._http_client.aclose()
        await self.redis.close()