import json
from unittest.mock import patch, AsyncMock
import pytest
from analyzer.classifier import classify_signals, analyze_signal


@pytest.mark.asyncio
async def test_classify_signals():
    mock_llm_response = json.dumps([
        {"source_id": "github:repo:owner/ai-tool", "domain": "AI/LLM"},
        {"source_id": "github:repo:owner/web-fw", "domain": "Web Frontend"},
    ])
    with patch("analyzer.classifier.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = mock_llm_response
        result = await classify_signals([
            {"source_id": "github:repo:owner/ai-tool", "title": "ai-tool", "description": "AI thing"},
            {"source_id": "github:repo:owner/web-fw", "title": "web-fw", "description": "Web thing"},
        ])
    assert result["github:repo:owner/ai-tool"] == "AI/LLM"
    assert result["github:repo:owner/web-fw"] == "Web Frontend"


@pytest.mark.asyncio
async def test_analyze_signal():
    mock_llm_response = json.dumps({
        "summary": "A tokenizer library",
        "insight": "From Karpathy, educational",
        "trend_status": "new_burst",
        "rating": 3,
    })
    with patch("analyzer.classifier.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = mock_llm_response
        result = await analyze_signal({
            "title": "owner/repo",
            "url": "https://github.com/owner/repo",
            "description": "desc",
            "metadata": '{"language": "Python", "stars_today": 500}',
            "raw_content": "# README",
        })
    assert result["summary"] == "A tokenizer library"
    assert result["trend_status"] == "new_burst"
    assert result["rating"] == 3
