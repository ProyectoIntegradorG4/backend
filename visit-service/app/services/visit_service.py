# app/services/visit_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.visit import ClientVisit, VisitEvidence

class VisitService:
    def __init__(self, db: Session):
        self.db = db

    def create_visit(
        self,
        *,
        client_id: int,
        account_mgr_id: int,
        visit_dt: datetime,
        title: str | None,
        notes: str | None
    ) -> ClientVisit:
        visit = ClientVisit(
            client_id=client_id,
            account_mgr_id=account_mgr_id,
            visit_datetime=visit_dt,
            title=title,
            notes=notes,
        )
        self.db.add(visit)
        self.db.flush()  # obtiene ID sin cerrar transacción
        return visit

    def add_evidence(
        self,
        *,
        visit_id: int,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_key: str
    ) -> VisitEvidence:
        ev = VisitEvidence(
            visit_id=visit_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
        )
        self.db.add(ev)
        return ev

    def list_by_client(self, client_id: int, limit: int = 50, offset: int = 0):
        q = (
            self.db.query(ClientVisit)
            .filter(ClientVisit.client_id == client_id)
            .order_by(ClientVisit.visit_datetime.desc())
        )
        total = q.count()
        items = q.limit(limit).offset(offset).all()
        return items, total

    def get(self, visit_id: int):
        return self.db.query(ClientVisit).filter(ClientVisit.id == visit_id).first()
