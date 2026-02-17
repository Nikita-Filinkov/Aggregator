from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.sync.scheduler import start_scheduler, shutdown_scheduler
from app.health.router import router as router_health
from app.sync.router import router as router_sync
from app.aggregator.events.router import router as event_router
from app.aggregator.tickets.router import router as router_tickets
from app.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔥 Приложение запускается...")
    start_scheduler()
    print("✅ Приложение запустилось")
    yield
    shutdown_scheduler()
    logger.info("🛑 Приложение останавливается...")


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
