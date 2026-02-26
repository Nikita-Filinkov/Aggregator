from typing import Dict, Optional


class NotificationServiceError(Exception):
    """Базовое исключение для ошибок API Events Provider"""

    def __init__(self, status: int, message: str, body: Optional[Dict] = None):
        self.status = status
        self.message = message
        self.body = body or {}
        super().__init__(f"HTTP {status}: {message}")
