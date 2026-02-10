from typing import Dict

from fastapi import APIRouter
from aiohttp import ClientSession, ClientTimeout, ClientConnectorError

from app.config import settings

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    timeout = ClientTimeout(total=10, connect=5)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.get(settings.HEALTH_URL) as response:
                status = response.status
                if status == 200:
                    return {"status": "ok"}
                return {"status": "fault"}
        except (ClientConnectorError, ClientTimeout):
            return {"status": "fault"}
