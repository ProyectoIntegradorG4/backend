from sqlalchemy.orm import Session
from app.models.audit import AuditLog, AuditLogCreate
from typing import Optional
import uuid

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    async def create_audit_log(self, audit_data: AuditLogCreate) -> AuditLog:
        """
        Crear un nuevo registro de auditoría.
        
        Args:
            audit_data: Datos del evento de auditoría
            
        Returns:
            El registro de auditoría creado
        """
        # Generar UUID único para el ID si no se proporciona
        unique_id = str(uuid.uuid4())
        
        db_audit_log = AuditLog(
            id=unique_id,
            event=audit_data.event,
            request=audit_data.request.model_dump(),  # Convertir Pydantic model a dict (v2)
            outcome=audit_data.outcome.value,
            action=audit_data.action.value,
            timestamp=audit_data.timestamp,
            auditid=audit_data.auditid
        )
        
        self.db.add(db_audit_log)
        self.db.commit()
        self.db.refresh(db_audit_log)
        return db_audit_log

    async def get_audit_log(self, audit_id: str) -> Optional[AuditLog]:
        """
        Obtener un registro de auditoría por ID.
        
        Args:
            audit_id: ID único del registro de auditoría
            
        Returns:
            El registro de auditoría o None si no se encuentra
        """
        return self.db.query(AuditLog).filter(AuditLog.id == audit_id).first()