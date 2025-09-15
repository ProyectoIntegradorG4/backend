from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from app.models.user import User, UserRegister, RegisterSuccessResponse, ErrorDetail
import jwt
from datetime import datetime, timedelta
from typing import Tuple, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.jwt_secret = "your-secret-key"
        self.jwt_algorithm = "HS256"

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def validate_password_complexity(self, password: str) -> bool:
        """Validación simplificada por ahora"""
        return len(password) >= 8

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
        Crear un usuario con validaciones básicas.
        """
        try:
            # 1. Validar complejidad de contraseña
            if not self.validate_password_complexity(user.password):
                error = ErrorDetail(
                    error="Reglas de negocio fallidas",
                    detalles={"password": "No cumple política de complejidad"}
                )
                return None, error

            # 2. Verificar si el correo electrónico ya existe
            existing_user = self.db.query(User).filter(User.correo_electronico == user.email).first()
            if existing_user:
                error = ErrorDetail(
                    error="Usuario ya existe",
                    detalles={"email": user.email}
                )
                return None, error

            # 3. Crear el usuario
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

            # 4. Generar token JWT
            token = self.generate_jwt_token(db_user.id, db_user.correo_electronico)

            # 5. Crear respuesta exitosa
            success_response = RegisterSuccessResponse(
                userId=db_user.id,
                institucionId=452,  # Hardcoded por ahora
                token=token
            )

            return success_response, None

        except IntegrityError as e:
            self.db.rollback()
            error = ErrorDetail(
                error="Usuario ya existe",
                detalles={"email": user.email}
            )
            return None, error

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error interno creando usuario: {str(e)}")
            error = ErrorDetail.create_with_trace(
                error="Error interno",
                detalles={"message": "Error interno del servidor"}
            )
            return None, error