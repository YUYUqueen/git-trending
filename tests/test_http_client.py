import httpx
import pytest
from unittest.mock import patch, AsyncMock

from crawlers.http_client import fetch, fetch_json


@pytest.mark.asyncio
async def test_fetch_returns_text():
    mock_response = httpx.Response(200, text="<html>hello</html>")
    with patch("crawlers.http_client.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance
        result = await fetch("https://example.com")
        assert result == "<html>hello</html>"


@pytest.mark.asyncio
async def test_fetch_json_returns_dict():
    mock_response = httpx.Response(200, json={"items": [1, 2]})
    with patch("crawlers.http_client.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance
        result = await fetch_json("https://api.example.com/data")
        assert result == {"items": [1, 2]}


@pytest.mark.asyncio
async def test_fetch_retries_on_failure():
    fail_response = httpx.Response(500)
    ok_response = httpx.Response(200, text="ok")
    with patch("crawlers.http_client.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.side_effect = [fail_response, ok_response]
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance
        result = await fetch("https://example.com", retries=2, backoff=0)
        assert result == "ok"
