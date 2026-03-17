from __future__ import annotations
import asyncio
import base64
import logging
import config
from crawlers.base import Signal
from crawlers.http_client import fetch_json

logger = logging.getLogger(__name__)
REQUEST_DELAY = 1.0
_semaphore = asyncio.Semaphore(3)


async def fetch_readme_for_signals(signals: list[Signal]) -> list[Signal]:
    tasks = [_rate_limited_fetch(s) for s in signals]
    return await asyncio.gather(*tasks)


async def _rate_limited_fetch(signal: Signal) -> Signal:
    async with _semaphore:
        result = await _fetch_single_readme(signal)
        await asyncio.sleep(REQUEST_DELAY)
        return result


async def _fetch_single_readme(signal: Signal) -> Signal:
    if signal.source == "github" and signal.signal_type in ("trending_repo", "topic"):
        repo_path = signal.source_id.replace("github:repo:", "")
        signal.raw_content = await _fetch_github_readme(repo_path)
    elif signal.source == "gitee" and signal.signal_type == "trending_repo":
        repo_path = signal.source_id.replace("gitee:repo:", "")
        signal.raw_content = await _fetch_gitee_readme(repo_path)
    return signal


async def _fetch_github_readme(repo_path: str) -> str:
    try:
        headers = {"Accept": "application/vnd.github+json"}
        if config.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
        data = await fetch_json(f"https://api.github.com/repos/{repo_path}/readme", headers=headers)
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64" and content:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        return content
    except Exception as e:
        logger.warning("Failed to fetch README for %s: %s", repo_path, e)
        return ""


async def _fetch_gitee_readme(repo_path: str) -> str:
    try:
        parts = repo_path.split("/")
        if len(parts) != 2:
            return ""
        owner, repo = parts
        params = {}
        if config.GITEE_TOKEN:
            params["access_token"] = config.GITEE_TOKEN
        data = await fetch_json(f"https://gitee.com/api/v5/repos/{owner}/{repo}/readme", params=params)
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64" and content:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        return content
    except Exception as e:
        logger.warning("Failed to fetch Gitee README for %s: %s", repo_path, e)
        return ""
