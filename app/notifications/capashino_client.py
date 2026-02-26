from typing import Optional

from aiohttp import ClientSession

from app.logger import logger
from app.notifications.exceptions import (
    BadRequestNotificationException,
    ExistsNotificationException,
    NotificationServiceErrorException,
    UnexpectedNotificationError,
    WrongApiKeyNotificationException,
)


class CapashinoClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._session: Optional[ClientSession] = None

    async def _get_session(self) -> ClientSession:
        """Получение соединения с сервисом уведомлений(Capashino)"""
        if self._session is None:
            self._session = ClientSession(
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json"}
            )
        return self._session

    async def send_notification(
        self, message: str, reference_id: str, idempotency_key: str
    ) -> bool:
        """Отправить уведомление"""
        url = f"{self.base_url}/api/notifications"
        payload = {
            "message": message,
            "reference_id": reference_id,
            "idempotency_key": idempotency_key,
        }
        session = await self._get_session()
        try:
            async with session.post(url, json=payload) as resp:
                status = resp.status

                if status == 201:
                    return True

                elif status == 400:
                    logger.error(
                        f"Нет reference_id, невалидное тело: {status} - {await resp.text()}"
                    )
                    raise BadRequestNotificationException

                elif status == 401:
                    logger.error(
                        f"Нет/неверный X-API-Key: {status} - {await resp.text()}"
                    )
                    raise WrongApiKeyNotificationException

                elif status == 409:
                    logger.error(
                        f"Уже есть уведомление с таким idempotency_key: {status} - {await resp.text()}"
                    )
                    raise ExistsNotificationException

                elif status >= 500:
                    logger.error(
                        f"Ошибка на стороне сервиса уведомлений: {status} - {await resp.text()}"
                    )
                    raise NotificationServiceErrorException

                else:
                    logger.error(f"Capashino error: {status} - {await resp.text()}")
                    message = (
                        "Неожиданная ошибка при отправке сообщения в сервис уведомлений"
                    )
                    raise UnexpectedNotificationError(status, message)
        except Exception:
            raise

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
