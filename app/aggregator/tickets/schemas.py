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


class TicketCreateResponse(BaseModel):
    ticket_id: UUID


class TicketCancelResponse(BaseModel):
    success: bool
