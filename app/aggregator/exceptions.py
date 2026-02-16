from fastapi import HTTPException, status


class AggregatorException(HTTPException):
    """Базовый класс для исключений агрегатора"""

    status_code = 500
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class EventNotFoundException(AggregatorException):
    """Ошибка - отсутствия события"""

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Такого события нет"


class EventNotPublished(AggregatorException):
    """Ошибка не опубликованного события"""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Событие не опубликовано"


class EventPassed(AggregatorException):
    """Ошибка событие прошло"""

    status_code = status.HTTP_409_CONFLICT
    detail = "Cобытие прошло"


class PlaceNotAvailable(AggregatorException):
    """Ошибка недоступного места"""

    status_code = status.HTTP_406_NOT_ACCEPTABLE
    detail = "Место не доступно"


class TicketRegistrationError(HTTPException):
    """Общие ошибки при регистрации"""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class TicketUnRegistrationError(HTTPException):
    """Общие ошибки при удалении билета"""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class TicketNotFoundException(AggregatorException):
    """Ошибка билет не найден"""

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Билет не найден"


class ProviderNetworkError(AggregatorException):
    """Ошибка сети при обращении к провайдеру"""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Сервис временно недоступен"


class ProviderAPIError(AggregatorException):
    """Ошибка, возвращённая API провайдера (4xx, 5xx)"""

    def __init__(self, status: int, detail: str):
        self.status_code = status
        self.detail = f"Ошибка провайдера: {detail}"
        super().__init__()


class ProviderUnexpectedResponse(AggregatorException):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Неожиданный ответ от провайдера"
