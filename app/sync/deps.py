from fastapi import Depends

from app.aggregator.events.repository import EventRepository
from app.aggregator.places.repository import PlaceRepository
from app.dependencies import (
    get_event_repo,
    get_place_repo,
    get_provider_client,
    get_sync_repo,
)
from app.provider.client import EventsProviderClient
from app.sync.repository import SyncMetadataRepository
from app.sync.usecase import SyncEventsUsecase


async def get_sync_usecase(
    client: EventsProviderClient = Depends(get_provider_client),
    place_repo: PlaceRepository = Depends(get_place_repo),
    event_repo: EventRepository = Depends(get_event_repo),
    sync_repo: SyncMetadataRepository = Depends(get_sync_repo),
) -> SyncEventsUsecase:
    return SyncEventsUsecase(client, place_repo, event_repo, sync_repo)
