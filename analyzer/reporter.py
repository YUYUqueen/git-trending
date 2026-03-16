from __future__ import annotations
import json
import logging
from analyzer.llm import call_llm
from analyzer.prompts import load_prompt
import config

logger = logging.getLogger(__name__)
TELEGRAM_MAX_LENGTH = 4096
RATING_STARS = {3: "\u2b50\u2b50\u2b50", 2: "\u2b50\u2b50", 1: "\u2b50"}


async def generate_daily_report(analyses: list[dict]) -> str:
    grouped = {}
    for a in analyses:
        domain = a.get("domain", "Other")
        grouped.setdefault(domain, []).append(a)
    sorted_domains = sorted(grouped.items(), key=lambda x: -len(x[1]))
    analyses_text = _format_analyses_for_llm(sorted_domains)
    overview = await call_llm(
        load_prompt("daily_overview", analyses=analyses_text),
        model=config.LLM_MODEL_DAILY,
    )
    lines = []
    lines.append("\U0001f4ca <b>Technology Daily Report</b>\n")
    lines.append(f"{overview}\n")
    lines.append("\u2501" * 20 + "\n")
    for domain, items in sorted_domains:
        lines.append(f"\n<b>{domain}</b>({len(items)})\n")
        for item in sorted(items, key=lambda x: -_get_rating(x)):
            stars = RATING_STARS.get(_get_rating(item), "\u2b50")
            title = item.get("title", "")
            url = item.get("url", "")
            summary = item.get("summary", "")
            lines.append(f'{stars} <a href="{url}">{title}</a>')
            lines.append(f"    {summary}\n")
    return "\n".join(lines)


async def generate_weekly_report(weekly_analyses: list[dict]) -> str:
    weekly_data_text = json.dumps(weekly_analyses, ensure_ascii=False, indent=2)
    report = await call_llm(
        load_prompt("weekly_report", weekly_data=weekly_data_text),
        model=config.LLM_MODEL_WEEKLY,
    )
    return report


def format_daily_telegram(report: str) -> list[str]:
    if len(report) <= TELEGRAM_MAX_LENGTH:
        return [report]
    messages = []
    while report:
        if len(report) <= TELEGRAM_MAX_LENGTH:
            messages.append(report)
            break
        split_at = report.rfind("\n", 0, TELEGRAM_MAX_LENGTH)
        if split_at == -1:
            split_at = TELEGRAM_MAX_LENGTH
        messages.append(report[:split_at])
        report = report[split_at:].lstrip("\n")
    return messages


def _format_analyses_for_llm(sorted_domains: list) -> str:
    lines = []
    for domain, items in sorted_domains:
        lines.append(f"\n## {domain} ({len(items)} projects)")
        for item in items:
            lines.append(f"- {item.get('title', '')}: {item.get('summary', '')}")
            if item.get("insight"):
                lines.append(f"  Insight: {item['insight']}")
    return "\n".join(lines)


def _get_rating(analysis: dict) -> int:
    return analysis.get("rating", 1)
