from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.audit import AuditLogCreate, AuditLogResponse
from app.services.audit_service import AuditService
from app.database.connection import get_db

router = APIRouter()

@router.post("/audit/register", response_model=AuditLogResponse, status_code=201)
async def register_audit_log(
    audit_data: AuditLogCreate,
    db: Session = Depends(get_db)
):
    """
    Registrar un evento de auditoría en el sistema.
    
    Args:
        audit_data: Datos del evento de auditoría
        db: Sesión de base de datos
    
    Returns:
        {"logged": true} si el registro fue exitoso
    """
    try:
        audit_service = AuditService(db)
        result = await audit_service.create_audit_log(audit_data)
        return AuditLogResponse(logged=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar evento de auditoría: {str(e)}")