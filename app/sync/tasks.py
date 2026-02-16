from app.database import get_async_db
from app.sync.usecase import SyncEventsUsecase
from app.dependencies import (
    get_provider_client,
    get_place_repo,
    get_event_repo,
    get_sync_repo,
)


async def run_sync_task():
    """Фоновая задача: выполняет синхронизацию, используя свою сессию."""
    async for session in get_async_db():
        client = get_provider_client()
        place_repo = await get_place_repo(session)
        event_repo = await get_event_repo(session)
        sync_repo = await get_sync_repo(session)

        usecase = SyncEventsUsecase(client, place_repo, event_repo, sync_repo)
        await usecase.execute()
