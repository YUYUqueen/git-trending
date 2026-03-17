from __future__ import annotations
import argparse
import asyncio
import logging

import config
from crawlers.github_trending import crawl_github_trending, crawl_github_trending_developers
from crawlers.github_api import crawl_github_topics, crawl_github_hot_issues
from crawlers.gitee import crawl_gitee_trending
from crawlers.readme_fetcher import fetch_readme_for_signals
from storage.db import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_crawl():
    """Crawl all sources, fetch READMEs, store in database."""
    db = Database(config.DB_PATH)
    db.init()
    errors = []

    # Phase 1: Crawl
    logger.info("Phase 1: Crawling...")
    all_signals = []
    crawlers = [
        ("GitHub Trending", crawl_github_trending),
        ("GitHub Developers", crawl_github_trending_developers),
        ("GitHub Topics", crawl_github_topics),
        ("GitHub Issues", crawl_github_hot_issues),
        ("Gitee", crawl_gitee_trending),
    ]
    for name, crawler in crawlers:
        try:
            signals = await crawler()
            all_signals.extend(signals)
            logger.info("%s: collected %d signals", name, len(signals))
        except ValueError as e:
            logger.error("%s DOM change detected: %s", name, e)
            errors.append(f"{name}: {e}")
        except Exception as e:
            logger.error("%s failed: %s", name, e)
            errors.append(f"{name}: {e}")

    # Phase 2: Fetch READMEs
    logger.info("Phase 2: Fetching READMEs...")
    repo_signals = [s for s in all_signals if s.signal_type in ("trending_repo", "topic")]
    if repo_signals:
        repo_signals = await fetch_readme_for_signals(repo_signals)
        repo_map = {s.source_id: s for s in repo_signals}
        all_signals = [repo_map.get(s.source_id, s) for s in all_signals]

    # Phase 3: Store
    logger.info("Phase 3: Storing %d signals...", len(all_signals))
    for signal in all_signals:
        db.insert_signal(signal)

    db.close()

    if errors:
        logger.warning("Errors during crawling: %s", errors)
    logger.info("Crawl complete: %d signals stored", len(all_signals))


def main():
    parser = argparse.ArgumentParser(description="Git Trending Intelligence Tool - Crawler")
    parser.add_argument("command", choices=["crawl"], help="Command to run")
    args = parser.parse_args()
    if args.command == "crawl":
        asyncio.run(run_crawl())


if __name__ == "__main__":
    main()
