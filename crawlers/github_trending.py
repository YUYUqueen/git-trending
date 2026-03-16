from __future__ import annotations
import logging
from datetime import date
from bs4 import BeautifulSoup
from crawlers.base import Signal
from crawlers.http_client import fetch

logger = logging.getLogger(__name__)
TRENDING_URL = "https://github.com/trending"
DEVELOPERS_URL = "https://github.com/trending/developers"


async def crawl_github_trending() -> list[Signal]:
    html = await fetch(TRENDING_URL)
    return parse_trending_repos(html)


async def crawl_github_trending_developers() -> list[Signal]:
    html = await fetch(DEVELOPERS_URL)
    return parse_trending_developers(html)


def parse_trending_repos(html: str) -> list[Signal]:
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.Box-row")
    if not articles:
        raise ValueError("DOM structure changed: no 'article.Box-row' found on GitHub Trending page")
    signals = []
    today = date.today()
    for article in articles:
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        repo_path = h2.get("href", "").strip("/")
        if not repo_path:
            continue
        desc_p = article.select_one("p")
        description = desc_p.get_text(strip=True) if desc_p else ""
        lang_span = article.select_one("[itemprop='programmingLanguage']")
        language = lang_span.get_text(strip=True) if lang_span else ""
        stars_today_el = article.select_one("span.d-inline-block.float-sm-right")
        stars_today_text = stars_today_el.get_text(strip=True) if stars_today_el else ""
        stars_today = parse_star_count(stars_today_text)
        signals.append(Signal(
            source="github",
            source_id=f"github:repo:{repo_path}",
            signal_type="trending_repo",
            title=repo_path,
            url=f"https://github.com/{repo_path}",
            description=description,
            metadata={"language": language, "stars_today": stars_today},
            raw_content="",
            collected_at=today,
        ))
    return signals


def parse_trending_developers(html: str) -> list[Signal]:
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.Box-row")
    if not articles:
        raise ValueError("DOM structure changed: no 'article.Box-row' found on GitHub Trending Developers page")
    signals = []
    today = date.today()
    for article in articles:
        name_link = article.select_one("h1.h3 a")
        if not name_link:
            continue
        username = name_link.get("href", "").strip("/")
        display_name = name_link.get_text(strip=True)
        repo_link = article.select_one("h1.h4 a") or article.select_one("article a.css-truncate-target")
        popular_repo = repo_link.get_text(strip=True) if repo_link else ""
        signals.append(Signal(
            source="github",
            source_id=f"github:dev:{username}",
            signal_type="trending_dev",
            title=display_name or username,
            url=f"https://github.com/{username}",
            description=f"Trending developer. Popular repo: {popular_repo}" if popular_repo else "Trending developer",
            metadata={"username": username, "popular_repo": popular_repo},
            raw_content="",
            collected_at=today,
        ))
    return signals


def parse_star_count(text: str) -> int:
    text = text.replace(",", "").replace("stars today", "").replace("stars this week", "").strip()
    try:
        return int(text)
    except ValueError:
        return 0
