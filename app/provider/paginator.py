from typing import Optional, Dict, Any

from app.provider.client import EventsProviderClient


class EventsPaginator:
    """Асинхронный итератор для обхода ВСЕХ событий через пагинацию"""

    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: Optional[str] = None,
    ):
        self.client = client
        self.changed_at = changed_at

        self._current_page_events: list = []
        self._current_index: int = 0
        self._next_url: Optional[str] = None
        self._first_page_loaded: bool = False

    def __aiter__(self):
        """Возвращаем сам итератор"""
        return self

    async def __anext__(self) -> Dict[str, Any]:
        """
        Возвращает следующее событие.
        Автоматически загружает следующую страницу, когда текущая закончилась.
        """
        if self._current_index >= len(self._current_page_events):
            await self._load_next_page()

            if not self._current_page_events:
                await self.client.close()
                raise StopAsyncIteration

        event = self._current_page_events[self._current_index]
        self._current_index += 1
        return event

    async def _load_next_page(self):
        """Загружает следующую страницу событий"""
        if not self._first_page_loaded:
            response = await self.client.get_events_page(changed_at=self.changed_at)
            self._first_page_loaded = True
        else:
            if self._next_url is None:
                self._current_page_events = []
                return
            response = await self.client.get_events_page(url=self._next_url)

        self._current_page_events = response.get("results", [])
        self._current_index = 0
        self._next_url = response.get("next")
