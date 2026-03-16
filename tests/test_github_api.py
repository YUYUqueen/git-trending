from datetime import date
from unittest.mock import patch, AsyncMock
import pytest
from crawlers.github_api import crawl_github_topics, crawl_github_hot_issues


@pytest.mark.asyncio
async def test_crawl_github_topics():
    mock_response = {
        "items": [{
            "full_name": "owner/repo",
            "html_url": "https://github.com/owner/repo",
            "description": "A trending topic project",
            "stargazers_count": 5000,
            "forks_count": 200,
            "language": "Python",
            "topics": ["ai", "llm"],
        }]
    }
    with patch("crawlers.github_api.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = await crawl_github_topics()
    assert len(signals) == 1
    assert signals[0].source == "github"
    assert signals[0].signal_type == "topic"
    assert signals[0].source_id == "github:repo:owner/repo"


@pytest.mark.asyncio
async def test_crawl_github_hot_issues():
    mock_response = {
        "items": [{
            "title": "Bug: something broken",
            "html_url": "https://github.com/owner/repo/issues/42",
            "repository_url": "https://api.github.com/repos/owner/repo",
            "reactions": {"+1": 100, "-1": 2, "laugh": 5},
            "comments": 30,
            "labels": [{"name": "bug"}],
        }]
    }
    with patch("crawlers.github_api.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = await crawl_github_hot_issues()
    assert len(signals) == 1
    assert signals[0].signal_type == "hot_issue"
    assert signals[0].source_id == "github:issue:owner/repo#42"
