from fastapi import Header, HTTPException, Request, status

ALLOWED_ROLE = "Administrador de Compras"


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
    Política para rutas legacy:
    - Sin Authorization y sin X-User-Role => 401
    - Con Authorization pero sin rol correcto => 403 'No autorizado'
    - Con X-User-Role que contenga el rol permitido => OK
    """
    auth = request.headers.get("Authorization")
    if not auth and not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    if (not x_user_role) or (ALLOWED_ROLE not in x_user_role):
        # si hay token pero el rol no está o no es válido => 403
        if auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado",
            )
    return {"roles": [x_user_role] if x_user_role else []}


def require_role_admincompras(x_user_role: str = Header(None)):
    """
    Dependencia del endpoint /api/v1/productos (los tests la sobre-escriben).
    Si explícitamente nos pasan un rol diferente => 403 'Acceso denegado'.
    """
    if x_user_role is not None and ALLOWED_ROLE not in x_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado",
        )
    return {"roles": [x_user_role] if x_user_role else []}
