from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from notify.telegram import send_report, send_alert


@pytest.mark.asyncio
async def test_send_report_single_message():
    with patch("notify.telegram.Bot") as MockBot:
        mock_bot = AsyncMock()
        MockBot.return_value = mock_bot
        await send_report("Short report")
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["text"] == "Short report"
        assert call_kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_send_report_splits_long_message():
    long_report = "Line\n" * 1000
    with patch("notify.telegram.Bot") as MockBot:
        mock_bot = AsyncMock()
        MockBot.return_value = mock_bot
        await send_report(long_report)
        assert mock_bot.send_message.call_count > 1


@pytest.mark.asyncio
async def test_send_alert():
    with patch("notify.telegram.Bot") as MockBot:
        mock_bot = AsyncMock()
        MockBot.return_value = mock_bot
        await send_alert("Something broke!")
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "Alert" in call_kwargs["text"]
        assert "Something broke!" in call_kwargs["text"]
