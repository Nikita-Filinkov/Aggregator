from app.clients.provider_client import EventsProviderClient
from app.config import settings


def get_provider_client():
    client = EventsProviderClient(
        api_key=settings.LMS_API_KEY, base_url=settings.BASE_URL
    )
    return client
