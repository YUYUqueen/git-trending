from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date
import pytest
from main import run_daily


@pytest.mark.asyncio
async def test_run_daily_pipeline(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("main.crawl_github_trending", new_callable=AsyncMock) as mock_gh_trending, \
         patch("main.crawl_github_trending_developers", new_callable=AsyncMock) as mock_gh_devs, \
         patch("main.crawl_github_topics", new_callable=AsyncMock) as mock_gh_topics, \
         patch("main.crawl_github_hot_issues", new_callable=AsyncMock) as mock_gh_issues, \
         patch("main.crawl_gitee_trending", new_callable=AsyncMock) as mock_gitee, \
         patch("main.fetch_readme_for_signals", new_callable=AsyncMock) as mock_readme, \
         patch("main.classify_signals", new_callable=AsyncMock) as mock_classify, \
         patch("main.analyze_signal", new_callable=AsyncMock) as mock_analyze, \
         patch("main.generate_daily_report", new_callable=AsyncMock) as mock_report, \
         patch("main.send_report", new_callable=AsyncMock) as mock_send, \
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
        mock_classify.return_value = {"github:repo:o/n": "AI/LLM"}
        mock_analyze.return_value = {
            "summary": "s", "insight": "i",
            "trend_status": "new_burst", "rating": 3,
        }
        mock_report.return_value = "Daily report content"

        await run_daily(dry_run=False)

        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_run_daily_dry_run_skips_send(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("main.crawl_github_trending", new_callable=AsyncMock) as mock_gh, \
         patch("main.crawl_github_trending_developers", new_callable=AsyncMock), \
         patch("main.crawl_github_topics", new_callable=AsyncMock), \
         patch("main.crawl_github_hot_issues", new_callable=AsyncMock), \
         patch("main.crawl_gitee_trending", new_callable=AsyncMock), \
         patch("main.fetch_readme_for_signals", new_callable=AsyncMock) as mock_readme, \
         patch("main.classify_signals", new_callable=AsyncMock) as mock_classify, \
         patch("main.analyze_signal", new_callable=AsyncMock) as mock_analyze, \
         patch("main.generate_daily_report", new_callable=AsyncMock) as mock_report, \
         patch("main.send_report", new_callable=AsyncMock) as mock_send, \
         patch("main.config") as mock_config:

        mock_config.DB_PATH = db_path
        mock_gh.return_value = []
        mock_readme.return_value = []
        mock_classify.return_value = {}
        mock_report.return_value = "report"

        await run_daily(dry_run=True)

        mock_send.assert_not_called()
