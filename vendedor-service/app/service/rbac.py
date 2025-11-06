# app/security/rbac.py
from fastapi import Header, HTTPException, Request, status
from typing import Optional, Dict, Any, List
import os

# Opcional: soportar JWT si hay SECRET_KEY
USE_JWT = True
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

try:
    from jose import jwt, JWTError  # python-jose[cryptography]
except Exception:
    USE_JWT = False
    jwt = None
    JWTError = Exception

ALLOWED_ROLE = "Administrador de Compras"  

def _get_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()

def _decode_jwt(token: str) -> Dict[str, Any]:
    if not (USE_JWT and SECRET_KEY):
        return {}
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

def require_auth_token(request: Request):
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    return None

def require_role_admincompras_header(request: Request, x_user_role: str = Header(None)):
    auth = request.headers.get("Authorization")
    if not auth and not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    # Preferimos JWT si está disponible
    if auth:
        token = _get_bearer_token(request)
        claims = _decode_jwt(token) if token else {}
        rol = (claims.get("rol") or x_user_role or "").lower()
        if "administrador de compras" not in rol:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        return {"roles": [rol]}
    # Sin Authorization -> usamos encabezado
    if (not x_user_role) or (ALLOWED_ROLE not in x_user_role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return {"roles": [x_user_role]}

def require_role_admincompras(x_user_role: str = Header(None)):
    if x_user_role is not None and ALLOWED_ROLE not in x_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado",
        )
    return {"roles": [x_user_role] if x_user_role else []}

def require_roles(allowed_roles: List[str]):
    allowed_norm = [r.lower() for r in allowed_roles]

    def _dep(request: Request, x_user_role: Optional[str] = Header(None)) -> Dict[str, Any]:
        token = _get_bearer_token(request)
        if not token and not x_user_role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header required")

        rol_claim = ""
        if token:
            claims = _decode_jwt(token)
            rol_claim = (claims.get("rol") or "").lower()

        header_rol = (x_user_role or "").lower()
        effective_role = rol_claim or header_rol

        if not effective_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

        # match por igualdad exacta case-insensitive
        if effective_role not in allowed_norm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

        return {"roles": [effective_role], "claims": (claims if token else {}), "token": token}

    return _dep
