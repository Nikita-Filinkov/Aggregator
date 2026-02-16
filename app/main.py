from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.sync.scheduler import start_scheduler, shutdown_scheduler
from app.health.router import router as router_health
from app.sync.router import router as router_sync
from app.aggregator.events.router import router as event_router
from app.aggregator.tickets.router import router as router_tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔥 Приложение запускается...")
    start_scheduler()
    print("✅ Приложение запустилось")
    yield
    shutdown_scheduler()
    print("🛑 Приложение останавливается...")


app = FastAPI(prefix="/api", lifespan=lifespan)

app.include_router(router_health)
app.include_router(router_sync)
app.include_router(event_router)
app.include_router(router_tickets)
