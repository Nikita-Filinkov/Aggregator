from uuid import UUID

from fastapi import APIRouter, Depends

from app.aggregator.events.repository import EventRepository
from app.aggregator.tickets.idempotency.repository import IdempotencyRepository
from app.aggregator.tickets.outbox.repository import OutboxRepository
from app.aggregator.tickets.repository import TicketRepository
from app.aggregator.tickets.schemas import (
    TicketCancelResponse,
    TicketCreateRequest,
    TicketCreateResponse,
)
from app.aggregator.tickets.usecase import CancelTicketUsecase, CreateTicketUsecase
from app.dependencies import (
    get_event_repo,
    get_idempotency_repo,
    get_outbox_repo,
    get_provider_client,
    get_ticket_repo,
)
from app.provider.client import EventsProviderClient
from app.sync.deps import get_sync_usecase
from app.sync.usecase import SyncEventsUsecase

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketCreateResponse, status_code=201)
async def registration_on_event(
    params: TicketCreateRequest,
    client: EventsProviderClient = Depends(get_provider_client),
    sync_events: SyncEventsUsecase = Depends(get_sync_usecase),
    event_repo: EventRepository = Depends(get_event_repo),
    ticket_repo: TicketRepository = Depends(get_ticket_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
    idempotency_repo: IdempotencyRepository = Depends(get_idempotency_repo),
):
    """Создание нового билета (регистрация на событие).

    - **idempotency_key** (опционально): ключ идемпотентности для защиты от дублирования запросов.
      Если ключ уже был использован с теми же данными, возвращается сохранённый ticket_id (201).
      Если ключ уже был использован, но данные отличаются, возвращается 409 Conflict."""
    usecase = CreateTicketUsecase(
        client, sync_events, event_repo, ticket_repo, outbox_repo, idempotency_repo
    )
    ticket_id = await usecase.execute(
        event_id=params.event_id,
        first_name=params.first_name,
        last_name=params.last_name,
        email=params.email,
        seat=params.seat,
        idempotency_key=params.idempotency_key,
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
