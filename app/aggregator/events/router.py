from uuid import UUID

from fastapi import APIRouter, Depends

from app.aggregator.events.dependencies import get_url_builder
from app.aggregator.events.seats_service import get_available_seats
from app.aggregator.events.schemas import (
    EventListResponse,
    EventListParams,
    EventDetailOut,
)
from app.aggregator.events.repository import EventRepository
from app.aggregator.exceptions import EventNotFoundException, EventNotPublished
from app.aggregator.places.schemas import SeatsResponse
from app.dependencies import get_event_repo, get_provider_client
from app.provider.client import EventsProviderClient

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventListResponse)
async def list_events(
    params: EventListParams = Depends(),
    event_repo: EventRepository = Depends(get_event_repo),
    build_url=Depends(get_url_builder),
):
    """Получить список событий с пагинацией и фильтрацией по дате"""

    events, total = await event_repo.events_list(
        date_from=params.date_from,
        page=params.page,
        page_size=params.page_size,
    )

    next_url = (
        build_url(
            page=params.page + 1,
            page_size=params.page_size,
            date_from=params.date_from,
        )
        if params.page * params.page_size < total
        else None
    )

    prev_url = (
        build_url(
            page=params.page - 1,
            page_size=params.page_size,
            date_from=params.date_from,
        )
        if params.page > 1
        else None
    )

    return EventListResponse(
        count=total,
        next=next_url,
        previous=prev_url,
        results=events,
    )


@router.get("/{event_id}", response_model=EventDetailOut)
async def get_event_details(
    event_id: UUID,
    event_repo: EventRepository = Depends(get_event_repo),
):
    """Получить детальную информацию о конкретном событии"""
    event = await event_repo.get_with_place(str(event_id))
    if not event:
        raise EventNotFoundException
    return event


@router.get("/{event_id}/seats", response_model=SeatsResponse)
async def get_event_seats(
    event_id: UUID,
    event_repo: EventRepository = Depends(get_event_repo),
    client: EventsProviderClient = Depends(get_provider_client),
):
    """Получить список свободных мест для события (с кэшированием на 30 секунд)"""
    event = await event_repo.get(str(event_id))

    if not event:
        raise EventNotFoundException

    if event.status != "published":
        raise EventNotPublished

    seats = await get_available_seats(str(event_id), client)
    return SeatsResponse(event_id=event_id, available_seats=seats)
