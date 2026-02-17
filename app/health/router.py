from typing import Dict, Any

from fastapi import APIRouter, Depends
from app.dependencies import get_provider_client

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("")
async def health_check(client=Depends(get_provider_client)) -> Dict[str, Any]:
    async with client:
        return await client.check_availability()
