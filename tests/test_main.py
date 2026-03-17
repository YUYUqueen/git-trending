from unittest.mock import patch, AsyncMock
from datetime import date
import pytest
from main import run_crawl


@pytest.mark.asyncio
async def test_run_crawl(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("main.crawl_github_trending", new_callable=AsyncMock) as mock_gh_trending, \
         patch("main.crawl_github_trending_developers", new_callable=AsyncMock) as mock_gh_devs, \
         patch("main.crawl_github_topics", new_callable=AsyncMock) as mock_gh_topics, \
         patch("main.crawl_github_hot_issues", new_callable=AsyncMock) as mock_gh_issues, \
         patch("main.crawl_gitee_trending", new_callable=AsyncMock) as mock_gitee, \
         patch("main.fetch_readme_for_signals", new_callable=AsyncMock) as mock_readme, \
         patch("main.config") as mock_config:

        mock_config.DB_PATH = db_path

        from crawlers.base import Signal
        signal = Signal(
            source="github", source_id="github:repo:o/n",
            signal_type="trending_repo", title="o/n",
            url="https://github.com/o/n", description="d",
            metadata={"language": "Python"}, raw_content="readme",
            collected_at=date.today(),
        )

        mock_gh_trending.return_value = [signal]
        mock_gh_devs.return_value = []
        mock_gh_topics.return_value = []
        mock_gh_issues.return_value = []
        mock_gitee.return_value = []
        mock_readme.return_value = [signal]

        await run_crawl()

        mock_gh_trending.assert_called_once()
        mock_readme.assert_called_once()
