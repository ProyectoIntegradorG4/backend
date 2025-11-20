from fastapi import Header, HTTPException, Request, status

ALLOWED_ROLE = "gerente_cuenta"

def require_auth_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    return None

def require_role_admincompras(x_user_role: str = Header(None)):
    if x_user_role is not None and ALLOWED_ROLE not in x_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado",
        )
    return {"roles": [x_user_role] if x_user_role else []}