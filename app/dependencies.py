from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.aggregator.events.repository import EventRepository
from app.aggregator.places.repository import PlaceRepository
from app.aggregator.tickets.repository import TicketRepository
from app.config import settings
from app.database import get_async_db
from app.provider.client import EventsProviderClient
from app.sync.repository import SyncMetadataRepository


def get_provider_client():
    """Фабрика для создания клиента Events Provider API"""
    client = EventsProviderClient(
        api_key=settings.LMS_API_KEY, base_url=settings.BASE_URL
    )
    return client


async def get_place_repo(
    session: AsyncSession = Depends(get_async_db),
) -> PlaceRepository:
    return PlaceRepository(session)


async def get_event_repo(
    session: AsyncSession = Depends(get_async_db),
) -> EventRepository:
    return EventRepository(session)


async def get_sync_repo(
    session: AsyncSession = Depends(get_async_db),
) -> SyncMetadataRepository:
    return SyncMetadataRepository(session)


async def get_ticket_repo(
    session: AsyncSession = Depends(get_async_db),
) -> TicketRepository:
    return TicketRepository(session)
