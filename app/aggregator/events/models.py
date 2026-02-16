import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from app.aggregator.tickets.models import Ticket


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    place_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("places.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    number_of_visitors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    status_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    place: Mapped["Place"] = relationship(
        "Place", back_populates="events", lazy="selectin"
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Event({self.name}, {self.event_time})"
