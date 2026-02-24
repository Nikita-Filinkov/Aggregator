from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TicketCreateRequest(BaseModel):
    event_id: UUID
    first_name: str = Field(..., min_length=3, max_length=100, examples=["Иван"])
    last_name: str = Field(..., min_length=3, max_length=100, examples=["Иванов"])
    email: EmailStr
    seat: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Схема мест в формате: секция{номер места}",
        examples=["A1-1000", "B1-2000", "C1-3000"],
    )
    idempotency_key: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Ключ идемпотентности для предотвращения не желательных повторов",
    )


class TicketCreateResponse(BaseModel):
    ticket_id: UUID


class TicketCancelResponse(BaseModel):
    success: bool
