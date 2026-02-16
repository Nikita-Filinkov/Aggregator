import asyncio
from datetime import datetime
from typing import Optional
from app.provider.client import EventsProviderClient
from app.provider.paginator import EventsPaginator
from app.aggregator.events.repository import EventRepository
from app.aggregator.places.repository import PlaceRepository
from app.sync.repository import SyncMetadataRepository
from app.aggregator.events.models import Event
from app.aggregator.places.models import Place


class SyncEventsUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        place_repo: PlaceRepository,
        event_repo: EventRepository,
        sync_repo: SyncMetadataRepository,
    ):
        self.client = client
        self.place_repo = place_repo
        self.event_repo = event_repo
        self.sync_repo = sync_repo

    async def execute(self, forced_changed_at: Optional[str] = None) -> None:
        """Запуск синхронизации. Если forced_changed_at не передан, берём из БД"""

        try:
            meta = await self.sync_repo.get()
            if forced_changed_at:
                changed_at = forced_changed_at
            else:
                if meta and meta.last_changed_at:
                    changed_at = meta.last_changed_at.date().isoformat()
                else:
                    changed_at = "2000-01-01"

            max_changed_at = None

            async with self.client:
                async for event_data in EventsPaginator(
                    self.client, changed_at=changed_at
                ):
                    event_changed = datetime.fromisoformat(event_data["changed_at"])

                    if meta and meta.last_changed_at:
                        if event_changed <= meta.last_changed_at:
                            continue

                    await self._process_event(event_data)

                    if max_changed_at is None or event_changed > max_changed_at:
                        max_changed_at = event_changed

            await self.place_repo.session.commit()
            # Лог - # Лог - Синхронизация выполнена
            print("📤 Вызов release_lock с success=True")
            await self.sync_repo.release_lock(
                success=True, last_changed_at=max_changed_at
            )
            print("✅ release_lock выполнен")
            # Лог - Синхронизация уже выполняется
        except Exception as e:
            # logger.exception("Ошибка во время синхронизации")
            await self.sync_repo.release_lock(success=False)
            raise

    async def _process_event(self, event_data: dict) -> None:
        """Сохранение площадки и события"""

        print(f"🔥 _process_event: {event_data.get('id')}")
        await asyncio.sleep(0.5)
        place_data = event_data["place"]
        place = await self.place_repo.get(place_data["id"])
        if not place:
            place = Place(
                id=place_data["id"],
                name=place_data["name"],
                city=place_data["city"],
                address=place_data["address"],
                seats_pattern=place_data["seats_pattern"],
                changed_at=datetime.fromisoformat(place_data["changed_at"]),
                created_at=datetime.fromisoformat(place_data["created_at"]),
            )
        else:
            place.name = place_data["name"]
            place.city = place_data["city"]
            place.address = place_data["address"]
            place.seats_pattern = place_data["seats_pattern"]
            place.changed_at = datetime.fromisoformat(place_data["changed_at"])
        await self.place_repo.save(place)

        event = await self.event_repo.get(event_data["id"])
        if not event:
            event = Event(
                id=event_data["id"],
                name=event_data["name"],
                place_id=place_data["id"],
                event_time=datetime.fromisoformat(event_data["event_time"]),
                registration_deadline=datetime.fromisoformat(
                    event_data["registration_deadline"]
                ),
                status=event_data["status"],
                number_of_visitors=event_data["number_of_visitors"],
                changed_at=datetime.fromisoformat(event_data["changed_at"]),
                created_at=datetime.fromisoformat(event_data["created_at"]),
                status_changed_at=datetime.fromisoformat(
                    event_data["status_changed_at"]
                )
                if event_data.get("status_changed_at")
                else None,
            )
        else:
            event.name = event_data["name"]
            event.place_id = place_data["id"]
            event.event_time = datetime.fromisoformat(event_data["event_time"])
            event.registration_deadline = datetime.fromisoformat(
                event_data["registration_deadline"]
            )
            event.status = event_data["status"]
            event.number_of_visitors = event_data["number_of_visitors"]
            event.changed_at = datetime.fromisoformat(event_data["changed_at"])
            event.status_changed_at = (
                datetime.fromisoformat(event_data["status_changed_at"])
                if event_data.get("status_changed_at")
                else None
            )
        await self.event_repo.save(event)
