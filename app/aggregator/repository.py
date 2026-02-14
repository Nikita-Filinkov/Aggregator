from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.aggregator.models import Place, Event, Ticket


class PlaceRepository:
    """Репозиторий для работы с таблицей Place"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, place_id: str) -> Optional[Place]:
        result = await self.session.execute(select(Place).where(Place.id == place_id))
        return result.scalar_one_or_none()

    async def save(self, place: Place) -> None:
        self.session.add(place)
        await self.session.flush()


class EventRepository:
    """Репозиторий для работы с таблицей Event"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, event_id: str) -> Optional[Event]:
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def save(self, event: Event) -> None:
        self.session.add(event)
        await self.session.flush()


class TicketRepository:
    """Репозиторий для работы с таблицей Ticket"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, ticket_id: str) -> Optional[Ticket]:
        result = await self.session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def save(self, ticket: Ticket) -> None:
        self.session.add(ticket)
        await self.session.flush()
        await self.session.commit()

    async def remove(self, ticket_id: str, event_id: str) -> None:
        result = await self.session.execute(
            select(Ticket).where(
                Ticket.ticket_id == ticket_id, Ticket.event_id == event_id
            )
        )
        ticket = result.scalar_one_or_none()

        if ticket:
            await self.session.delete(ticket)
            await self.session.flush()
