import pytest
from aiohttp import ClientSession
from unittest.mock import AsyncMock, MagicMock, patch
from requests import Response

from app.provider.client import EventsProviderError, EventsProviderClient


@pytest.mark.asyncio
async def test_get_events_page_success(patched_client, mock_session, mock_response_factory):
    """Успешное получение страницы событий по параметру changed_at"""
    json_response = {
        "next": "https://test.events-provider.com/api/events/?cursor=xyz",
        "previous": None,
        "results": [{"id": "event1"}]
    }
    mock_response = mock_response_factory(status=200, json_data=json_response)
    mock_session.request.return_value = mock_response

    result = await patched_client.get_events_page(changed_at="2020-01-01")

    assert result == json_response
    mock_session.request.assert_called_once_with(
        "GET",
        "https://test.events-provider.com/api/events/",
        params={"changed_at": "2020-01-01"}
    )


@pytest.mark.asyncio
async def test_get_events_page_with_url(patched_client, mock_session, mock_response_factory):
    """Получение страницы по-полному URL (следующая страница)"""
    mock_response = mock_response_factory(status=200, json_data={"results": []})
    mock_session.request.return_value = mock_response

    url = "https://test.events-provider.com/api/events/?cursor=xyz"
    await patched_client.get_events_page(url=url)

    mock_session.request.assert_called_once_with(
        "GET",
        url,
        params={"changed_at": "2000-01-01"}
    )


@pytest.mark.asyncio
async def test_get_event_seats_success(patched_client, mock_session, mock_response_factory):
    """Успешное получение списка свободных мест"""
    mock_response = mock_response_factory(status=200, json_data={"seats": ["A1", "A2", "B3"]})
    mock_session.request.return_value = mock_response

    seats = await patched_client.get_event_seats("event-123")

    assert seats == ["A1", "A2", "B3"]
    mock_session.request.assert_called_once_with(
        "GET",
        "https://test.events-provider.com/api/events/event-123/seats/"
    )


@pytest.mark.asyncio
async def test_get_event_seats_empty(patched_client, mock_session, mock_response_factory):
    """Если API вернул пустой объект (нет ключа seats), возвращаем пустой список"""
    mock_response = mock_response_factory(status=200, json_data={})
    mock_session.request.return_value = mock_response

    seats = await patched_client.get_event_seats("event-123")

    assert seats == []


@pytest.mark.asyncio
async def test_unregister_success(patched_client, mock_session, mock_response_factory):
    """Успешная отмена регистрации"""
    mock_response = mock_response_factory(status=200, json_data={"success": True})
    mock_session.request.return_value = mock_response

    result = await patched_client.unregister(event_id="event-123", ticket_id="ticket-123")

    assert result == {"success": True}
    mock_session.request.assert_called_once_with(
        "DELETE",
        "https://test.events-provider.com/api/events/event-123/unregister/",
        json={"ticket_id": "ticket-123"}
    )

@pytest.mark.asyncio
async def test_retry_on_server_error(patched_client, mock_session, mock_response_factory):
    """При ошибке 500 клиент должен повторить запрос"""
    mock_response_500 = mock_response_factory(status=500)
    mock_response_200 = mock_response_factory(status=200, json_data={"seats": ["A1"]})
    mock_session.request.side_effect = [mock_response_500, mock_response_200]

    seats = await patched_client.get_event_seats("event-123")

    assert seats == ["A1"]
    assert mock_session.request.call_count == 2


@pytest.mark.asyncio
async def test_max_retries_exceeded(patched_client, mock_session, mock_response_factory):
    """Превышение числа попыток – выбрасывается исключение"""
    mock_response = mock_response_factory(status=500)
    mock_session.request.return_value = mock_response

    with pytest.raises(EventsProviderError) as exc_info:
        await patched_client.get_event_seats("event-123")

    assert exc_info.value.status == 500
    expected_calls = patched_client.max_retries + 1
    assert mock_session.request.call_count == expected_calls


def test_register_success(client, mock_sync_session):
    """Успешная синхронная регистрация"""
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 201
    mock_response.json.return_value = {"ticket_id": "ticket-123"}

    mock_sync_session.post.return_value = mock_response

    with patch.object(client, '_sync_session', mock_sync_session):
        result = client.register(
            event_id="event-123",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15"
        )

    assert result == {"ticket_id": "ticket-123"}
    mock_sync_session.post.assert_called_once_with(
        "https://test.events-provider.com/api/events/event-123/register/",
        json={
            "event_id": "event-123",
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "ivan@example.com",
            "seat": "A15"
        }
    )


def test_register_error(client, mock_sync_session):
    """Ошибка регистрации (например, место занято)"""
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 400
    mock_response.reason = "Bad Request"

    mock_sync_session.post.return_value = mock_response

    with patch.object(client, '_sync_session', mock_sync_session):
        with pytest.raises(EventsProviderError) as exc_info:
            client.register(
                event_id="event-123",
                first_name="Иван",
                last_name="Иванов",
                email="ivan@example.com",
                seat="A15"
            )

    assert exc_info.value.status == 400


def test_client_headers():
    """Проверка заголовков с API-ключом"""
    client = EventsProviderClient(api_key="my-key", base_url="http://test.com")
    assert client.headers == {"x-api-key": "my-key"}
    assert client._sync_session.headers.get("x-api-key") == "my-key"


@pytest.mark.asyncio
async def test_close():
    """Проверка закрытия асинхронной сессии"""
    client = EventsProviderClient(api_key="key", base_url="http://test.com")
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.closed = False
    client._session = mock_session

    await client.close()
    mock_session.close.assert_awaited_once()
    assert client._session is None

    mock_sync_session = MagicMock()
    client._sync_session = mock_sync_session
    client.close_sync()
    mock_sync_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager():
    """Проверка работы async with"""
    client = EventsProviderClient(api_key="key", base_url="http://test.com")
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.closed = False
    client._session = mock_session

    async with client as cm:
        assert cm is client

    mock_session.close.assert_awaited_once()
