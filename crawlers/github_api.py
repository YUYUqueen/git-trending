from __future__ import annotations
import logging
from datetime import date, timedelta
import config
from crawlers.base import Signal
from crawlers.http_client import fetch_json

logger = logging.getLogger(__name__)
API_BASE = "https://api.github.com"


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return headers


async def crawl_github_topics() -> list[Signal]:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    data = await fetch_json(
        f"{API_BASE}/search/repositories",
        headers=_github_headers(),
        params={"q": f"created:>{yesterday} stars:>50", "sort": "stars", "order": "desc", "per_page": 30},
    )
    today = date.today()
    signals = []
    for item in data.get("items", []):
        full_name = item["full_name"]
        signals.append(Signal(
            source="github",
            source_id=f"github:repo:{full_name}",
            signal_type="topic",
            title=full_name,
            url=item["html_url"],
            description=item.get("description", "") or "",
            metadata={"stars": item.get("stargazers_count", 0), "forks": item.get("forks_count", 0), "language": item.get("language", ""), "topics": item.get("topics", [])},
            raw_content="",
            collected_at=today,
        ))
    return signals


async def crawl_github_hot_issues() -> list[Signal]:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    data = await fetch_json(
        f"{API_BASE}/search/issues",
        headers=_github_headers(),
        params={"q": f"created:>{yesterday} reactions:>20 is:issue", "sort": "reactions-+1", "order": "desc", "per_page": 30},
    )
    today = date.today()
    signals = []
    for item in data.get("items", []):
        html_url = item["html_url"]
        parts = html_url.replace("https://github.com/", "").split("/")
        if len(parts) >= 4:
            repo_path = f"{parts[0]}/{parts[1]}"
            issue_num = parts[3]
            source_id = f"github:issue:{repo_path}#{issue_num}"
        else:
            source_id = f"github:issue:{html_url}"
        signals.append(Signal(
            source="github",
            source_id=source_id,
            signal_type="hot_issue",
            title=item["title"],
            url=html_url,
            description=item["title"],
            metadata={"reactions": item.get("reactions", {}), "comments": item.get("comments", 0), "labels": [l["name"] for l in item.get("labels", [])]},
            raw_content="",
            collected_at=today,
        ))
    return signals
