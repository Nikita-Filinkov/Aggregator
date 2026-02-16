from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.aggregator.places.models import Place


class PlaceRepository:
    """Репозиторий для работы с таблицей Place"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, place_id: str) -> Optional[Place]:
        """Получение места проведения по его place_id"""
        result = await self.session.execute(select(Place).where(Place.id == place_id))
        return result.scalar_one_or_none()

    async def save(self, place: Place) -> None:
        """Сохранение места проведения в БД"""
        self.session.add(place)
        await self.session.flush()
