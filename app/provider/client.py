import asyncio
import logging
from typing import Any, Dict, List, Optional

import requests
from aiohttp import ClientConnectorError, ClientError, ClientSession, ClientTimeout
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.logger import logger
from app.provider.exceptions import EventsProviderError, ProviderTemporaryError


class EventsProviderClient:
    """Асинхронный HTTP-клиент для Events Provider API"""

    MAX_RETRIES = settings.MAX_RETRIES
    BACKOFF_FACTOR = settings.BACKOFF_FACTOR
    ASYNC_RETRY_EXCEPTIONS = (
        ClientError,
        asyncio.TimeoutError,
        ConnectionError,
        ProviderTemporaryError,
    )
    SYNC_RETRY_EXCEPTIONS = (
        requests.ConnectionError,
        requests.Timeout,
        requests.RequestException,
    )
    RETRY_STATUSES = {408, 429, 500, 502, 503, 504}

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-api-key": api_key}
        self._session: Optional[ClientSession] = None

        self._sync_session = requests.Session()
        self._sync_session.headers.update(self.headers)

    async def _get_session(self) -> ClientSession:
        """Создаёт или возвращает существующую сессию"""
        if self._session is None:
            timeout = ClientTimeout(total=10, connect=5)
            self._session = ClientSession(
                headers=self.headers, raise_for_status=False, timeout=timeout
            )
        return self._session

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=BACKOFF_FACTOR, min=1, max=5),
        retry=retry_if_exception_type(ASYNC_RETRY_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Выполняет HTTP-запрос с повторными попытками"""
        session = await self._get_session()

        try:
            async with session.request(method, url, **kwargs) as resp:
                if resp.status < 300:
                    return await resp.json()

                if resp.status in self.RETRY_STATUSES or resp.status >= 500:
                    raise ProviderTemporaryError(status=resp.status)

                raise EventsProviderError(
                    status=resp.status, message=f"Provider error: {resp.reason}"
                )
        except (ClientError, asyncio.TimeoutError, ConnectionError) as e:
            message = "Ошибка при обращении к провайдеру"
            logger.warning(message, extra={"tries": self.MAX_RETRIES, "error": str(e)})
            raise ProviderTemporaryError(status=0, message=message)

    async def check_availability(self):
        """Проверка доступности API"""
        session = await self._get_session()
        try:
            async with session.get(self.base_url) as response:
                status = response.status
                if status == 200:
                    return {"status": "ok"}
                return {"status": "fault"}
        except (ClientConnectorError, asyncio.TimeoutError):
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

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=BACKOFF_FACTOR, min=1, max=5),
        retry=retry_if_exception_type(SYNC_RETRY_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> Dict[str, str]:
        """Синхронная регистрация участника с повторными попытками"""
        url = f"{self.base_url}/api/events/{event_id}/register/"

        payload = {
            "event_id": event_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat,
        }

        try:
            response = self._sync_session.post(url, json=payload)
            status = response.status_code

            if status < 300:
                return response.json()

            elif status in self.RETRY_STATUSES or status >= 500:
                raise ProviderTemporaryError(status=status)
            else:
                raise EventsProviderError(
                    status=status, message=f"Ошибка провайдера: {response.reason}"
                )

        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            logger.warning("Ошибка сети при регистрации", extra={"error": str(e)})
            raise ProviderTemporaryError(status=0, message="Network error") from e

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
        """Синхронное закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def close_sync(self):
        """Асинхронное закрытие сессии"""
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
