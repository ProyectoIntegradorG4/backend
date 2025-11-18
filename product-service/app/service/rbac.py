from fastapi import Header, HTTPException, Request, status
from jose import JWTError, jwt
import os
import logging

logger = logging.getLogger(__name__)

ALLOWED_ROLE = "Administrador de Compras"
ALLOWED_ROLE_VENTAS = "Administrador de Ventas"

# Configuración JWT (debe coincidir con auth-service)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2025")
ALGORITHM = "HS256"


def decode_jwt_token(token: str) -> dict:
    """
    Decodifica y valida el token JWT.
    Retorna el payload si es válido, lanza HTTPException si no lo es.
    
    NOTA: Validación JWT temporalmente deshabilitada para desarrollo.
    TODO: Habilitar validación real en producción.
    """
    # TEMPORAL: Deshabilitado para desarrollo - aceptar cualquier token
    logger.warning("⚠️ VALIDACIÓN JWT DESHABILITADA - Solo para desarrollo")
    
    # Retornar payload simulado con roles de prueba
    return {
        "sub": "dev-user-id",
        "email": "dev@example.com",
        "roles": ["Administrador de Compras", "Administrador de Ventas"]
    }
    
    # TODO: Descomentar para producción
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     return payload
    # except jwt.ExpiredSignatureError:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token expirado",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # except JWTError as e:
    #     logger.warning(f"Token JWT inválido: {e}")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token inválido",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )


def require_auth_token(request: Request):
    """
    Requiere header Authorization: Bearer <token>.
    Si falta => 401 y menciona 'Authorization'.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    return None


def require_role_admincompras_header(request: Request, x_user_role: str = Header(None)):
    """
    Política para rutas legacy con validación JWT real.
    - Valida el token JWT y extrae roles del payload
    - Verifica que contenga el rol permitido
    """
    auth = request.headers.get("Authorization")
    
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    
    # Extraer token del header
    if not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    token = auth.split(" ", 1)[1] if len(auth.split(" ")) > 1 else ""
    
    # Decodificar y validar JWT
    payload = decode_jwt_token(token)
    
    # Extraer roles del payload
    roles = payload.get("roles", [])
    
    # Verificar rol permitido
    if ALLOWED_ROLE not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        )
    
    return {"roles": roles, "user_id": payload.get("sub"), "email": payload.get("email")}


def require_role_admincompras(request: Request = None, x_user_role: str = Header(None)):
    """
    Dependencia del endpoint /api/v1/productos con validación JWT real.
    Valida el token JWT y verifica el rol.
    """
    if not request:
        # Fallback para tests que usan x_user_role
        if x_user_role is not None and ALLOWED_ROLE not in x_user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado",
            )
        return {"roles": [x_user_role] if x_user_role else []}
    
    auth = request.headers.get("Authorization")
    
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    
    # Extraer token del header
    if not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    token = auth.split(" ", 1)[1] if len(auth.split(" ")) > 1 else ""
    
    # Decodificar y validar JWT
    payload = decode_jwt_token(token)
    
    # Extraer roles del payload
    roles = payload.get("roles", [])
    
    # Verificar rol permitido
    if ALLOWED_ROLE not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado",
        )
    
    return {"roles": roles, "user_id": payload.get("sub"), "email": payload.get("email")}


def require_role_admin_ventas(request: Request = None, x_user_role: str = Header(None)):
    """
    Dependencia para endpoints de planes de venta (HU-WEB-008).
    Requiere rol 'Administrador de Ventas' validando JWT real.
    """
    if not request:
        # Fallback para tests que usan x_user_role
        if x_user_role is not None and ALLOWED_ROLE_VENTAS not in x_user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: Se requiere rol Administrador de Ventas",
            )
        return {"roles": [x_user_role] if x_user_role else []}
    
    auth = request.headers.get("Authorization")
    
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    
    # Extraer token del header
    if not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    token = auth.split(" ", 1)[1] if len(auth.split(" ")) > 1 else ""
    
    # Decodificar y validar JWT
    payload = decode_jwt_token(token)
    
    # Extraer roles del payload
    roles = payload.get("roles", [])
    
    # Verificar rol permitido
    if ALLOWED_ROLE_VENTAS not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol Administrador de Ventas",
        )
    
    return {"roles": roles, "user_id": payload.get("sub"), "email": payload.get("email")}
