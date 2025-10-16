from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.models.user import LoginRequest, LoginResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de login con JWT
    Recibe email y password, retorna token JWT y datos del usuario
    """
    try:
        auth_service = AuthService(db)
        
        # Procesar login
        login_response = await auth_service.login(login_request)
        
        if not login_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return login_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error no manejado en login: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/verify-token")
async def verify_token(token: str, db: Session = Depends(get_db)):
    """
    Endpoint para verificar si un token JWT es válido
    """
    try:
        auth_service = AuthService(db)
        
        # Verificar token
        token_data = auth_service.verify_token(token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        
        return {
            "valid": True,
            "user_id": token_data.user_id,
            "email": token_data.email,
            "roles": token_data.roles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
