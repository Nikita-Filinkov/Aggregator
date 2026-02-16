from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.aggregator.tickets.models import Ticket


class TicketRepository:
    """Репозиторий для работы с таблицей Ticket"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, ticket_id: str) -> Optional[Ticket]:
        """Получение билета по его ticket_id"""
        result = await self.session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def save(self, ticket: Ticket) -> None:
        """Сохранение ticket в БД"""
        self.session.add(ticket)
        await self.session.flush()
        await self.session.commit()

    async def delete_by_ticket_id(self, ticket_id: str, event_id: str) -> None:
        """Удаление билета по его ticket_id"""
        result = await self.session.execute(
            select(Ticket).where(
                Ticket.ticket_id == ticket_id, Ticket.event_id == event_id
            )
        )
        ticket = result.scalar_one_or_none()

        if ticket:
            await self.session.delete(ticket)
            await self.session.flush()
