from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.aggregator.places.schemas import PlaceDetailOut, PlaceOut


class EventOut(BaseModel):
    """Событие для списка"""

    id: UUID
    name: str
    place: PlaceOut
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class EventDetailOut(EventOut):
    """Событие с расширенной информацией о месте"""

    place: PlaceDetailOut


class EventListResponse(BaseModel):
    """Ответ со списком событий и пагинацией"""

    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[EventOut]


class EventListParams(BaseModel):
    date_from: Optional[date] = Field(None, description="События после указанной даты")
    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(20, ge=1, le=100, description="Размер страницы")
