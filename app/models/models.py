import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, default=1, nullable=False
    )

    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return f"SyncMetadata(last_sync={self.last_sync_at}, status={self.sync_status})"


class Place(Base):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    city: Mapped[str] = mapped_column(String(100), nullable=False)

    address: Mapped[str] = mapped_column(Text, nullable=False)

    seats_pattern: Mapped[str] = mapped_column(String(500), nullable=False)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="place", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Place({self.name}, {self.city})"


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


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    seat: Mapped[str] = mapped_column(String(10), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)

    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    event: Mapped["Event"] = relationship(
        "Event", back_populates="tickets", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Ticket({self.ticket_id}, seat={self.seat})"
