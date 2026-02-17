from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_provider_client, get_event_repo, get_ticket_repo
from app.provider.client import EventsProviderClient
from app.aggregator.events.repository import EventRepository
from app.aggregator.tickets.repository import TicketRepository
from app.aggregator.tickets.schemas import (
    TicketCreateRequest,
    TicketCreateResponse,
    TicketCancelResponse,
)
from app.aggregator.tickets.usecase import CreateTicketUsecase, CancelTicketUsecase

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketCreateResponse, status_code=201)
async def registration_on_event(
    params: TicketCreateRequest,
    client: EventsProviderClient = Depends(get_provider_client),
    event_repo: EventRepository = Depends(get_event_repo),
    ticket_repo: TicketRepository = Depends(get_ticket_repo),
):
    """Регистрация на событие и получение билета"""
    usecase = CreateTicketUsecase(client, event_repo, ticket_repo)
    ticket_id = await usecase.execute(
        event_id=params.event_id,
        first_name=params.first_name,
        last_name=params.last_name,
        email=params.email,
        seat=params.seat,
    )
    return TicketCreateResponse(ticket_id=ticket_id)


@router.delete("/{ticket_id}", response_model=TicketCancelResponse, status_code=200)
async def cancel_ticket(
    ticket_id: UUID,
    client: EventsProviderClient = Depends(get_provider_client),
    ticket_repo: TicketRepository = Depends(get_ticket_repo),
    event_repo: EventRepository = Depends(get_event_repo),
):
    """Отмена регистрации"""
    usecase = CancelTicketUsecase(client, ticket_repo, event_repo)
    await usecase.execute(ticket_id)
    return TicketCancelResponse(success=True)
