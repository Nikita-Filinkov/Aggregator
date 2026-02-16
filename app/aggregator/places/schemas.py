from uuid import UUID
from typing import List

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    """Площадка внутри события (только основные поля)"""

    id: UUID
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class PlaceDetailOut(PlaceOut):
    """Площадка со схемой мест"""

    seats_pattern: str


class SeatsResponse(BaseModel):
    """Доступные места по событию"""

    event_id: UUID
    available_seats: List[str]
