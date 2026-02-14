from fastapi import FastAPI
from app.health.router import router as router_health
from app.sync.router import router as router_sync

app = FastAPI(prefix="/api")

app.include_router(router_health)
app.include_router(router_sync)
