from fastapi import APIRouter, BackgroundTasks, Depends
from app.sync.deps import get_sync_usecase
from app.usecases.sync_events import SyncEventsUsecase

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger", status_code=200)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    sync_usecase: SyncEventsUsecase = Depends(get_sync_usecase),
):
    """Запуск синхронизации в фоне"""
    background_tasks.add_task(sync_usecase.execute)
    return {"status": "sync_started"}
