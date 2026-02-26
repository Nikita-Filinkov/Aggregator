

class EventsProviderError(Exception):
    """Базовое исключение для ошибок API Events Provider"""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class ProviderTemporaryError(EventsProviderError):
    """Исключение для временных ошибок"""

    def __init__(self, status: int, message: str = "Временная ошибка"):
        self.status = status
        self.message = message
        super().__init__(self.status, self.message)
