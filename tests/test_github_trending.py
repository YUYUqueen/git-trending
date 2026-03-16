import os
from datetime import date
from unittest.mock import patch, AsyncMock
import pytest
from crawlers.github_trending import crawl_github_trending


@pytest.fixture
def trending_html():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "github_trending.html")
    with open(fixture_path) as f:
        return f.read()


@pytest.mark.asyncio
async def test_crawl_github_trending(trending_html):
    with patch("crawlers.github_trending.fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = trending_html
        signals = await crawl_github_trending()
    assert len(signals) > 0
    for s in signals:
        assert s.source == "github"
        assert s.signal_type == "trending_repo"
        assert s.source_id.startswith("github:repo:")
        assert s.url.startswith("https://github.com/")
        assert s.collected_at == date.today()


@pytest.mark.asyncio
async def test_crawl_github_trending_validates_dom():
    with patch("crawlers.github_trending.fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = "<html><body>totally different page</body></html>"
        with pytest.raises(ValueError, match="DOM structure"):
            await crawl_github_trending()
