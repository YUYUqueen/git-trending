from unittest.mock import patch, AsyncMock
import pytest
from analyzer.reporter import generate_daily_report, generate_weekly_report, format_daily_telegram


@pytest.mark.asyncio
async def test_generate_daily_report():
    analyses = [
        {
            "title": "owner/ai-tool", "url": "https://github.com/owner/ai-tool",
            "domain": "AI/LLM", "summary": "An AI tool", "insight": "Very useful",
            "trend_status": "new_burst", "source": "github",
            "metadata": '{"language": "Python", "stars_today": 500}',
            "signal_type": "trending_repo", "description": "AI tool desc",
            "rating": 3,
        },
        {
            "title": "owner/web-fw", "url": "https://github.com/owner/web-fw",
            "domain": "Web", "summary": "A web framework", "insight": "Fast",
            "trend_status": "rising", "source": "github",
            "metadata": '{"language": "TypeScript", "stars_today": 200}',
            "signal_type": "trending_repo", "description": "Web fw desc",
            "rating": 2,
        },
    ]
    with patch("analyzer.reporter.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = "今天 AI 领域有一个新项目爆发..."
        report = await generate_daily_report(analyses)
    assert "今天 AI 领域" in report
    assert "AI/LLM" in report
    assert "owner/ai-tool" in report


@pytest.mark.asyncio
async def test_generate_weekly_report():
    weekly_analyses = [{
        "title": "owner/proj", "url": "https://github.com/owner/proj",
        "domain": "AI/LLM", "summary": "An AI project", "insight": "Notable",
        "trend_status": "sustained", "source": "github", "collected_at": "2026-03-15",
        "metadata": '{"language": "Python"}', "signal_type": "trending_repo",
        "description": "desc",
    }]
    with patch("analyzer.reporter.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = "本周 AI 领域持续活跃..."
        report = await generate_weekly_report(weekly_analyses)
    assert "本周" in report


def test_format_daily_telegram():
    report = "# Daily Report\n\nSome content here"
    messages = format_daily_telegram(report)
    assert len(messages) >= 1
    assert isinstance(messages[0], str)


def test_format_daily_telegram_splits_long():
    report = "Line\n" * 2000  # > 4096 chars
    messages = format_daily_telegram(report)
    assert len(messages) > 1
    for msg in messages:
        assert len(msg) <= 4096
