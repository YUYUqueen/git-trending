from __future__ import annotations
import logging
from datetime import date
import config
from crawlers.base import Signal
from crawlers.http_client import fetch_json

logger = logging.getLogger(__name__)
GITEE_API = "https://gitee.com/api/v5"


async def crawl_gitee_trending() -> list[Signal]:
    try:
        data = await _try_trending_endpoint()
    except Exception:
        logger.warning("Gitee trending endpoint failed, falling back to search")
        data = await _fallback_search()
    return _parse_repos(data)


async def _try_trending_endpoint() -> list[dict]:
    params = {}
    if config.GITEE_TOKEN:
        params["access_token"] = config.GITEE_TOKEN
    return await fetch_json(f"{GITEE_API}/projects/trending", params=params)


async def _fallback_search() -> list[dict]:
    params = {"sort": "stars_count", "order": "desc", "per_page": 30, "page": 1}
    if config.GITEE_TOKEN:
        params["access_token"] = config.GITEE_TOKEN
    result = await fetch_json(f"{GITEE_API}/search/repositories", params=params)
    if isinstance(result, dict):
        return result.get("data", result.get("items", []))
    return result


def _parse_repos(data: list[dict]) -> list[Signal]:
    today = date.today()
    signals = []
    for item in data:
        full_name = item.get("full_name", "")
        signals.append(Signal(
            source="gitee",
            source_id=f"gitee:repo:{full_name}",
            signal_type="trending_repo",
            title=full_name,
            url=item.get("html_url", ""),
            description=item.get("description", "") or "",
            metadata={"stars": item.get("stargazers_count", 0), "forks": item.get("forks_count", 0), "language": item.get("language", "")},
            raw_content="",
            collected_at=today,
        ))
    return signals
