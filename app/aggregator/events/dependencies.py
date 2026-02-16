from datetime import date
from typing import Optional

from fastapi import Request


def get_url_builder(request: Request):
    base_url = str(request.base_url).rstrip("/")

    def build_url(
        page: int,
        page_size: int,
        date_from: Optional[date] = None,
        endpoint: str = "/api/events/",
    ) -> str:
        url = f"{base_url}{endpoint}?page={page}&page_size={page_size}"
        if date_from:
            url += f"&date_from={date_from.isoformat()}"
        return url

    return build_url
