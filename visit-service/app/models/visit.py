# app/models/visit.py
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class ClientVisit(Base):
    __tablename__ = "clients_visits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_mgr_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    visit_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    evidences: Mapped[list["VisitEvidence"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan"
    )

class VisitEvidence(Base):
    __tablename__ = "clients_visits_evidence"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("clients_visits.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    visit: Mapped[ClientVisit] = relationship(back_populates="evidences")
