import base64
from unittest.mock import patch, AsyncMock
import pytest
from crawlers.readme_fetcher import fetch_readme_for_signals
from crawlers.base import Signal
from datetime import date


def make_signal(source_id="github:repo:owner/name", source="github"):
    return Signal(
        source=source, source_id=source_id, signal_type="trending_repo",
        title="owner/name", url=f"https://{source}.com/owner/name",
        description="desc", metadata={}, raw_content="", collected_at=date.today(),
    )


@pytest.mark.asyncio
async def test_fetch_readme_for_github_signal():
    readme_content = base64.b64encode(b"# My Project\nThis is cool.").decode()
    mock_response = {"content": readme_content, "encoding": "base64"}
    with patch("crawlers.readme_fetcher.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = [make_signal()]
        updated = await fetch_readme_for_signals(signals)
    assert updated[0].raw_content == "# My Project\nThis is cool."


@pytest.mark.asyncio
async def test_fetch_readme_truncates_long_content():
    long_readme = "x" * 5000
    readme_content = base64.b64encode(long_readme.encode()).decode()
    mock_response = {"content": readme_content, "encoding": "base64"}
    with patch("crawlers.readme_fetcher.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = [make_signal()]
        updated = await fetch_readme_for_signals(signals)
    assert len(updated[0].raw_content) == 3000


@pytest.mark.asyncio
async def test_fetch_readme_failure_leaves_empty():
    with patch("crawlers.readme_fetcher.fetch_json", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("404")
        signals = [make_signal()]
        updated = await fetch_readme_for_signals(signals)
    assert updated[0].raw_content == ""
