from sqlalchemy.orm import Session
from app.models.audit import AuditLog, AuditLogCreate
from datetime import datetime, timezone
import uuid


class AuditService:
    """Servicio para gestionar eventos de auditoría"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_audit_log(self, audit_data: AuditLogCreate) -> dict:
        """
        Crear un registro de auditoría
        
        Args:
            audit_data: Datos del evento de auditoría
            
        Returns:
            dict con el resultado del registro
        """
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                event=audit_data.event,
                request=audit_data.request.model_dump() if hasattr(audit_data.request, 'model_dump') else audit_data.request,
                action=audit_data.action.value if hasattr(audit_data.action, 'value') else audit_data.action,
                outcome=audit_data.outcome.value if hasattr(audit_data.outcome, 'value') else audit_data.outcome,
                timestamp=audit_data.timestamp if audit_data.timestamp else datetime.now(timezone.utc),
                auditid=audit_data.auditid
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            return {"logged": True, "id": audit_log.id}
        except Exception as e:
            self.db.rollback()
            raise e

