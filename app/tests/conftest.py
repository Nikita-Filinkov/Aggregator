from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponse, ClientSession

from app.provider.client import EventsProviderClient


@pytest.fixture
def client():
    """Базовая фикстура клиента с тестовыми параметрами"""
    return EventsProviderClient(
        api_key="test-api-key", base_url="https://test.events-provider.com"
    )


@pytest.fixture
def mock_response_factory():
    """Фабрика для создания мок-ответов aiohttp с поддержкой async with"""

    def _create_mock_response(status=200, json_data=None):
        mock = AsyncMock(spec=ClientResponse)
        mock.status = status
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=None)
        mock.json = AsyncMock(return_value=json_data or {})
        return mock

    return _create_mock_response


@pytest.fixture
def mock_session(mock_response_factory):
    """Мок сессии aiohttp с настроенным request (возвращает MagicMock)"""
    session = AsyncMock(spec=ClientSession)
    session.request = MagicMock(return_value=mock_response_factory())
    return session


@pytest.fixture
def patched_client(client, mock_session):
    """Клиент с подменённым _get_session, возвращающим mock_session."""
    with patch.object(client, "_get_session", return_value=mock_session):
        yield client


@pytest.fixture
def mock_sync_session():
    """Мок для синхронной сессии (requests. Session)."""
    return MagicMock()
