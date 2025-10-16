from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user import User, LoginRequest, LoginResponse, TokenData
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# Configuración de JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Manejar variable de entorno que puede estar vacía
jwt_expire_str = os.getenv("JWT_EXPIRE_MINUTES", "60")
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(jwt_expire_str) if jwt_expire_str else 60
except (ValueError, TypeError):
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña contra hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Crear token JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            email: str = payload.get("email")
            roles: list = payload.get("roles", [])
            
            if user_id is None or email is None:
                return None
                
            return TokenData(user_id=user_id, email=email, roles=roles)
        except JWTError:
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autenticar usuario con email y contraseña"""
        try:
            # Buscar usuario por email
            query = text("""
                SELECT id, nombre, correo_electronico, password_hash, nit, rol, activo
                FROM usuarios 
                WHERE correo_electronico = :email AND activo = true
            """)
            
            result = self.db.execute(query, {"email": email}).fetchone()
            
            if not result:
                logger.warning(f"Usuario no encontrado o inactivo: {email}")
                return None
            
            # Verificar contraseña
            if not self.verify_password(password, result.password_hash):
                logger.warning(f"Contraseña incorrecta para usuario: {email}")
                return None
            
            # Crear objeto User con los datos obtenidos
            user = User()
            user.id = result.id
            user.nombre = result.nombre
            user.correo_electronico = result.correo_electronico
            user.password_hash = result.password_hash
            user.nit = result.nit
            user.rol = result.rol
            user.activo = result.activo
            
            return user
            
        except Exception as e:
            logger.error(f"Error en autenticación: {str(e)}")
            return None

    async def login(self, login_request: LoginRequest) -> Optional[LoginResponse]:
        """Procesar login y generar token JWT"""
        try:
            # Autenticar usuario
            user = await self.authenticate_user(login_request.email, login_request.password)
            
            if not user:
                return None
            
            # Crear token JWT
            token_data = {
                "sub": str(user.id),
                "email": user.correo_electronico,
                "roles": [user.rol] if user.rol else []
            }
            
            access_token = self.create_access_token(data=token_data)
            
            # Crear respuesta
            response = LoginResponse(
                id=str(user.id),
                email=user.correo_electronico,
                fullName=user.nombre,
                isActive=user.activo,
                roles=[user.rol] if user.rol else [],
                token=access_token
            )
            
            logger.info(f"Login exitoso para usuario: {user.correo_electronico}")
            return response
            
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return None
