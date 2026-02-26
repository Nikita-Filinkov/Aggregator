import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from aiohttp import ClientConnectorError

from app.aggregator.events.repository import EventRepository
from app.aggregator.exceptions import (
    EventNotFoundException,
    EventNotPublished,
    EventPassed,
    FailedSyncEvent,
    ProviderNetworkError,
    ProviderUnexpectedResponse,
    TicketNotFoundException,
    TicketRegistrationError,
    TicketUnRegistrationError,
)
from app.aggregator.tickets.idempotency.exeptions import (
    DontConsistentData,
    IdemDontHaveTicket,
)
from app.aggregator.tickets.idempotency.repository import IdempotencyRepository
from app.aggregator.tickets.models import Ticket
from app.aggregator.tickets.outbox.repository import OutboxRepository
from app.aggregator.tickets.repository import TicketRepository
from app.logger import logger
from app.provider.client import EventsProviderClient
from app.provider.exceptions import EventsProviderError, ProviderTemporaryError
from app.sync.usecase import SyncEventsUsecase


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        sync_events: SyncEventsUsecase,
        event_repo: EventRepository,
        ticket_repo: TicketRepository,
        outbox_repo: OutboxRepository,
        idempotency_repo: IdempotencyRepository,
    ):
        self.client = client
        self.sync_events = sync_events
        self.event_repo = event_repo
        self.ticket_repo = ticket_repo
        self.outbox_repo = outbox_repo
        self.idempotency_repo = idempotency_repo

    async def execute(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
        idempotency_key: Optional[str] = None,
    ) -> UUID:

        input_params = {
            "event_id": str(event_id),
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat,
        }

        if idempotency_key:
            existing = await self.idempotency_repo.get(idempotency_key)
            if existing:
                saved = existing.response_data

                if (
                    saved.get("event_id") != input_params["event_id"]
                    or saved.get("seat") != input_params["seat"]
                    or saved.get("email") != input_params["email"]
                    or saved.get("first_name") != input_params["first_name"]
                    or saved.get("last_name") != input_params["last_name"]
                ):
                    logger.warning(
                        "Ключ идемпотентности совпадает, но входные и сохранённые данные отличаются",
                        extra={
                            "idempotency_key": idempotency_key,
                            "input_params": input_params,
                            "saved_params": saved,
                        },
                    )
                    raise DontConsistentData

                ticket_id_str = saved.get("ticket_id")
                if not ticket_id_str:
                    logger.exception(
                        "Нет билета в таблице идемпотентности, хотя ключ идемпотентности есть",
                        extra={
                            "idempotency_key": idempotency_key,
                            "input_params": input_params,
                        },
                    )
                    raise IdemDontHaveTicket

                return UUID(ticket_id_str)

        try:
            await self.sync_events.execute()
        except (ProviderTemporaryError, EventsProviderError) as e:
            logger.exception(
                "Ошибка при попытке синхронизировать данные перед регистрацией",
                extra={"error": e},
            )
            raise FailedSyncEvent

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
            raise

        except Exception as e:
            logger.error("Внутренняя ошибка сервера", extra={"error": e})
            raise TicketRegistrationError(detail="Внутренняя ошибка сервера")

        try:
            response = await asyncio.to_thread(
                self.client.register,
                event_id=str(event_id),
                first_name=first_name,
                last_name=last_name,
                email=email,
                seat=seat,
            )
        except EventsProviderError:
            raise TicketUnRegistrationError(
                "Ошибка регистрации. Возможно, место уже занято."
            )
        except (ClientConnectorError, asyncio.TimeoutError):
            raise ProviderNetworkError()

        except Exception as e:
            logger.error("Внутренняя ошибка сервера", extra={"error": e})
            raise TicketRegistrationError(detail="Внутренняя ошибка сервера")

        ticket_id_str = response.get("ticket_id")
        if not ticket_id_str:
            raise TicketUnRegistrationError("Неверный ответ от провайдера")

        ticket_data = input_params.copy()
        ticket_data["ticket_id"] = ticket_id_str

        ticket_id: UUID = UUID(ticket_id_str)

        ticket = Ticket(
            ticket_id=ticket_id,
            event_id=event_id,
            seat=seat,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        await self.ticket_repo.save(ticket)

        outbox_payload = ticket_data

        await self.outbox_repo.create(
            event_type="ticket_created", payload=outbox_payload
        )

        if idempotency_key:
            await self.idempotency_repo.save(idempotency_key, ticket_data)

        await self.ticket_repo.session.commit()

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

        except EventsProviderError:
            raise TicketUnRegistrationError("Не удалось отменить регистрацию")

        except (ClientConnectorError, asyncio.TimeoutError):
            raise ProviderNetworkError()

        except Exception as e:
            logger.error("Внутренняя ошибка сервера", extra={"error": e})
            raise TicketRegistrationError(detail="Внутренняя ошибка сервера")

        await self.ticket_repo.delete_by_ticket_id(
            ticket_id=str(ticket_id), event_id=str(ticket.event_id)
        )
        await self.ticket_repo.session.commit()
