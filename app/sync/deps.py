from fastapi import Depends

from app.dependencies import (
    get_provider_client,
    get_place_repo,
    get_event_repo,
    get_sync_repo,
)
from app.provider.client import EventsProviderClient
from app.aggregator.repository import PlaceRepository, EventRepository
from app.sync.repository import SyncMetadataRepository

from app.usecases.sync_events import SyncEventsUsecase


async def get_sync_usecase(
    client: EventsProviderClient = Depends(get_provider_client),
    place_repo: PlaceRepository = Depends(get_place_repo),
    event_repo: EventRepository = Depends(get_event_repo),
    sync_repo: SyncMetadataRepository = Depends(get_sync_repo),
) -> SyncEventsUsecase:
    return SyncEventsUsecase(client, place_repo, event_repo, sync_repo)
