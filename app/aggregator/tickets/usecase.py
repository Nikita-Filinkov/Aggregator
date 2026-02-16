import asyncio
from datetime import datetime, timezone
from uuid import UUID
from aiohttp import ClientConnectorError

from app.aggregator.events.repository import EventRepository
from app.aggregator.tickets.repository import TicketRepository
from app.aggregator.tickets.models import Ticket
from app.provider.client import EventsProviderClient
from app.aggregator.exceptions import (
    EventNotFoundException,
    EventNotPublished,
    EventPassed,
    TicketNotFoundException,
    TicketUnRegistrationError,
    ProviderNetworkError,
    ProviderUnexpectedResponse,
)
from fastapi import HTTPException, status

from app.provider.exceptions import EventsProviderError


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        event_repo: EventRepository,
        ticket_repo: TicketRepository,
    ):
        self.client = client
        self.event_repo = event_repo
        self.ticket_repo = ticket_repo

    async def execute(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> UUID:

        event = await self.event_repo.get(str(event_id))
        if not event:
            raise EventNotFoundException

        if event.status != "published":
            raise EventNotPublished

        if event.registration_deadline and event.registration_deadline < datetime.now(
            timezone.utc
        ):
            raise EventPassed

        try:
            available = await self.client.get_event_seats(str(event_id))
            if seat not in available:
                raise TicketUnRegistrationError(f"Место {seat} недоступно")
        except TicketUnRegistrationError:
            # Лог - не удалось получить список мест
            raise
        except Exception as e:
            # logger.exception("Неожиданная ошибка при проверке мест")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
        try:
            response = await asyncio.to_thread(
                self.client.register,
                event_id=str(event_id),
                first_name=first_name,
                last_name=last_name,
                email=email,
                seat=seat,
            )
        except EventsProviderError as e:
            # logger.error(f"Ошибка провайдера при регистрации: {e.status} {e.message}")
            raise TicketUnRegistrationError(
                "Ошибка регистрации. Возможно, место уже занято."
            )
        except (ClientConnectorError, asyncio.TimeoutError) as e:
            # logger.error(f"Сетевая ошибка при регистрации: {e}")
            raise ProviderNetworkError()
        except Exception as e:
            # logger.exception("Неожиданная ошибка при регистрации")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
        ticket_id_str = response.get("ticket_id")
        if not ticket_id_str:
            raise TicketUnRegistrationError("Неверный ответ от провайдера")
            # Лог - не верный ответ от провайдера
        ticket_id = UUID(ticket_id_str)

        ticket = Ticket(
            ticket_id=ticket_id,
            event_id=event_id,
            seat=seat,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        await self.ticket_repo.save(ticket)

        return ticket_id


class CancelTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        ticket_repo: TicketRepository,
        event_repo: EventRepository,
    ):
        self.client = client
        self.ticket_repo = ticket_repo
        self.event_repo = event_repo

    async def execute(self, ticket_id: UUID) -> None:

        ticket = await self.ticket_repo.get(str(ticket_id))

        if not ticket:
            raise TicketNotFoundException

        event = await self.event_repo.get(str(ticket.event_id))

        if not event:
            raise EventNotFoundException

        if event.registration_deadline and event.registration_deadline < datetime.now(
            timezone.utc
        ):
            raise EventPassed

        try:
            response = await self.client.unregister(
                event_id=str(ticket.event_id), ticket_id=str(ticket_id)
            )
            if not response.get("success"):
                raise ProviderUnexpectedResponse()
        except EventsProviderError as e:
            # logger.error(f"Ошибка провайдера при отмене: {e.status} {e.message}")
            raise TicketUnRegistrationError("Не удалось отменить регистрацию")
        except (ClientConnectorError, asyncio.TimeoutError) as e:
            # logger.error(f"Сетевая ошибка при отмене: {e}")
            raise ProviderNetworkError()
        except Exception as e:
            # logger.exception("Неожиданная ошибка при отмене")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        await self.ticket_repo.delete_by_ticket_id(
            ticket_id=str(ticket_id), event_id=str(ticket.event_id)
        )
        await self.ticket_repo.session.commit()
