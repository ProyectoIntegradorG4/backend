from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from app.models.user import User, UserRegister, RegisterSuccessResponse, ErrorDetail
from app.services.audit_client import AuditClient
import re
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Tuple, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_client = AuditClient()
        self.nit_service_url = "http://nit-validation-service:8002"
        self.jwt_secret = "your-secret-key"  # En producción usar variable de entorno
        self.jwt_algorithm = "HS256"

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def validate_password_complexity(self, password: str) -> bool:
        """
        Valida que la contraseña cumpla con la política de complejidad:
        - Al menos 8 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        - Al menos un carácter especial
        """
        if len(password) < 8:
            return False
        
        if not re.search(r"[A-Z]", password):
            return False
        
        if not re.search(r"[a-z]", password):
            return False
        
        if not re.search(r"\d", password):
            return False
        
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            return False
        
        return True

    async def validate_nit_exists(self, nit: int) -> Tuple[bool, Optional[int]]:
        """
        Valida que el NIT exista en InstitucionesAsociadas.
        Returns: (existe, institucion_id)
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.nit_service_url}/api/v1/validate/{nit}")
                
                if response.status_code == 200:
                    data = response.json()
                    # Si el NIT es válido y está activo
                    if data.get("valid", False) and data.get("activo", False):
                        # En este caso usamos un ID fijo ya que no tenemos tabla de instituciones en user_db
                        # En producción, esto sería un ID real de institución
                        return True, 1
                    else:
                        return False, None
                elif response.status_code == 404:
                    return False, None
                else:
                    logger.error(f"Error validando NIT: {response.status_code}")
                    return False, None
        except Exception as e:
            logger.error(f"Error conectando con nit-validation-service: {str(e)}")
            return False, None

    def generate_jwt_token(self, user_id: int, email: str) -> str:
        """Genera un token JWT para el usuario."""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def create_user(self, user: UserRegister) -> Tuple[RegisterSuccessResponse, Optional[ErrorDetail]]:
        """
        Crear un usuario con validaciones completas y auditoría.
        
        Returns:
            Tuple[RegisterSuccessResponse, ErrorDetail]: Respuesta exitosa o error
        """
        user_data = {
            "nombre": user.nombre,
            "email": user.email,
            "nit": user.nit
        }
        
        try:
            # 1. Validar complejidad de contraseña
            if not self.validate_password_complexity(user.password):
                error = ErrorDetail(
                    error="Reglas de negocio fallidas",
                    detalles={"password": "No cumple política de complejidad"}
                )
                await self.audit_client.log_user_register_error(
                    user_data, "password_policy", "Contraseña no cumple política", "other"
                )
                return None, error

            # 2. Validar que el NIT existe en InstitucionesAsociadas
            nit_exists, institucion_id = await self.validate_nit_exists(user.nit)
            if not nit_exists:
                error = ErrorDetail(
                    error="NIT no autorizado",
                    detalles={"nit": f"{user.nit} no existe en InstitucionesAsociadas"}
                )
                await self.audit_client.log_user_register_error(
                    user_data, "nit_not_found", f"NIT {user.nit} no autorizado", "nit"
                )
                return None, error

            # 3. Verificar si el correo electrónico ya existe
            existing_user = self.db.query(User).filter(User.correo_electronico == user.email).first()
            if existing_user:
                error = ErrorDetail(
                    error="Usuario ya existe",
                    detalles={"email": user.email}
                )
                await self.audit_client.log_user_register_error(
                    user_data, "user_exists", f"Email {user.email} ya registrado", "email"
                )
                return None, error

            # 4. Crear el usuario
            password_hash = self.get_password_hash(user.password)
            db_user = User(
                nombre=user.nombre,
                correo_electronico=user.email,
                password_hash=password_hash,
                nit=user.nit
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            # 5. Generar token JWT
            token = self.generate_jwt_token(db_user.id, db_user.correo_electronico)

            # 6. Registrar éxito en auditoría
            await self.audit_client.log_user_register_success(
                user_data, db_user.id, institucion_id or 0
            )

            # 7. Crear respuesta exitosa
            success_response = RegisterSuccessResponse(
                userId=db_user.id,
                institucionId=institucion_id or 0,
                token=token
            )

            return success_response, None

        except IntegrityError as e:
            self.db.rollback()
            error = ErrorDetail(
                error="Usuario ya existe",
                detalles={"email": user.email}
            )
            await self.audit_client.log_user_register_error(
                user_data, "integrity_error", "Error de integridad en BD", "email"
            )
            return None, error

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error interno creando usuario: {str(e)}")
            error = ErrorDetail.create_with_trace(
                error="Error interno",
                detalles={"message": "Error interno del servidor"}
            )
            await self.audit_client.log_user_register_error(
                user_data, "internal_error", str(e), "other"
            )
            return None, error