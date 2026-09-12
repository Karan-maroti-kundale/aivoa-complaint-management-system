from datetime import datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(30), default="Copilot")
    customer_name: Mapped[str | None] = mapped_column(String(200))
    complaint_source: Mapped[str | None] = mapped_column(String(100))
    facility: Mapped[str | None] = mapped_column(String(200))
    material_impact: Mapped[str | None] = mapped_column(String(200))
    product_name: Mapped[str | None] = mapped_column(String(200))
    product_strength: Mapped[str | None] = mapped_column(String(100))
    batch_number: Mapped[str | None] = mapped_column(String(100))
    affected_quantity: Mapped[str | None] = mapped_column(String(100))
    manufacturing_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    complaint_type: Mapped[str | None] = mapped_column(String(120))
    complaint_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(30))
    priority: Mapped[str | None] = mapped_column(String(30))
    risk_assessment: Mapped[str | None] = mapped_column(Text)
    suggested_next_action: Mapped[str | None] = mapped_column(Text)
    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="Draft")
    committed: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_input: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditEvent(Base):
    __tablename__ = "complaint_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_number: Mapped[str] = mapped_column(String(40), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    actor_type: Mapped[str] = mapped_column(String(30), default="system")
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
