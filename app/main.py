from fastapi import FastAPI
from app.health.health import router as router_health


app = FastAPI(prefix="/api")

app.include_router(router_health)
