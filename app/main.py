import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.aggregator.events.router import router as event_router
from app.aggregator.tickets.outbox.worker import OutboxWorker
from app.aggregator.tickets.router import router as router_tickets
from app.config import settings
from app.health.router import router as router_health
from app.logger import logger
from app.notifications.capashino_client import CapashinoClient
from app.sync.router import router as router_sync
from app.sync.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔥 Приложение запускается...")
    start_scheduler()
    capashino_client = CapashinoClient(
        api_key=settings.LMS_API_KEY, base_url=settings.CAPASHINO_BASE_URL
    )

    worker = OutboxWorker(
        capashino_client=capashino_client,
        poll_interval=10,
    )
    task = asyncio.create_task(worker.start())

    yield
    shutdown_scheduler()
    logger.info("🛑 Приложение останавливается...")
    await worker.stop()
    task.cancel()
    await capashino_client.close()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


app.include_router(router_health, prefix="/api")
app.include_router(router_sync, prefix="/api")
app.include_router(event_router, prefix="/api")
app.include_router(router_tickets, prefix="/api")
