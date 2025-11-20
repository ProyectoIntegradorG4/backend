# app/services/rbac.py
from typing import List, Optional

from fastapi import Header, HTTPException, Request, status

ALLOWED_ROLE = "gerente_cuenta"


class CurrentUser:
    def __init__(self, user_id: int, roles: List[str], token: str):
        self.user_id = user_id
        self.roles = roles or []
        self.token = token


def _build_current_user(
    request: Request,
    x_user_id: Optional[str],
    x_user_role: Optional[str],
) -> CurrentUser:
    
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header required",
        )

    if not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Role header required",
        )

    # Intentar convertir el user id a int
    try:
        user_id_int = int(x_user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id must be numeric",
        )

    # Validar rol permitido
    if ALLOWED_ROLE and ALLOWED_ROLE not in x_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado (rol requerido)",
        )

    # Extraer el token (sin validarlo)
    token = auth.split(" ", 1)[1]

    return CurrentUser(
        user_id=user_id_int,
        roles=[x_user_role],
        token=token,
    )


def require_auth_token(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> CurrentUser:
    
    return _build_current_user(request, x_user_id, x_user_role)


def require_role_admincompras_header(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> CurrentUser:
    
    return _build_current_user(request, x_user_id, x_user_role)


def require_role_admincompras(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> CurrentUser:
    """
    Versión para endpoints que solo necesitan verificar el rol,
    pero igual validamos token + user_id.
    """
    return _build_current_user(request, x_user_id, x_user_role)
