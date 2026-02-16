from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.dependencies import get_sync_repo
from app.sync.tasks import run_sync_task


router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger", status_code=200)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_db),
):
    """Запуск синхронизации в фоне"""
    sync_repo = await get_sync_repo(session)
    locked, last_date = await sync_repo.acquire_lock()
    if not locked:
        return {"status": "Синхронизация в процессе"}
    background_tasks.add_task(run_sync_task)
    return {"status": "Синхронизация запущена"}
