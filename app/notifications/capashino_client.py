from typing import Optional

from aiohttp import ClientSession

from app.logger import logger


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

    async def send_notification(self, message: str, reference_id: str, idempotency_key: str) -> bool:
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
                if resp.status == 201:
                    return True
                else:
                    # Расширить обработку ошибок
                    logger.error(f"Capashino error: {resp.status} - {await resp.text()}")
                    return False
        except Exception:
            logger.exception("Capashino request failed")
            return False

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
