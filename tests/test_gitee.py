from datetime import date
from unittest.mock import patch, AsyncMock
import pytest
from crawlers.gitee import crawl_gitee_trending


@pytest.mark.asyncio
async def test_crawl_gitee_trending():
    mock_response = [{
        "full_name": "owner/repo",
        "html_url": "https://gitee.com/owner/repo",
        "description": "A Chinese open source project",
        "stargazers_count": 3000,
        "forks_count": 500,
        "language": "Java",
    }]
    with patch("crawlers.gitee.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = await crawl_gitee_trending()
    assert len(signals) == 1
    assert signals[0].source == "gitee"
    assert signals[0].signal_type == "trending_repo"
    assert signals[0].source_id == "gitee:repo:owner/repo"


@pytest.mark.asyncio
async def test_crawl_gitee_trending_fallback_to_search():
    search_response = {"data": [{
        "full_name": "owner/repo2",
        "html_url": "https://gitee.com/owner/repo2",
        "description": "Fallback project",
        "stargazers_count": 1000,
        "forks_count": 100,
        "language": "Go",
    }]}
    with patch("crawlers.gitee.fetch_json", new_callable=AsyncMock) as mock:
        mock.side_effect = [Exception("404"), search_response]
        signals = await crawl_gitee_trending()
    assert len(signals) == 1
    assert signals[0].source == "gitee"
