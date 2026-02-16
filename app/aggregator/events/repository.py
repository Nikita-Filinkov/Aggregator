from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.aggregator.events.models import Event


class EventRepository:
    """Репозиторий для работы с таблицей Event"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, event_id: str) -> Optional[Event]:
        """Получение одного события по его event_id"""
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def get_with_place(self, event_id: str) -> Optional[Event]:
        """Получение события с подгрузкой связанной площадки"""
        result = await self.session.execute(
            select(Event).where(Event.id == event_id).options(selectinload(Event.place))
        )
        return result.scalar_one_or_none()

    async def save(self, event: Event) -> None:
        """Сохранение события в БД"""
        self.session.add(event)
        await self.session.flush()

    async def events_list(
        self,
        date_from: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """Возвращает список событий с пагинацией и общее количество events"""
        query = (
            select(Event).options(selectinload(Event.place)).order_by(Event.event_time)
        )

        count_query = select(func.count()).select_from(Event)

        if date_from:
            query = query.where(Event.event_time >= date_from)
            count_query = count_query.where(Event.event_time >= date_from)

        total = await self.session.scalar(count_query)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        events = result.scalars().all()
        return events, total
