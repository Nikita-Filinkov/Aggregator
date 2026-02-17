import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.aggregator.events.models import Event


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
