from sqlalchemy.orm import Session
from app.models.audit import AuditLog, AuditLogCreate
from typing import Optional
import uuid


class AuditService:
    """Service for managing audit logs"""

    def __init__(self, db: Session):
        self.db = db

    async def create_audit_log(self, audit_data: AuditLogCreate) -> AuditLog:
        """
        Create a new audit log entry

        Args:
            audit_data: Audit log data to create

        Returns:
            Created audit log entry
        """
        db_audit_log = AuditLog(
            id=str(uuid.uuid4()),
            event=audit_data.event,
            request=audit_data.request.model_dump(),
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
        Get an audit log by ID

        Args:
            audit_id: ID of the audit log to retrieve

        Returns:
            Audit log if found, None otherwise
        """
        return self.db.query(AuditLog).filter(AuditLog.id == audit_id).first()
