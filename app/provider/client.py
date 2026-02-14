import asyncio
import requests

from aiohttp import ClientSession, ClientError, ClientTimeout, ClientConnectorError
from typing import Optional, Dict, Any, List

from app.exceptions import EventsProviderError


class EventsProviderClient:
    """Асинхронный HTTP-клиент для Events Provider API"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-api-key": api_key}
        self._session: Optional[ClientSession] = None

        self._sync_session = requests.Session()
        self._sync_session.headers.update(self.headers)

        self.max_retries: int = 3
        self.backoff_factor: float = 0.5
        self.retry_exceptions: tuple = (
            ClientError,
            asyncio.TimeoutError,
            ConnectionError,
        )

    async def _sleep_with_backoff(self, attempt: int):
        """Экспоненциальная задержка перед повторной попыткой"""
        delay = self.backoff_factor * (2**attempt)
        await asyncio.sleep(delay)

    async def _get_session(self) -> ClientSession:
        """Создаёт или возвращает существующую сессию"""
        if self._session is None:
            timeout = ClientTimeout(total=10, connect=5)
            self._session = ClientSession(
                headers=self.headers, raise_for_status=False, timeout=timeout
            )
        return self._session

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Выполняет HTTP-запрос с повторными попытками
        """
        session = await self._get_session()
        retry_statuses = {408, 429, 500, 502, 503, 504}

        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(method, url, **kwargs) as resp:
                    status_code = resp.status
                    if resp.status < 300:
                        return await resp.json()

                    if 400 <= status_code < 500 and status_code not in retry_statuses:
                        raise EventsProviderError(status_code, resp.reason)

                    if status_code in retry_statuses or status_code >= 500:
                        if attempt == self.max_retries:
                            raise EventsProviderError(status_code, resp.reason)
                        await self._sleep_with_backoff(attempt)
                        # Логи
                        continue

                    raise EventsProviderError(
                        status=status_code,
                        message=resp.reason or "Unexpected status",
                    )
            except self.retry_exceptions as e:
                if attempt == self.max_retries:
                    raise EventsProviderError(
                        status=0,
                        message=f"Network error after {self.max_retries} retries: {e}",
                    )
                # Логи
                await self._sleep_with_backoff(attempt)

    async def check_availability(self):
        """Проверка доступности API"""
        session = await self._get_session()
        try:
            async with session.get(self.base_url) as response:
                status = response.status
                if status == 200:
                    return {"status": "ok"}
                return {"status": "fault"}
        except (ClientConnectorError, ClientTimeout):
            return {"status": "fault"}

    async def get_events_page(
        self, changed_at: str = "2000-01-01", url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение событий на одной странице"""
        params = {"changed_at": changed_at}
        if not url:
            url = f"{self.base_url}/api/events/"
        return await self._request("GET", url, params=params)

    async def get_event_seats(self, event_id: str) -> List[str]:
        """Получить список свободных мест для события"""
        url = f"{self.base_url}/api/events/{event_id}/seats/"
        data = await self._request("GET", url)
        return data.get("seats", [])

    def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> Dict[str, str]:
        """Синхронная регистрация участника"""
        url = f"{self.base_url}/api/events/{event_id}/register/"
        payload = {
            "event_id": event_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat,
        }
        response = self._sync_session.post(url, json=payload)

        if response.status_code < 300:
            return response.json()
        else:
            raise EventsProviderError(
                status=response.status_code,
                message=f"Registration failed (HTTP {response.status_code}):",
            )

    async def unregister(
        self,
        event_id: str,
        ticket_id: str,
    ) -> Dict[str, bool]:
        """Асинхронная отмена регистрации"""
        url = f"{self.base_url}/api/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        return await self._request("DELETE", url, json=payload)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def close_sync(self):
        self._sync_session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
        self.close_sync()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close_sync()
