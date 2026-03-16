from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from analyzer.llm import call_llm


@pytest.mark.asyncio
async def test_call_llm_returns_text():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="LLM response text")]
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    with patch("analyzer.llm.get_client", return_value=mock_client):
        result = await call_llm("test prompt", model="claude-haiku-4-5-20251001")
    assert result == "LLM response text"
