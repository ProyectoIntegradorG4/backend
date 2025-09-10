from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.audit import AuditLog, AuditLogCreate, ActionType
from typing import List, Optional, Dict, Any
from datetime import datetime

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    async def create_audit_log(self, audit_log: AuditLogCreate) -> AuditLog:
        db_audit_log = AuditLog(
            user_id=audit_log.user_id,
            service_name=audit_log.service_name,
            action_type=audit_log.action_type,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            details=audit_log.details,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            request_path=audit_log.request_path,
            http_method=audit_log.http_method,
            status_code=audit_log.status_code,
            response_time_ms=audit_log.response_time_ms
        )
        
        self.db.add(db_audit_log)
        self.db.commit()
        self.db.refresh(db_audit_log)
        return db_audit_log

    async def get_audit_log(self, audit_id: int) -> Optional[AuditLog]:
        return self.db.query(AuditLog).filter(AuditLog.id == audit_id).first()

    async def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        service_name: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        query = self.db.query(AuditLog)
        
        # Aplicar filtros
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if service_name:
            query = query.filter(AuditLog.service_name == service_name)
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    async def get_user_audit_logs(self, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    async def get_service_audit_logs(self, service_name: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.service_name == service_name
        ).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    async def get_audit_summary(self) -> Dict[str, Any]:
        # Total de logs
        total_logs = self.db.query(func.count(AuditLog.id)).scalar()
        
        # Logs por servicio
        logs_by_service = self.db.query(
            AuditLog.service_name,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.service_name).all()
        
        # Logs por acción
        logs_by_action = self.db.query(
            AuditLog.action_type,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action_type).all()
        
        # Logs por día (últimos 7 días)
        seven_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        logs_by_day = self.db.query(
            func.date(AuditLog.timestamp).label('date'),
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= seven_days_ago
        ).group_by(func.date(AuditLog.timestamp)).order_by('date').all()
        
        return {
            "total_logs": total_logs,
            "logs_by_service": [{"service": item[0], "count": item[1]} for item in logs_by_service],
            "logs_by_action": [{"action": item[0], "count": item[1]} for item in logs_by_action],
            "logs_by_day": [{"date": str(item[0]), "count": item[1]} for item in logs_by_day]
        }

    async def log_user_action(
        self, 
        user_id: int, 
        action: ActionType, 
        resource_type: str, 
        resource_id: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Método de conveniencia para registrar acciones de usuario"""
        audit_log = AuditLogCreate(
            user_id=user_id,
            service_name="user-service",
            action_type=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        return await self.create_audit_log(audit_log)