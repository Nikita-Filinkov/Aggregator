from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import get_async_db
from app.dependencies import (
    get_provider_client,
    get_place_repo,
    get_event_repo,
    get_sync_repo,
)
from app.sync.deps import get_sync_usecase
from app.logger import logger

scheduler = AsyncIOScheduler()


async def sync_job() -> None:
    """Фоновая задача синхронизации"""
    logger.info("Запуск фоновой задачи синхронизации")
    try:
        async for session in get_async_db():
            logger.debug("Сессия БД получена")
            sync_repo = await get_sync_repo(session)
            logger.debug("Попытка захвата блокировки")
            locked, last_date = await sync_repo.acquire_lock()
            logger.info(
                "Результат захвата блокировки",
                extra={
                    "locked": locked,
                    "last_date": str(last_date) if last_date else None,
                },
            )
            if not locked:
                logger.info("Синхронизация уже выполняется, выходим")
                return

            logger.info("Запуск usecase синхронизации")
            try:
                usecase = await get_sync_usecase(
                    client=get_provider_client(),
                    place_repo=await get_place_repo(session),
                    event_repo=await get_event_repo(session),
                    sync_repo=sync_repo,
                )
                await usecase.execute()
                logger.info("Синхронизация успешно завершена")
            except Exception as e:
                logger.exception(
                    "Ошибка при выполнении usecase", extra={"error": str(e)}
                )
                raise
    except Exception as e:
        logger.exception(
            "Критическая ошибка в фоновой задаче синхронизации", extra={"error": str(e)}
        )


def start_scheduler() -> None:
    """Старт планировщика"""
    logger.info("Запуск планировщика")
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(days=1),
        id="daily_sync",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    jobs = scheduler.get_jobs()
    logger.info("Планировщик запущен", extra={"jobs_count": len(jobs)})


def shutdown_scheduler() -> None:
    """Остановка планировщика"""
    scheduler.shutdown()
    logger.info("Планировщик остановлен")
