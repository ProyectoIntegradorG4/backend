from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.user_service import UserService
from app.models.user import UserRegister, RegisterSuccessResponse, ErrorDetail
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register")
async def register_user(user: UserRegister, db: Session = Depends(get_db)):
    """
    User Management Orquestador - POST /register (externo)
    """
    try:
        user_service = UserService(db)
        
        # Procesar registro
        result = await user_service.create_user(user)
        
        # result es una tupla (success_response, error_response)
        success_response, error_response = result
        
        if success_response:
            return success_response.model_dump()
        
        # Si hay error, manejar según el tipo
        if error_response:
            if error_response.error == "Datos inválidos":
                raise HTTPException(status_code=400, detail=error_response.model_dump())
            elif error_response.error == "NIT no autorizado":
                raise HTTPException(status_code=404, detail=error_response.model_dump())
            elif error_response.error == "Usuario ya existe":
                raise HTTPException(status_code=409, detail=error_response.model_dump())
            elif error_response.error == "Reglas de negocio fallidas":
                raise HTTPException(status_code=422, detail=error_response.model_dump())
            else:
                raise HTTPException(status_code=500, detail=error_response.model_dump())
        
        # Fallback si algo salió mal
        raise HTTPException(
            status_code=500, 
            detail={"error": "Error interno", "detalles": {"message": "Respuesta inesperada del servicio"}}
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error no manejado en register_user: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        error_detail = {
            "error": "Error interno",
            "traceId": "error-" + str(hash(str(e)))[:8],
            "detalles": {"message": str(e)}
        }
        raise HTTPException(status_code=500, detail=error_detail)