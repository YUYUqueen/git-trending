from __future__ import annotations
import argparse
import asyncio
import logging
import sys

import config
from crawlers.github_trending import crawl_github_trending, crawl_github_trending_developers
from crawlers.github_api import crawl_github_topics, crawl_github_hot_issues
from crawlers.gitee import crawl_gitee_trending
from crawlers.readme_fetcher import fetch_readme_for_signals
from analyzer.classifier import classify_signals, analyze_signal
from analyzer.reporter import generate_daily_report, generate_weekly_report
from notify.telegram import send_report, send_alert
from storage.db import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_daily(dry_run: bool = False):
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
            if not dry_run:
                try:
                    await send_alert(f"Crawler '{name}' DOM structure changed: {e}")
                except Exception:
                    pass
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
    stored_ids = {}
    for signal in all_signals:
        signal_id = db.insert_signal(signal)
        if signal_id:
            stored_ids[signal.source_id] = signal_id

    # Phase 4: Analyze
    logger.info("Phase 4: Analyzing...")
    unanalyzed = db.get_unanalyzed_signals()
    if unanalyzed:
        try:
            domains = await classify_signals(unanalyzed)
        except Exception as e:
            logger.error("Classification failed: %s", e)
            domains = {}
        for signal_row in unanalyzed:
            try:
                analysis = await analyze_signal(signal_row)
                domain = domains.get(signal_row["source_id"], "Other")
                db.insert_analysis(
                    signal_id=signal_row["id"],
                    domain=domain,
                    summary=analysis.get("summary", ""),
                    insight=analysis.get("insight", ""),
                    trend_status=analysis.get("trend_status", "unknown"),
                    rating=analysis.get("rating", 1),
                )
            except Exception as e:
                logger.error("Analysis failed for %s: %s", signal_row["source_id"], e)
                errors.append(f"Analysis {signal_row['source_id']}: {e}")

    # Phase 5: Generate report
    logger.info("Phase 5: Generating daily report...")
    from datetime import date
    analyses = db.get_analyses_by_date(date.today())
    if analyses:
        report = await generate_daily_report(analyses)
        if errors:
            report += f"\n\n\u26a0\ufe0f Errors during collection:\n" + "\n".join(f"- {e}" for e in errors)
        db.insert_report("daily", report)
        if not dry_run:
            logger.info("Phase 6: Sending to Telegram...")
            try:
                await send_report(report)
            except Exception as e:
                logger.error("Telegram send failed: %s", e)
        else:
            logger.info("Phase 6: Dry run — skipping Telegram send")
            print(report)
    else:
        logger.warning("No analyses to report")

    db.close()
    logger.info("Daily pipeline complete")


async def run_weekly(dry_run: bool = False):
    from datetime import date, timedelta
    db = Database(config.DB_PATH)
    db.init()
    today = date.today()
    week_start = today - timedelta(days=7)
    analyses = db.get_analyses_date_range(week_start, today)
    if not analyses:
        logger.warning("No data for weekly report")
        db.close()
        return
    logger.info("Generating weekly report from %d analyses...", len(analyses))
    report = await generate_weekly_report(analyses)
    db.insert_report("weekly", report)
    if not dry_run:
        await send_report(report)
    else:
        print(report)
    db.close()
    logger.info("Weekly pipeline complete")


def main():
    parser = argparse.ArgumentParser(description="Git Trending Intelligence Tool")
    parser.add_argument("command", choices=["daily", "weekly"], help="Pipeline to run")
    parser.add_argument("--dry-run", action="store_true", help="Skip Telegram send and DB upload")
    args = parser.parse_args()
    if args.command == "daily":
        asyncio.run(run_daily(dry_run=args.dry_run))
    elif args.command == "weekly":
        asyncio.run(run_weekly(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
