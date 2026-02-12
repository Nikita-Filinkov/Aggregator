from app.provider.client import EventsProviderClient
from app.config import settings


def get_provider_client():
    """Фабрика для создания клиента Events Provider API"""
    client = EventsProviderClient(
        api_key=settings.LMS_API_KEY, base_url=settings.BASE_URL
    )
    return client
