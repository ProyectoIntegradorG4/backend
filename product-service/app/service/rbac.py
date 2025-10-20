from fastapi import Header, HTTPException, status

REQUIRED_ROLE = "Administrador de Compras"

def require_role_admincompras(x_user_role: str = Header(None, alias="X-User-Role")):
    """
    Verifica rol vía header X-User-Role.
    En producción, integrar con Auth Service/Keycloak/OPA.
    """
    if x_user_role != REQUIRED_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: se requiere rol Administrador de Compras"
        )
