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

scheduler = AsyncIOScheduler()


# async def sync_job() -> None:
#     """Фоновая задача синхронизации"""
#
#     async for session in get_async_db():
#         sync_repo = await get_sync_repo(session)
#
#         locked, last_date = await sync_repo.acquire_lock()
#         if not locked:
#             return
#
#         try:
#             usecase = await get_sync_usecase(
#                 client=get_provider_client(),
#                 place_repo=await get_place_repo(session),
#                 event_repo=await get_event_repo(session),
#                 sync_repo=sync_repo,
#             )
#             await usecase.execute()
#         except Exception as e:
#             raise
async def sync_job() -> None:
    """Фоновая задача синхронизации"""
    print("⏰⏰⏰ SYNC_JOB НАЧАЛА ⏰⏰⏰")
    try:
        async for session in get_async_db():
            print("📦 Сессия получена")
            sync_repo = await get_sync_repo(session)
            print("🔒 Пытаемся захватить блокировку...")
            locked, last_date = await sync_repo.acquire_lock()
            print(f"🔒 Результат блокировки: locked={locked}, last_date={last_date}")
            if not locked:
                print("⏳ Синхронизация уже выполняется, выходим")
                return

            print("🚀 Запускаем usecase...")
            try:
                usecase = await get_sync_usecase(
                    client=get_provider_client(),
                    place_repo=await get_place_repo(session),
                    event_repo=await get_event_repo(session),
                    sync_repo=sync_repo,
                )
                await usecase.execute()
                print("✅ Синхронизация завершена")
            except Exception as e:
                print(f"❌ Ошибка в usecase: {e}")
                raise
    except Exception as e:
        print(f"❌❌❌ КРИТИЧЕСКАЯ ОШИБКА В JOB: {e}")
        import traceback

        traceback.print_exc()


def start_scheduler() -> None:
    """Старт планировщика"""
    print("🚀 ЗАПУСК ПЛАНИРОВЩИКА!")
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(days=1),
        # trigger=IntervalTrigger(seconds=60),
        id="daily_sync",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    print(f"✅ Планировщик запущен. Jobs: {scheduler.get_jobs()}")
    # logger.info("Планировщик фоновой синхронизации запущен")


def shutdown_scheduler() -> None:
    """Остановка планировщика"""
    scheduler.shutdown()
    # logger.info("Планировщик остановлен")
