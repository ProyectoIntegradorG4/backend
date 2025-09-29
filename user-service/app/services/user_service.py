import asyncio
import hashlib
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt
import httpx
import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRegister, RegisterSuccessResponse, ErrorDetail
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = "your-secret-key-here"  # En producción, usar variable de entorno
        self.algorithm = "HS256"
        self.nit_service_url = "http://nit-validation-service:8002"
        self.audit_service_url = "http://audit-service:8003"
        self.timeout = 5.0
        
        # Cliente HTTP reutilizable con configuración optimizada
        self._http_client = None
        
        # Cliente Redis para cache
        self._redis_client = None
    
    async def get_http_client(self):
        if self._http_client is None:
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
                keepalive_expiry=30
            )
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=limits,
                http2=False  # Deshabilitar HTTP/2 temporalmente
            )
        return self._http_client
    
    async def get_redis_client(self):
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    "redis://redis-cache:6379",
                    decode_responses=True,
                    max_connections=20
                )
            except Exception as e:
                logger.warning(f"Redis no disponible, funcionando sin cache: {e}")
                self._redis_client = None
        return self._redis_client

    def validate_password_complexity(self, password: str) -> bool:
        """Validación optimizada de complejidad de contraseña"""
        if len(password) < 8:
            return False
        
        # Usar una sola expresión regular para todas las validaciones
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$'
        return bool(re.match(pattern, password))

    def get_password_hash(self, password: str) -> str:
        """Hashing optimizado de contraseña"""
        # Usar rounds más bajos para mejor rendimiento (10 en lugar de 12)
        salt = bcrypt.gensalt(rounds=10)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    async def validate_nit_exists(self, nit: str) -> Tuple[bool, Optional[int]]:
        """Validación de NIT con cache Redis"""
        redis_client = await self.get_redis_client()
        
        # Verificar cache primero
        if redis_client:
            try:
                cache_key = f"nit_validation:{nit}"
                cached_result = await redis_client.get(cache_key)
                
                if cached_result:
                    result = json.loads(cached_result)
                    logger.info(f"Cache hit para NIT {nit}")
                    return result["exists"], result.get("institucion_id")
            except Exception as e:
                logger.warning(f"Error accediendo cache Redis: {e}")
        
        # Si no está en cache, hacer request HTTP
        try:
            http_client = await self.get_http_client()
            response = await http_client.get(f"{self.nit_service_url}/api/v1/validate/{nit}")
            
            if response.status_code == 200:
                data = response.json()
                institucion_id = data.get("id", 1)
                
                # Guardar en cache por 1 hora si Redis está disponible
                if redis_client:
                    try:
                        cache_data = {"exists": True, "institucion_id": institucion_id}
                        await redis_client.setex(cache_key, 3600, json.dumps(cache_data))
                    except Exception as e:
                        logger.warning(f"Error guardando en cache: {e}")
                
                return True, institucion_id
            else:
                # Guardar resultado negativo en cache por 5 minutos
                if redis_client:
                    try:
                        cache_data = {"exists": False, "institucion_id": None}
                        await redis_client.setex(cache_key, 300, json.dumps(cache_data))
                    except Exception as e:
                        logger.warning(f"Error guardando en cache: {e}")
                
                return False, None
                
        except Exception as e:
            logger.error(f"Error validando NIT: {e}")
            return False, None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Generación optimizada de tokens JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def log_audit_async(self, event_data: dict, outcome: str, action: str, error_msg: str = None):
        """Log de auditoría asíncrono no bloqueante"""
        try:
            http_client = await self.get_http_client()
            
            audit_data = {
                "event": "user_register",
                "request": event_data,
                "outcome": outcome,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auditid": f"user-{hashlib.md5(str(event_data).encode()).hexdigest()}"
            }
            
            # Fire and forget - no esperamos respuesta
            asyncio.create_task(
                self._send_audit_log(audit_data)
            )
            
        except Exception as e:
            logger.warning(f"Error preparando audit log: {e}")
            # No fallar si la auditoría falla

    async def _send_audit_log(self, audit_data: dict):
        """Envío interno de log de auditoría"""
        try:
            http_client = await self.get_http_client()
            await http_client.post(
                f"{self.audit_service_url}/audit/register",
                json=audit_data,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.warning(f"Error enviando audit log: {e}")

    async def create_user(self, user: UserRegister) -> Tuple[Optional[RegisterSuccessResponse], Optional[ErrorDetail]]:
        """Creación optimizada de usuarios con validaciones paralelas"""
        user_data = {
            "nombre": user.nombre,
            "email": user.email,
            "nit": user.nit
        }

        # 1. Validar complejidad de contraseña (rápido, local)
        if not self.validate_password_complexity(user.password):
            await self.log_audit_async(user_data, "fail", "other", "Password complexity failed")
            return None, ErrorDetail(
                error="Reglas de negocio fallidas",
                detalles={"password": "No cumple política de complejidad"}
            )

        # 2. Ejecutar validaciones de NIT y email en paralelo
        validation_tasks = [
            self.validate_nit_exists(user.nit),
            asyncio.to_thread(self._check_email_exists, user.email)
        ]
        
        try:
            (nit_exists, institucion_id), email_exists = await asyncio.gather(*validation_tasks)
        except Exception as e:
            await self.log_audit_async(user_data, "fail", "other", f"Validation error: {str(e)}")
            return None, ErrorDetail(
                error="Error interno",
                detalles={"message": "Error en validaciones"}
            )

        # 3. Verificar resultados de validaciones
        if not nit_exists:
            await self.log_audit_async(user_data, "fail", "nit", f"NIT {user.nit} not found")
            return None, ErrorDetail(
                error="NIT no autorizado",
                detalles={"nit": f"{user.nit} no existe en InstitucionesAsociadas"}
            )

        if email_exists:
            await self.log_audit_async(user_data, "fail", "email", f"Email {user.email} already exists")
            return None, ErrorDetail(
                error="Usuario ya existe",
                detalles={"email": user.email}
            )

        # 4. Crear usuario con hash de contraseña en thread separado
        password_hash = await asyncio.to_thread(self.get_password_hash, user.password)
        
        db_user = User(
            nombre=user.nombre,
            correo_electronico=user.email,
            password_hash=password_hash,
            nit=user.nit
        )

        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
        except IntegrityError:
            self.db.rollback()
            await self.log_audit_async(user_data, "fail", "email", "Database integrity error")
            return None, ErrorDetail(
                error="Usuario ya existe",
                detalles={"email": user.email}
            )
        except Exception as e:
            self.db.rollback()
            await self.log_audit_async(user_data, "fail", "other", f"Database error: {str(e)}")
            return None, ErrorDetail(
                error="Error interno",
                detalles={"message": "Error al crear usuario"}
            )

        # 5. Generar token JWT
        access_token = self.create_access_token(
            data={"sub": str(db_user.id), "email": db_user.correo_electronico}
        )

        # 6. Log de éxito (asíncrono)
        await self.log_audit_async(user_data, "success", "email", None)

        # 7. Respuesta exitosa
        return RegisterSuccessResponse(
            userId=db_user.id,
            institucionId=institucion_id or 1,
            token=access_token,
            rol=db_user.rol
        ), None

    def _check_email_exists(self, email: str) -> bool:
        """Verificación sincrónica de email duplicado"""
        existing_user = self.db.query(User).filter(User.correo_electronico == email).first()
        return existing_user is not None

    async def close(self):
        """Cerrar conexiones"""
        if self._http_client:
            await self._http_client.aclose()
        if self._redis_client:
            await self._redis_client.close()