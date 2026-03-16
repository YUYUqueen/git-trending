from __future__ import annotations
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


async def fetch(url: str, headers: dict | None = None, retries: int = 3, backoff: float = 1.0) -> str:
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for attempt in range(retries):
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
            logger.warning("fetch %s attempt %d: status %d", url, attempt + 1, response.status_code)
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
    raise httpx.HTTPStatusError(f"Failed after {retries} retries", request=response.request, response=response)


async def fetch_json(url: str, headers: dict | None = None, params: dict | None = None, retries: int = 3, backoff: float = 1.0) -> dict:
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for attempt in range(retries):
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            logger.warning("fetch_json %s attempt %d: status %d", url, attempt + 1, response.status_code)
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
    raise httpx.HTTPStatusError(f"Failed after {retries} retries", request=response.request, response=response)
