from __future__ import annotations
import json
import logging
import re
from analyzer.llm import call_llm
from analyzer.prompts import load_prompt

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Otherwise return as-is
    return text.strip()


async def classify_signals(signals: list[dict]) -> dict[str, str]:
    projects_text = json.dumps(
        [{"source_id": s["source_id"], "title": s["title"], "description": s.get("description", "")} for s in signals],
        ensure_ascii=False,
    )
    response = await call_llm(load_prompt("classify", projects=projects_text))
    try:
        classifications = json.loads(_extract_json(response))
        return {c["source_id"]: c["domain"] for c in classifications}
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse classification response: %s", e)
        return {}


async def analyze_signal(signal: dict) -> dict:
    metadata = signal.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    response = await call_llm(
        load_prompt(
            "analyze",
            title=signal.get("title", ""),
            url=signal.get("url", ""),
            description=signal.get("description", ""),
            language=metadata.get("language", "N/A"),
            stars_today=str(metadata.get("stars_today", "N/A")),
            raw_content=signal.get("raw_content", ""),
        )
    )
    try:
        return json.loads(_extract_json(response))
    except json.JSONDecodeError as e:
        logger.error("Failed to parse analysis response: %s", e)
        return {"summary": signal.get("description", ""), "insight": "", "trend_status": "unknown", "rating": 1}
