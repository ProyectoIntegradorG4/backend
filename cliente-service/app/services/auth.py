from fastapi import Header, HTTPException, Depends
from jose import JWTError, jwt
from typing import Dict, Optional
import os
import logging

logger = logging.getLogger("uvicorn")

# Configuración de JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
ALGORITHM = "HS256"


class TokenData:
    """Datos extraídos del token JWT"""
    def __init__(self, user_id: int, email: str, roles: list, nit: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        self.roles = roles
        self.nit = nit


async def get_current_user(authorization: str = Header(None)) -> Dict:
    """
    Extraer y validar el token JWT del header Authorization.
    
    Args:
        authorization: Header Authorization en formato "Bearer <token>"
        
    Returns:
        Dict con información del usuario (user_id, roles)
        
    Raises:
        HTTPException 401 si el token es inválido o no está presente
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token no proporcionado. Header Authorization requerido."
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Formato de token inválido. Use 'Bearer <token>'"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        roles = payload.get("roles", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Token inválido: falta user_id"
            )
        
        return {
            "user_id": int(user_id),
            "email": email,
            "roles": roles
        }
        
    except JWTError as e:
        logger.warning(f"Error al decodificar token JWT: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )
    except ValueError as e:
        logger.error(f"Error al convertir user_id a int: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Token inválido: user_id mal formado"
        )


async def require_gerente_cuenta(current_user: dict = Depends(get_current_user)) -> Dict:
    """
    Verificar que el usuario autenticado tiene el rol 'gerente_cuenta'.
    
    Args:
        current_user: Usuario actual obtenido del token
        
    Returns:
        Dict con información del usuario
        
    Raises:
        HTTPException 403 si el usuario no tiene el rol requerido
    """
    if "gerente_cuenta" not in current_user["roles"]:
        logger.warning(
            f"Usuario {current_user.get('user_id')} intentó acceder sin rol gerente_cuenta. "
            f"Roles: {current_user.get('roles')}"
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Se requiere rol 'gerente_cuenta'"
        )
    
    logger.info(f"✅ Acceso autorizado para gerente_cuenta: user_id={current_user['user_id']}")
    return current_user


async def get_optional_user(authorization: str = Header(None)) -> Optional[Dict]:
    """
    Extraer información del usuario del token si está presente.
    No lanza excepción si el token no está presente.
    
    Args:
        authorization: Header Authorization opcional
        
    Returns:
        Dict con información del usuario o None
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None

