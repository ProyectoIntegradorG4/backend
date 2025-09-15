from sqlalchemy.orm import Session
from app.models.institucion import (
    InstitucionAsociada, 
    NITValidationResponse, 
    PaisEnum,
    NITError,
    NITErrorCodes
)
from app.database.connection import get_redis_client, REDIS_TTL
from typing import Optional, Tuple
import json
import re
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class NITValidationService:
    """Servicio para validación de NIT con caché Redis"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        
    def _generate_cache_key(self, nit: str, pais: Optional[str] = None) -> str:
        """Generar clave de caché para el NIT"""
        base_key = f"nit_validation:{nit.upper()}"
        if pais:
            base_key += f":{pais.upper()}"
        return base_key
    
    def _validate_nit_format(self, nit: str) -> Tuple[bool, Optional[str]]:
        """
        Validar formato básico del NIT
        Reglas básicas:
        - Solo números y guión
        - Longitud entre 8 y 20 caracteres
        - Formato básico: XXXXXXXXX-X (opcional el guión)
        """
        if not nit:
            return False, "NIT no puede estar vacío"
        
        # Remover espacios y convertir a mayúsculas
        nit_clean = nit.replace(" ", "").replace("-", "").upper()
        
        # Verificar longitud
        if len(nit_clean) < 8 or len(nit_clean) > 20:
            return False, "NIT debe tener entre 8 y 20 caracteres"
        
        # Verificar que solo contenga números (básico)
        if not nit_clean.isdigit():
            return False, "NIT debe contener solo números"
        
        return True, None
    
    def _get_from_cache(self, cache_key: str) -> Optional[dict]:
        """Obtener datos del caché Redis"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error reading from Redis cache: {e}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: dict, ttl: int = REDIS_TTL) -> None:
        """Almacenar datos en caché Redis"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(data, default=str)
            )
            logger.info(f"Cache set for key: {cache_key}")
        except Exception as e:
            logger.error(f"Error writing to Redis cache: {e}")
    
    def _query_database(self, db: Session, nit: str, pais: Optional[str]) -> Optional[InstitucionAsociada]:
        """Consultar la base de datos por NIT"""
        try:
            # Buscar por NIT exacto (conservando formato con guiones)
            query = db.query(InstitucionAsociada).filter(
                InstitucionAsociada.nit == nit
            )
            
            if pais:
                query = query.filter(InstitucionAsociada.pais == pais)
            
            return query.first()
        
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    def _create_response(self, institucion: Optional[InstitucionAsociada], mensaje: Optional[str] = None) -> NITValidationResponse:
        """Crear respuesta de validación"""
        if not institucion:
            return NITValidationResponse(
                valid=False,
                mensaje=mensaje or "NIT no encontrado en instituciones asociadas"
            )
        
        return NITValidationResponse(
            valid=True,
            nit=institucion.nit,
            nombre_institucion=institucion.nombre_institucion,
            pais=institucion.pais,
            fecha_registro=institucion.fecha_registro,
            activo=institucion.activo,
            mensaje="NIT válido encontrado"
        )
    
    async def validate_nit(self, db: Session, nit: str, pais: Optional[str] = None) -> NITValidationResponse:
        """
        Validar NIT contra la base de datos con caché Redis
        
        Args:
            db: Sesión de base de datos
            nit: NIT a validar
            pais: País opcional para filtrar búsqueda
            
        Returns:
            NITValidationResponse con resultado de validación
        """
        start_time = time.time()
        
        try:
            # 1. Validar formato del NIT
            is_valid_format, format_error = self._validate_nit_format(nit)
            if not is_valid_format:
                logger.warning(f"Invalid NIT format: {nit} - {format_error}")
                return NITValidationResponse(
                    valid=False,
                    mensaje=f"Formato de NIT inválido: {format_error}"
                )
            
            # Normalizar NIT para caché (sin guiones) pero conservar original para DB
            nit_normalized = nit.replace(" ", "").replace("-", "").upper()
            nit_original = nit.strip()
            
            # 2. Verificar caché Redis
            cache_key = self._generate_cache_key(nit_normalized, pais)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"NIT validation from cache completed in {processing_time:.2f}ms")
                return NITValidationResponse(**cached_result)
            
            # 3. Consultar base de datos con formato original
            logger.info(f"Cache miss, querying database for NIT: {nit_original}")
            institucion = self._query_database(db, nit_original, pais)
            
            # 4. Verificar estado de la institución
            mensaje = None
            if institucion and not institucion.activo:
                mensaje = f"Institución encontrada pero está inactiva"
            
            # 5. Crear respuesta
            response = self._create_response(institucion, mensaje)
            
            # 6. Almacenar en caché (tanto resultados positivos como negativos)
            cache_data = response.dict()
            cache_ttl = REDIS_TTL if response.valid else REDIS_TTL // 4  # TTL menor para resultados negativos
            self._set_cache(cache_key, cache_data, cache_ttl)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"NIT validation completed in {processing_time:.2f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"Error validating NIT {nit}: {e}")
            return NITValidationResponse(
                valid=False,
                mensaje="Error interno del servicio. Intente nuevamente."
            )
    
    async def get_institution_details(self, db: Session, nit: str) -> Optional[InstitucionAsociada]:
        """Obtener detalles completos de una institución por NIT"""
        try:
            return db.query(InstitucionAsociada).filter(
                InstitucionAsociada.nit == nit
            ).first()
        except Exception as e:
            logger.error(f"Error getting institution details: {e}")
            return None
    
    def clear_cache_for_nit(self, nit: str, pais: Optional[str] = None) -> bool:
        """Limpiar caché para un NIT específico"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(nit, pais)
            result = self.redis_client.delete(cache_key)
            logger.info(f"Cache cleared for NIT: {nit}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error clearing cache for NIT {nit}: {e}")
            return False
    
    def get_cache_stats(self) -> dict:
        """Obtener estadísticas del caché"""
        if not self.redis_client:
            return {"error": "Redis no disponible"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}