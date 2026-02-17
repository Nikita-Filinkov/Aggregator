import asyncio
import time
from typing import Dict, List, Tuple

from aiohttp import ClientConnectorError

from app.provider.client import EventsProviderClient
from app.provider.exceptions import EventsProviderError

_seats_cache: Dict[str, Tuple[float, List[str]]] = {}
_cache_lock = asyncio.Lock()
CACHE_TTL = 30  # секунд


async def get_available_seats(
    event_id: str,
    client: EventsProviderClient,
) -> List[str]:

    async with _cache_lock:
        cached = _seats_cache.get(event_id)
        if cached is not None and time.time() - cached[0] < CACHE_TTL:
            return cached[1]

    try:
        seats = await client.get_event_seats(event_id)
    except (ClientConnectorError, asyncio.TimeoutError):
        raise

    except EventsProviderError:
        raise

    except Exception:
        raise

    async with _cache_lock:
        _seats_cache[event_id] = (time.time(), seats)
    return seats
