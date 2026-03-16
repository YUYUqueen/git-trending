# Git Trending Intelligence Tool Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily automated pipeline that crawls GitHub + Gitee trending content, analyzes it with Claude LLM, and pushes structured reports to Telegram.

**Architecture:** Modular Python pipeline — crawlers produce unified Signal objects, stored in SQLite, analyzed by Claude API, formatted into daily/weekly reports, pushed via Telegram Bot. Runs on GitHub Actions cron. SQLite persisted via GitHub Releases.

**Tech Stack:** Python 3.11+, httpx, BeautifulSoup4, anthropic SDK, python-telegram-bot, SQLite3, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-03-17-git-trending-tool-design.md`

---

## Chunk 1: Foundation — Data Model, Config, Storage

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```txt
httpx>=0.27.0
beautifulsoup4>=4.12.0
anthropic>=0.40.0
python-telegram-bot>=21.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "git-trending"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
data/*.db
.venv/
```

- [ ] **Step 4: Create data directory with .gitkeep**

```bash
mkdir -p data && touch data/.gitkeep
```

- [ ] **Step 5: Create virtual environment and install dependencies**

Run: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pyproject.toml .gitignore data/.gitkeep
git commit -m "chore: project scaffolding and dependencies"
```

---

### Task 2: Signal data model

**Files:**
- Create: `crawlers/__init__.py`
- Create: `crawlers/base.py`
- Create: `tests/__init__.py`
- Create: `tests/test_base.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_base.py
from datetime import date
from crawlers.base import Signal


def test_signal_creation():
    signal = Signal(
        source="github",
        source_id="github:repo:owner/name",
        signal_type="trending_repo",
        title="owner/name",
        url="https://github.com/owner/name",
        description="A cool project",
        metadata={"stars": 1000, "language": "Python"},
        raw_content="# README\nThis is a project.",
        collected_at=date(2026, 3, 17),
    )
    assert signal.source == "github"
    assert signal.source_id == "github:repo:owner/name"
    assert signal.signal_type == "trending_repo"


def test_signal_raw_content_truncation():
    long_content = "x" * 5000
    signal = Signal(
        source="github",
        source_id="github:repo:owner/name",
        signal_type="trending_repo",
        title="owner/name",
        url="https://github.com/owner/name",
        description="desc",
        metadata={},
        raw_content=long_content,
        collected_at=date(2026, 3, 17),
    )
    assert len(signal.raw_content) == 3000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crawlers'`

- [ ] **Step 3: Write minimal implementation**

```python
# crawlers/__init__.py
```

```python
# crawlers/base.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

MAX_RAW_CONTENT_LENGTH = 3000


@dataclass
class Signal:
    source: str
    source_id: str
    signal_type: str
    title: str
    url: str
    description: str
    metadata: dict
    raw_content: str
    collected_at: date

    def __post_init__(self):
        if len(self.raw_content) > MAX_RAW_CONTENT_LENGTH:
            self.raw_content = self.raw_content[:MAX_RAW_CONTENT_LENGTH]
```

```python
# tests/__init__.py
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_base.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add crawlers/ tests/
git commit -m "feat: add Signal data model with raw_content truncation"
```

---

### Task 3: Config module

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
from unittest.mock import patch


def test_config_loads_from_env():
    env = {
        "GITHUB_TOKEN": "gh_test",
        "GITEE_TOKEN": "gitee_test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "TELEGRAM_BOT_TOKEN": "123:ABC",
        "TELEGRAM_CHAT_ID": "-100123",
    }
    with patch.dict(os.environ, env, clear=False):
        from importlib import reload
        import config
        reload(config)
        assert config.GITHUB_TOKEN == "gh_test"
        assert config.GITEE_TOKEN == "gitee_test"
        assert config.ANTHROPIC_API_KEY == "sk-ant-test"
        assert config.TELEGRAM_BOT_TOKEN == "123:ABC"
        assert config.TELEGRAM_CHAT_ID == "-100123"


def test_config_defaults():
    from importlib import reload
    import config
    reload(config)
    assert config.LLM_MODEL_DAILY == "claude-haiku-4-5-20251001"
    assert config.LLM_MODEL_WEEKLY == "claude-sonnet-4-6"
    assert config.DB_PATH == "data/trending.db"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Write minimal implementation**

```python
# config.py
import os

# API tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITEE_TOKEN = os.getenv("GITEE_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# LLM models
LLM_MODEL_DAILY = os.getenv("LLM_MODEL_DAILY", "claude-haiku-4-5-20251001")
LLM_MODEL_WEEKLY = os.getenv("LLM_MODEL_WEEKLY", "claude-sonnet-4-6")

# Storage
DB_PATH = os.getenv("DB_PATH", "data/trending.db")

# Retry
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1  # seconds
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config module loading from environment variables"
```

---

### Task 4: SQLite storage layer

**Files:**
- Create: `storage/__init__.py`
- Create: `storage/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db.py
import os
import tempfile
from datetime import date, datetime

from crawlers.base import Signal
from storage.db import Database


def make_signal(**overrides):
    defaults = dict(
        source="github",
        source_id="github:repo:owner/name",
        signal_type="trending_repo",
        title="owner/name",
        url="https://github.com/owner/name",
        description="A cool project",
        metadata={"stars": 1000},
        raw_content="# README",
        collected_at=date(2026, 3, 17),
    )
    defaults.update(overrides)
    return Signal(**defaults)


def test_init_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        # Verify tables exist
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "signals" in table_names
        assert "analyses" in table_names
        assert "reports" in table_names
        db.close()
    finally:
        os.unlink(db_path)


def test_insert_and_query_signal():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        signal = make_signal()
        signal_id = db.insert_signal(signal)
        assert signal_id == 1

        rows = db.get_signals_by_date(date(2026, 3, 17))
        assert len(rows) == 1
        assert rows[0]["title"] == "owner/name"
        db.close()
    finally:
        os.unlink(db_path)


def test_duplicate_signal_same_day_is_ignored():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        signal = make_signal()
        db.insert_signal(signal)
        db.insert_signal(signal)  # same source_id + date

        rows = db.get_signals_by_date(date(2026, 3, 17))
        assert len(rows) == 1
        db.close()
    finally:
        os.unlink(db_path)


def test_same_signal_different_days():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        db.insert_signal(make_signal(collected_at=date(2026, 3, 17)))
        db.insert_signal(make_signal(collected_at=date(2026, 3, 18)))

        rows_17 = db.get_signals_by_date(date(2026, 3, 17))
        rows_18 = db.get_signals_by_date(date(2026, 3, 18))
        assert len(rows_17) == 1
        assert len(rows_18) == 1
        db.close()
    finally:
        os.unlink(db_path)


def test_insert_and_query_analysis():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        signal = make_signal()
        signal_id = db.insert_signal(signal)
        db.insert_analysis(
            signal_id=signal_id,
            domain="AI/LLM",
            summary="A tokenizer library",
            insight="From Karpathy, educational value",
            trend_status="new_burst",
            rating=3,
        )
        analyses = db.get_analyses_by_date(date(2026, 3, 17))
        assert len(analyses) == 1
        assert analyses[0]["domain"] == "AI/LLM"
        assert analyses[0]["rating"] == 3
        db.close()
    finally:
        os.unlink(db_path)


def test_get_unanalyzed_signals():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        s1_id = db.insert_signal(make_signal(source_id="github:repo:a/a"))
        s2_id = db.insert_signal(make_signal(source_id="github:repo:b/b"))
        db.insert_analysis(
            signal_id=s1_id,
            domain="Web",
            summary="s",
            insight="i",
            trend_status="stable",
            rating=2,
        )
        unanalyzed = db.get_unanalyzed_signals()
        assert len(unanalyzed) == 1
        assert unanalyzed[0]["source_id"] == "github:repo:b/b"
        db.close()
    finally:
        os.unlink(db_path)


def test_get_signals_date_range():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        db.insert_signal(make_signal(source_id="github:repo:a/a", collected_at=date(2026, 3, 15)))
        db.insert_signal(make_signal(source_id="github:repo:b/b", collected_at=date(2026, 3, 16)))
        db.insert_signal(make_signal(source_id="github:repo:c/c", collected_at=date(2026, 3, 17)))

        rows = db.get_signals_date_range(date(2026, 3, 15), date(2026, 3, 16))
        assert len(rows) == 2
        db.close()
    finally:
        os.unlink(db_path)


def test_get_analyses_date_range():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        s1 = db.insert_signal(make_signal(source_id="github:repo:a/a", collected_at=date(2026, 3, 15)))
        s2 = db.insert_signal(make_signal(source_id="github:repo:b/b", collected_at=date(2026, 3, 17)))
        db.insert_analysis(signal_id=s1, domain="AI", summary="s", insight="i", trend_status="rising", rating=2)
        db.insert_analysis(signal_id=s2, domain="Web", summary="s", insight="i", trend_status="new_burst", rating=3)

        analyses = db.get_analyses_date_range(date(2026, 3, 14), date(2026, 3, 16))
        assert len(analyses) == 1
        assert analyses[0]["domain"] == "AI"
        db.close()
    finally:
        os.unlink(db_path)


def test_insert_and_query_report():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.init()
        db.insert_report("daily", "# Report content")
        reports = db.get_reports_by_type("daily")
        assert len(reports) == 1
        assert reports[0]["content"] == "# Report content"
        db.close()
    finally:
        os.unlink(db_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'storage'`

- [ ] **Step 3: Write minimal implementation**

```python
# storage/__init__.py
```

```python
# storage/db.py
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Optional

from crawlers.base import Signal

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY,
    source TEXT,
    source_id TEXT,
    signal_type TEXT,
    title TEXT,
    url TEXT,
    description TEXT,
    metadata JSON,
    raw_content TEXT,
    collected_at DATE,
    UNIQUE(source_id, collected_at)
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id) UNIQUE,
    domain TEXT,
    summary TEXT,
    insight TEXT,
    trend_status TEXT,
    rating INTEGER DEFAULT 1,
    analyzed_at DATETIME
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    report_type TEXT,
    content TEXT,
    generated_at DATETIME
);
"""


class Database:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def init(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def insert_signal(self, signal: Signal) -> Optional[int]:
        try:
            cursor = self.conn.execute(
                """INSERT INTO signals
                   (source, source_id, signal_type, title, url, description,
                    metadata, raw_content, collected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    signal.source,
                    signal.source_id,
                    signal.signal_type,
                    signal.title,
                    signal.url,
                    signal.description,
                    json.dumps(signal.metadata),
                    signal.raw_content,
                    signal.collected_at.isoformat(),
                ),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_signals_by_date(self, d: date) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM signals WHERE collected_at = ?",
            (d.isoformat(),),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_unanalyzed_signals(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT s.* FROM signals s
               LEFT JOIN analyses a ON s.id = a.signal_id
               WHERE a.id IS NULL"""
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_analysis(
        self,
        signal_id: int,
        domain: str,
        summary: str,
        insight: str,
        trend_status: str,
        rating: int = 1,
    ):
        self.conn.execute(
            """INSERT INTO analyses
               (signal_id, domain, summary, insight, trend_status, rating, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (signal_id, domain, summary, insight, trend_status, rating,
             datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def get_analyses_by_date(self, d: date) -> list[dict]:
        rows = self.conn.execute(
            """SELECT a.*, s.title, s.url, s.source, s.source_id,
                      s.signal_type, s.metadata, s.description
               FROM analyses a
               JOIN signals s ON a.signal_id = s.id
               WHERE s.collected_at = ?""",
            (d.isoformat(),),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_signals_date_range(self, start: date, end: date) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM signals WHERE collected_at BETWEEN ? AND ?",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_analyses_date_range(self, start: date, end: date) -> list[dict]:
        rows = self.conn.execute(
            """SELECT a.*, s.title, s.url, s.source, s.source_id,
                      s.signal_type, s.metadata, s.description, s.collected_at
               FROM analyses a
               JOIN signals s ON a.signal_id = s.id
               WHERE s.collected_at BETWEEN ? AND ?""",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_report(self, report_type: str, content: str):
        self.conn.execute(
            """INSERT INTO reports (report_type, content, generated_at)
               VALUES (?, ?, ?)""",
            (report_type, content, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def get_reports_by_type(self, report_type: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM reports WHERE report_type = ? ORDER BY generated_at DESC",
            (report_type,),
        ).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add storage/ tests/test_db.py
git commit -m "feat: add SQLite storage layer with Signal/Analysis/Report CRUD"
```

---

## Chunk 2: Crawlers

### Task 5: HTTP client with retry

**Files:**
- Create: `crawlers/http_client.py`
- Create: `tests/test_http_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_http_client.py
import httpx
import pytest
from unittest.mock import patch, AsyncMock

from crawlers.http_client import fetch, fetch_json


@pytest.mark.asyncio
async def test_fetch_returns_text():
    mock_response = httpx.Response(200, text="<html>hello</html>")
    with patch("crawlers.http_client.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        result = await fetch("https://example.com")
        assert result == "<html>hello</html>"


@pytest.mark.asyncio
async def test_fetch_json_returns_dict():
    mock_response = httpx.Response(200, json={"items": [1, 2]})
    with patch("crawlers.http_client.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        result = await fetch_json("https://api.example.com/data")
        assert result == {"items": [1, 2]}


@pytest.mark.asyncio
async def test_fetch_retries_on_failure():
    fail_response = httpx.Response(500)
    ok_response = httpx.Response(200, text="ok")
    with patch("crawlers.http_client.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get.side_effect = [fail_response, ok_response]
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        result = await fetch("https://example.com", retries=2, backoff=0)
        assert result == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_http_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crawlers.http_client'`

- [ ] **Step 3: Write minimal implementation**

```python
# crawlers/http_client.py
from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def fetch(
    url: str,
    headers: dict | None = None,
    retries: int = 3,
    backoff: float = 1.0,
) -> str:
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for attempt in range(retries):
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
            logger.warning(
                "fetch %s attempt %d: status %d",
                url, attempt + 1, response.status_code,
            )
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
    raise httpx.HTTPStatusError(
        f"Failed after {retries} retries",
        request=response.request,
        response=response,
    )


async def fetch_json(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    retries: int = 3,
    backoff: float = 1.0,
) -> dict:
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for attempt in range(retries):
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "fetch_json %s attempt %d: status %d",
                url, attempt + 1, response.status_code,
            )
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
    raise httpx.HTTPStatusError(
        f"Failed after {retries} retries",
        request=response.request,
        response=response,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_http_client.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add crawlers/http_client.py tests/test_http_client.py
git commit -m "feat: add HTTP client with retry and exponential backoff"
```

---

### Task 6: GitHub Trending crawler

**Files:**
- Create: `crawlers/github_trending.py`
- Create: `tests/test_github_trending.py`
- Create: `tests/fixtures/github_trending.html` (sample HTML)

- [ ] **Step 1: Create sample HTML fixture**

Save a trimmed-down sample of the GitHub Trending page HTML structure to `tests/fixtures/github_trending.html`. The fixture should include 2-3 repo entries with realistic structure (article tags with repo name, description, language, stars).

Run: open `https://github.com/trending` in a browser, inspect the HTML structure of a trending repo entry, and create a minimal fixture.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_github_trending.py
import os
from datetime import date
from unittest.mock import patch, AsyncMock

import pytest

from crawlers.github_trending import crawl_github_trending


@pytest.fixture
def trending_html():
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "github_trending.html"
    )
    with open(fixture_path) as f:
        return f.read()


@pytest.mark.asyncio
async def test_crawl_github_trending(trending_html):
    with patch("crawlers.github_trending.fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = trending_html
        signals = await crawl_github_trending()

    assert len(signals) > 0
    for s in signals:
        assert s.source == "github"
        assert s.signal_type == "trending_repo"
        assert s.source_id.startswith("github:repo:")
        assert s.url.startswith("https://github.com/")
        assert s.collected_at == date.today()


@pytest.mark.asyncio
async def test_crawl_github_trending_validates_dom():
    with patch("crawlers.github_trending.fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = "<html><body>totally different page</body></html>"
        with pytest.raises(ValueError, match="DOM structure"):
            await crawl_github_trending()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_github_trending.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write minimal implementation**

```python
# crawlers/github_trending.py
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
        raise ValueError(
            "DOM structure changed: no 'article.Box-row' found on GitHub Trending page"
        )

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

        signals.append(
            Signal(
                source="github",
                source_id=f"github:repo:{repo_path}",
                signal_type="trending_repo",
                title=repo_path,
                url=f"https://github.com/{repo_path}",
                description=description,
                metadata={
                    "language": language,
                    "stars_today": stars_today,
                },
                raw_content="",  # README fetched separately
                collected_at=today,
            )
        )
    return signals


def parse_trending_developers(html: str) -> list[Signal]:
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.Box-row")
    if not articles:
        raise ValueError(
            "DOM structure changed: no 'article.Box-row' found on GitHub Trending Developers page"
        )

    signals = []
    today = date.today()
    for article in articles:
        name_link = article.select_one("h1.h3 a")
        if not name_link:
            continue
        username = name_link.get("href", "").strip("/")
        display_name = name_link.get_text(strip=True)

        repo_link = article.select_one("h1.h4 a") or article.select_one("article a.css-truncate-target")
        popular_repo = ""
        if repo_link:
            popular_repo = repo_link.get_text(strip=True)

        signals.append(
            Signal(
                source="github",
                source_id=f"github:dev:{username}",
                signal_type="trending_dev",
                title=display_name or username,
                url=f"https://github.com/{username}",
                description=f"Trending developer. Popular repo: {popular_repo}" if popular_repo else "Trending developer",
                metadata={"username": username, "popular_repo": popular_repo},
                raw_content="",
                collected_at=today,
            )
        )
    return signals


def parse_star_count(text: str) -> int:
    text = text.replace(",", "").replace("stars today", "").replace("stars this week", "").strip()
    try:
        return int(text)
    except ValueError:
        return 0
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_github_trending.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add crawlers/github_trending.py tests/test_github_trending.py tests/fixtures/
git commit -m "feat: add GitHub Trending repos and developers crawler"
```

---

### Task 7: GitHub API crawler (Topics + Issues)

**Files:**
- Create: `crawlers/github_api.py`
- Create: `tests/test_github_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_github_api.py
from datetime import date
from unittest.mock import patch, AsyncMock

import pytest

from crawlers.github_api import crawl_github_topics, crawl_github_hot_issues


@pytest.mark.asyncio
async def test_crawl_github_topics():
    mock_response = {
        "items": [
            {
                "full_name": "owner/repo",
                "html_url": "https://github.com/owner/repo",
                "description": "A trending topic project",
                "stargazers_count": 5000,
                "forks_count": 200,
                "language": "Python",
                "topics": ["ai", "llm"],
            }
        ]
    }
    with patch("crawlers.github_api.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = await crawl_github_topics()

    assert len(signals) == 1
    assert signals[0].source == "github"
    assert signals[0].signal_type == "topic"
    assert signals[0].source_id == "github:repo:owner/repo"


@pytest.mark.asyncio
async def test_crawl_github_hot_issues():
    mock_response = {
        "items": [
            {
                "title": "Bug: something broken",
                "html_url": "https://github.com/owner/repo/issues/42",
                "repository_url": "https://api.github.com/repos/owner/repo",
                "reactions": {"+1": 100, "-1": 2, "laugh": 5},
                "comments": 30,
                "labels": [{"name": "bug"}],
            }
        ]
    }
    with patch("crawlers.github_api.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = await crawl_github_hot_issues()

    assert len(signals) == 1
    assert signals[0].signal_type == "hot_issue"
    assert signals[0].source_id == "github:issue:owner/repo#42"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# crawlers/github_api.py
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
        params={
            "q": f"created:>{yesterday} stars:>50",
            "sort": "stars",
            "order": "desc",
            "per_page": 30,
        },
    )

    today = date.today()
    signals = []
    for item in data.get("items", []):
        full_name = item["full_name"]
        signals.append(
            Signal(
                source="github",
                source_id=f"github:repo:{full_name}",
                signal_type="topic",
                title=full_name,
                url=item["html_url"],
                description=item.get("description", "") or "",
                metadata={
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language", ""),
                    "topics": item.get("topics", []),
                },
                raw_content="",
                collected_at=today,
            )
        )
    return signals


async def crawl_github_hot_issues() -> list[Signal]:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    data = await fetch_json(
        f"{API_BASE}/search/issues",
        headers=_github_headers(),
        params={
            "q": f"created:>{yesterday} reactions:>20 is:issue",
            "sort": "reactions-+1",
            "order": "desc",
            "per_page": 30,
        },
    )

    today = date.today()
    signals = []
    for item in data.get("items", []):
        html_url = item["html_url"]
        # Extract owner/repo and issue number from URL
        parts = html_url.replace("https://github.com/", "").split("/")
        if len(parts) >= 4:
            repo_path = f"{parts[0]}/{parts[1]}"
            issue_num = parts[3]
            source_id = f"github:issue:{repo_path}#{issue_num}"
        else:
            source_id = f"github:issue:{html_url}"

        signals.append(
            Signal(
                source="github",
                source_id=source_id,
                signal_type="hot_issue",
                title=item["title"],
                url=html_url,
                description=item["title"],
                metadata={
                    "reactions": item.get("reactions", {}),
                    "comments": item.get("comments", 0),
                    "labels": [l["name"] for l in item.get("labels", [])],
                },
                raw_content="",
                collected_at=today,
            )
        )
    return signals
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_api.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add crawlers/github_api.py tests/test_github_api.py
git commit -m "feat: add GitHub API crawler for topics and hot issues"
```

---

### Task 8: Gitee crawler

**Files:**
- Create: `crawlers/gitee.py`
- Create: `tests/test_gitee.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gitee.py
from datetime import date
from unittest.mock import patch, AsyncMock

import pytest

from crawlers.gitee import crawl_gitee_trending


@pytest.mark.asyncio
async def test_crawl_gitee_trending():
    mock_response = [
        {
            "full_name": "owner/repo",
            "html_url": "https://gitee.com/owner/repo",
            "description": "A Chinese open source project",
            "stargazers_count": 3000,
            "forks_count": 500,
            "language": "Java",
        }
    ]
    with patch("crawlers.gitee.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = await crawl_gitee_trending()

    assert len(signals) == 1
    assert signals[0].source == "gitee"
    assert signals[0].signal_type == "trending_repo"
    assert signals[0].source_id == "gitee:repo:owner/repo"


@pytest.mark.asyncio
async def test_crawl_gitee_trending_fallback_to_search():
    """If trending endpoint fails, fall back to search API."""
    search_response = {
        "data": [
            {
                "full_name": "owner/repo2",
                "html_url": "https://gitee.com/owner/repo2",
                "description": "Fallback project",
                "stargazers_count": 1000,
                "forks_count": 100,
                "language": "Go",
            }
        ]
    }
    with patch("crawlers.gitee.fetch_json", new_callable=AsyncMock) as mock:
        mock.side_effect = [Exception("404"), search_response]
        signals = await crawl_gitee_trending()

    assert len(signals) == 1
    assert signals[0].source == "gitee"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_gitee.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# crawlers/gitee.py
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
    return await fetch_json(
        f"{GITEE_API}/projects/trending",
        params=params,
    )


async def _fallback_search() -> list[dict]:
    params = {
        "sort": "stars_count",
        "order": "desc",
        "per_page": 30,
        "page": 1,
    }
    if config.GITEE_TOKEN:
        params["access_token"] = config.GITEE_TOKEN
    result = await fetch_json(
        f"{GITEE_API}/search/repositories",
        params=params,
    )
    if isinstance(result, dict):
        return result.get("data", result.get("items", []))
    return result


def _parse_repos(data: list[dict]) -> list[Signal]:
    today = date.today()
    signals = []
    for item in data:
        full_name = item.get("full_name", "")
        signals.append(
            Signal(
                source="gitee",
                source_id=f"gitee:repo:{full_name}",
                signal_type="trending_repo",
                title=full_name,
                url=item.get("html_url", ""),
                description=item.get("description", "") or "",
                metadata={
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language", ""),
                },
                raw_content="",
                collected_at=today,
            )
        )
    return signals
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_gitee.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add crawlers/gitee.py tests/test_gitee.py
git commit -m "feat: add Gitee crawler with search API fallback"
```

---

### Task 9: README fetcher

**Files:**
- Create: `crawlers/readme_fetcher.py`
- Create: `tests/test_readme_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_readme_fetcher.py
import base64
from unittest.mock import patch, AsyncMock

import pytest

from crawlers.readme_fetcher import fetch_readme_for_signals
from crawlers.base import Signal
from datetime import date


def make_signal(source_id="github:repo:owner/name", source="github"):
    return Signal(
        source=source,
        source_id=source_id,
        signal_type="trending_repo",
        title="owner/name",
        url=f"https://{source}.com/owner/name",
        description="desc",
        metadata={},
        raw_content="",
        collected_at=date.today(),
    )


@pytest.mark.asyncio
async def test_fetch_readme_for_github_signal():
    readme_content = base64.b64encode(b"# My Project\nThis is cool.").decode()
    mock_response = {"content": readme_content, "encoding": "base64"}

    with patch("crawlers.readme_fetcher.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = [make_signal()]
        updated = await fetch_readme_for_signals(signals)

    assert updated[0].raw_content == "# My Project\nThis is cool."


@pytest.mark.asyncio
async def test_fetch_readme_truncates_long_content():
    long_readme = "x" * 5000
    readme_content = base64.b64encode(long_readme.encode()).decode()
    mock_response = {"content": readme_content, "encoding": "base64"}

    with patch("crawlers.readme_fetcher.fetch_json", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        signals = [make_signal()]
        updated = await fetch_readme_for_signals(signals)

    assert len(updated[0].raw_content) == 3000


@pytest.mark.asyncio
async def test_fetch_readme_failure_leaves_empty():
    with patch("crawlers.readme_fetcher.fetch_json", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("404")
        signals = [make_signal()]
        updated = await fetch_readme_for_signals(signals)

    assert updated[0].raw_content == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_readme_fetcher.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# crawlers/readme_fetcher.py
from __future__ import annotations

import asyncio
import base64
import logging

import config
from crawlers.base import Signal, MAX_RAW_CONTENT_LENGTH
from crawlers.http_client import fetch_json

logger = logging.getLogger(__name__)


REQUEST_DELAY = 1.0  # seconds between requests to avoid rate limiting
_semaphore = asyncio.Semaphore(3)  # max 3 concurrent README fetches


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
        content = await _fetch_github_readme(repo_path)
        signal.raw_content = content[:MAX_RAW_CONTENT_LENGTH]
    elif signal.source == "gitee" and signal.signal_type == "trending_repo":
        repo_path = signal.source_id.replace("gitee:repo:", "")
        content = await _fetch_gitee_readme(repo_path)
        signal.raw_content = content[:MAX_RAW_CONTENT_LENGTH]
    return signal


async def _fetch_github_readme(repo_path: str) -> str:
    try:
        headers = {"Accept": "application/vnd.github+json"}
        if config.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
        data = await fetch_json(
            f"https://api.github.com/repos/{repo_path}/readme",
            headers=headers,
        )
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
        data = await fetch_json(
            f"https://gitee.com/api/v5/repos/{owner}/{repo}/readme",
            params=params,
        )
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64" and content:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        return content
    except Exception as e:
        logger.warning("Failed to fetch Gitee README for %s: %s", repo_path, e)
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_readme_fetcher.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add crawlers/readme_fetcher.py tests/test_readme_fetcher.py
git commit -m "feat: add README fetcher for GitHub and Gitee repos"
```

---

## Chunk 3: LLM Analysis

### Task 10: LLM client wrapper

**Files:**
- Create: `analyzer/__init__.py`
- Create: `analyzer/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py
from unittest.mock import patch, MagicMock

import pytest

from analyzer.llm import call_llm


@pytest.mark.asyncio
async def test_call_llm_returns_text():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="LLM response text")]
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("analyzer.llm.get_client", return_value=mock_client):
        result = await call_llm("test prompt", model="claude-haiku-4-5-20251001")

    assert result == "LLM response text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# analyzer/__init__.py
```

```python
# analyzer/llm.py
from __future__ import annotations

import logging

import anthropic

import config

logger = logging.getLogger(__name__)

_client = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


async def call_llm(
    prompt: str,
    model: str | None = None,
    system: str = "",
    max_tokens: int = 4096,
) -> str:
    client = get_client()
    model = model or config.LLM_MODEL_DAILY
    messages = [{"role": "user", "content": prompt}]

    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    if system:
        kwargs["system"] = system

    response = await client.messages.create(**kwargs)
    return response.content[0].text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_llm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analyzer/ tests/test_llm.py
git commit -m "feat: add LLM client wrapper for Claude API"
```

---

### Task 11: Prompt files

**Files:**
- Create: `prompts/classify.md`
- Create: `prompts/analyze.md`
- Create: `prompts/daily_overview.md`
- Create: `prompts/weekly_report.md`
- Create: `analyzer/prompts.py`
- Create: `tests/test_prompts.py`

- [ ] **Step 1: Create prompt files**

```markdown
<!-- prompts/classify.md -->
You are a technology trend analyst. Given a list of software projects, classify each into a technology domain.

Rules:
- Use dynamic domain names (e.g., "AI/LLM", "Web Frontend", "Database/Storage", "DevOps", "Programming Languages", "Security", etc.)
- Each project gets exactly one domain
- Return valid JSON array

Input projects:
{projects}

Return JSON:
[{{"source_id": "...", "domain": "..."}}, ...]
```

```markdown
<!-- prompts/analyze.md -->
You are a technology trend analyst. Analyze this open-source project and provide a concise assessment.

Project: {title}
URL: {url}
Description: {description}
Language: {language}
Stars today: {stars_today}
README (first 3000 chars):
{raw_content}

Provide your analysis as JSON:
{{
  "summary": "One sentence: what this project is and what problem it solves",
  "insight": "One sentence: why it's worth attention — author background, how it differs from alternatives, or what trend it represents",
  "trend_status": "new_burst | rising | sustained | resurgence",
  "rating": 3
}}

rating: 1=routine trending, 2=worth knowing, 3=strongly recommend
trend_status: new_burst=new project exploding, rising=growing steadily, sustained=consistently popular, resurgence=old project trending again
```

```markdown
<!-- prompts/daily_overview.md -->
You are a technology trend analyst writing a daily briefing in Chinese.

Below are today's trending projects, grouped by domain, with analyses:

{analyses}

Write a concise overview paragraph (2-4 sentences) that captures:
- Which domains are most active today
- Any notable patterns (e.g., multiple AI projects, a new language gaining traction)
- One highlight worth calling out

Write in Chinese. Be specific, not generic. Reference actual project names.
```

```markdown
<!-- prompts/weekly_report.md -->
You are a technology trend analyst writing a weekly report in Chinese.

Below are the past 7 days of trending data with analyses:

{weekly_data}

Generate a weekly report with these sections (in Chinese):

1. **本周全景** — 2-3 sentence overview of the week
2. **持续霸榜** — Projects that appeared 3+ days. For each: why it's sustained, not just a spike
3. **新兴信号** — New patterns: multiple projects in same domain appearing, a technology direction gaining momentum
4. **领域热度排行** — Rank domains by number of trending projects, use bar visualization
5. **退热项目** — Projects that were hot last week but disappeared this week

Be specific. Use project names. Provide insight, not just lists.
```

- [ ] **Step 2: Write prompt loader and failing test**

```python
# tests/test_prompts.py
from analyzer.prompts import load_prompt


def test_load_prompt_classify():
    prompt = load_prompt("classify", projects="[test]")
    assert "[test]" in prompt
    assert "technology domain" in prompt


def test_load_prompt_analyze():
    prompt = load_prompt("analyze", title="test/repo", url="http://test",
                         description="desc", language="Python",
                         stars_today="100", raw_content="readme")
    assert "test/repo" in prompt
    assert "Python" in prompt
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: FAIL

- [ ] **Step 4: Write implementation**

```python
# analyzer/prompts.py
from __future__ import annotations

import os

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


def load_prompt(name: str, **kwargs) -> str:
    path = os.path.join(PROMPTS_DIR, f"{name}.md")
    with open(path) as f:
        template = f.read()
    return template.format(**kwargs)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add prompts/ analyzer/prompts.py tests/test_prompts.py
git commit -m "feat: add prompt templates and loader for LLM analysis"
```

---

### Task 12: Classifier and per-item analyzer

**Files:**
- Create: `analyzer/classifier.py`
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_classifier.py
import json
from unittest.mock import patch, AsyncMock

import pytest

from analyzer.classifier import classify_signals, analyze_signal


@pytest.mark.asyncio
async def test_classify_signals():
    mock_llm_response = json.dumps([
        {"source_id": "github:repo:owner/ai-tool", "domain": "AI/LLM"},
        {"source_id": "github:repo:owner/web-fw", "domain": "Web Frontend"},
    ])
    with patch("analyzer.classifier.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = mock_llm_response
        result = await classify_signals([
            {"source_id": "github:repo:owner/ai-tool", "title": "ai-tool", "description": "AI thing"},
            {"source_id": "github:repo:owner/web-fw", "title": "web-fw", "description": "Web thing"},
        ])

    assert result["github:repo:owner/ai-tool"] == "AI/LLM"
    assert result["github:repo:owner/web-fw"] == "Web Frontend"


@pytest.mark.asyncio
async def test_analyze_signal():
    mock_llm_response = json.dumps({
        "summary": "A tokenizer library",
        "insight": "From Karpathy, educational",
        "trend_status": "new_burst",
        "rating": 3,
    })
    with patch("analyzer.classifier.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = mock_llm_response
        result = await analyze_signal({
            "title": "owner/repo",
            "url": "https://github.com/owner/repo",
            "description": "desc",
            "metadata": '{"language": "Python", "stars_today": 500}',
            "raw_content": "# README",
        })

    assert result["summary"] == "A tokenizer library"
    assert result["trend_status"] == "new_burst"
    assert result["rating"] == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_classifier.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# analyzer/classifier.py
from __future__ import annotations

import json
import logging

from analyzer.llm import call_llm
from analyzer.prompts import load_prompt

logger = logging.getLogger(__name__)


async def classify_signals(signals: list[dict]) -> dict[str, str]:
    projects_text = json.dumps(
        [{"source_id": s["source_id"], "title": s["title"],
          "description": s.get("description", "")}
         for s in signals],
        ensure_ascii=False,
    )
    response = await call_llm(load_prompt("classify", projects=projects_text))

    try:
        classifications = json.loads(response)
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
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse analysis response: %s", e)
        return {
            "summary": signal.get("description", ""),
            "insight": "",
            "trend_status": "unknown",
            "rating": 1,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_classifier.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analyzer/classifier.py tests/test_classifier.py
git commit -m "feat: add LLM-based classifier and per-signal analyzer"
```

---

## Chunk 4: Reports and Notifications

### Task 13: Report generator

**Files:**
- Create: `analyzer/reporter.py`
- Create: `tests/test_reporter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reporter.py
from unittest.mock import patch, AsyncMock

import pytest

from analyzer.reporter import generate_daily_report, generate_weekly_report, format_daily_telegram


@pytest.mark.asyncio
async def test_generate_daily_report():
    analyses = [
        {
            "title": "owner/ai-tool", "url": "https://github.com/owner/ai-tool",
            "domain": "AI/LLM", "summary": "An AI tool", "insight": "Very useful",
            "trend_status": "new_burst", "source": "github",
            "metadata": '{"language": "Python", "stars_today": 500}',
            "signal_type": "trending_repo", "description": "AI tool desc",
        },
        {
            "title": "owner/web-fw", "url": "https://github.com/owner/web-fw",
            "domain": "Web", "summary": "A web framework", "insight": "Fast",
            "trend_status": "rising", "source": "github",
            "metadata": '{"language": "TypeScript", "stars_today": 200}',
            "signal_type": "trending_repo", "description": "Web fw desc",
        },
    ]
    with patch("analyzer.reporter.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = "今天 AI 领域有一个新项目爆发..."
        report = await generate_daily_report(analyses)

    assert "今天 AI 领域" in report
    assert "AI/LLM" in report
    assert "owner/ai-tool" in report


@pytest.mark.asyncio
async def test_generate_weekly_report():
    weekly_analyses = [
        {
            "title": "owner/proj", "url": "https://github.com/owner/proj",
            "domain": "AI/LLM", "summary": "An AI project", "insight": "Notable",
            "trend_status": "sustained", "source": "github", "collected_at": "2026-03-15",
            "metadata": '{"language": "Python"}', "signal_type": "trending_repo",
            "description": "desc",
        },
    ]
    with patch("analyzer.reporter.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = "本周 AI 领域持续活跃..."
        report = await generate_weekly_report(weekly_analyses)

    assert "本周" in report


def test_format_daily_telegram():
    report = "# Daily Report\n\nSome content here"
    messages = format_daily_telegram(report)
    assert len(messages) >= 1
    assert isinstance(messages[0], str)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reporter.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# analyzer/reporter.py
from __future__ import annotations

import json
import logging
from itertools import groupby

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

    # Sort domains by count descending
    sorted_domains = sorted(grouped.items(), key=lambda x: -len(x[1]))

    # Build analyses text for LLM overview
    analyses_text = _format_analyses_for_llm(sorted_domains)

    # Generate overview paragraph
    overview = await call_llm(
        load_prompt("daily_overview", analyses=analyses_text),
        model=config.LLM_MODEL_DAILY,
    )

    # Build full report
    lines = []
    lines.append("\U0001f4ca <b>Technology Daily Report</b>\n")
    lines.append(f"{overview}\n")
    lines.append("\u2501" * 20 + "\n")

    for domain, items in sorted_domains:
        lines.append(f"\n<b>{domain}</b>({len(items)})\n")
        for item in sorted(items, key=lambda x: -_get_rating(x)):
            metadata = item.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
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
        # Find a good split point
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
    metadata = analysis.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    # Rating may be in analysis directly or default to 1
    return analysis.get("rating", 1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reporter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analyzer/reporter.py tests/test_reporter.py
git commit -m "feat: add daily/weekly report generator with Telegram formatting"
```

---

### Task 14: Telegram notification

**Files:**
- Create: `notify/__init__.py`
- Create: `notify/telegram.py`
- Create: `tests/test_telegram.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_telegram.py
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from notify.telegram import send_report, send_alert


@pytest.mark.asyncio
async def test_send_report_single_message():
    with patch("notify.telegram.Bot") as MockBot:
        mock_bot = AsyncMock()
        MockBot.return_value = mock_bot

        await send_report("Short report")

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["text"] == "Short report"
        assert call_kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_send_report_splits_long_message():
    long_report = "Line\n" * 1000  # > 4096 chars
    with patch("notify.telegram.Bot") as MockBot:
        mock_bot = AsyncMock()
        MockBot.return_value = mock_bot

        await send_report(long_report)

        assert mock_bot.send_message.call_count > 1


@pytest.mark.asyncio
async def test_send_alert():
    with patch("notify.telegram.Bot") as MockBot:
        mock_bot = AsyncMock()
        MockBot.return_value = mock_bot

        await send_alert("Something broke!")

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "Alert" in call_kwargs["text"]
        assert "Something broke!" in call_kwargs["text"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_telegram.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# notify/__init__.py
```

```python
# notify/telegram.py
from __future__ import annotations

import logging

from telegram import Bot

import config
from analyzer.reporter import format_daily_telegram

logger = logging.getLogger(__name__)


async def send_report(report: str):
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    chat_id = config.TELEGRAM_CHAT_ID
    messages = format_daily_telegram(report)

    for msg in messages:
        await bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    logger.info("Sent %d message(s) to Telegram", len(messages))


async def send_alert(text: str):
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=f"\u26a0\ufe0f <b>Alert</b>\n\n{text}",
        parse_mode="HTML",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_telegram.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add notify/ tests/test_telegram.py
git commit -m "feat: add Telegram notification with message splitting"
```

---

## Chunk 5: Pipeline and Deployment

### Task 15: Main pipeline orchestrator

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_main.py
import argparse
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date

import pytest

from main import run_daily, run_weekly


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# main.py
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
            # DOM structure change — send immediate alert
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
        # Replace in all_signals
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
        # Classify
        try:
            domains = await classify_signals(unanalyzed)
        except Exception as e:
            logger.error("Classification failed: %s", e)
            domains = {}

        # Per-item analysis
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

        # Phase 6: Send
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_main.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main pipeline orchestrator with daily/weekly commands"
```

---

### Task 16: GitHub Actions workflows

**Files:**
- Create: `.github/workflows/daily.yml`
- Create: `.github/workflows/weekly.yml`

- [ ] **Step 1: Create daily workflow**

```yaml
# .github/workflows/daily.yml
name: Daily Trending

on:
  schedule:
    - cron: '0 0 * * *'  # UTC 0:00 = Beijing 8:00
  workflow_dispatch:  # Allow manual trigger

jobs:
  daily:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Create data directory
        run: mkdir -p data

      - name: Download database from latest release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release download latest --pattern "trending.db" --dir data/ || echo "No existing database found, starting fresh"

      - name: Run daily pipeline
        env:
          GITHUB_TOKEN: ${{ secrets.GH_PAT }}
          GITEE_TOKEN: ${{ secrets.GITEE_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python main.py daily

      - name: Upload database to release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release delete latest --yes || true
          gh release create latest data/trending.db --title "Latest Database" --notes "Auto-updated by daily pipeline"

      - name: Alert on failure
        if: failure()
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python -c "
          import asyncio
          from notify.telegram import send_alert
          asyncio.run(send_alert('Daily pipeline failed! Check GitHub Actions logs.'))
          "
```

- [ ] **Step 2: Create weekly workflow**

```yaml
# .github/workflows/weekly.yml
name: Weekly Report

on:
  schedule:
    - cron: '0 0 * * 1'  # UTC 0:00 every Monday = Beijing 8:00 Monday
  workflow_dispatch:

jobs:
  weekly:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Create data directory
        run: mkdir -p data

      - name: Download database from latest release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release download latest --pattern "trending.db" --dir data/ || echo "No database found"

      - name: Run weekly report
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python main.py weekly

      - name: Upload database to release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release delete latest --yes || true
          gh release create latest data/trending.db --title "Latest Database" --notes "Auto-updated by weekly pipeline"

      - name: Alert on failure
        if: failure()
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python -c "
          import asyncio
          from notify.telegram import send_alert
          asyncio.run(send_alert('Weekly report pipeline failed! Check GitHub Actions logs.'))
          "
```

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Actions workflows for daily and weekly pipelines"
```

---

### Task 17: End-to-end dry-run test

**Files:** None (uses existing code)

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run dry-run locally**

Run: `python main.py daily --dry-run`
Expected: Pipeline runs through all phases, prints report to stdout, no Telegram send.

- [ ] **Step 3: Fix any issues found during dry-run**

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final adjustments after end-to-end dry-run"
```

---

## Setup Checklist (Post-Implementation)

Before the first real run, configure these GitHub Secrets:

- [ ] `GH_PAT` — GitHub Personal Access Token (for API rate limits)
- [ ] `GITEE_TOKEN` — Gitee API token
- [ ] `ANTHROPIC_API_KEY` — Claude API key
- [ ] `TELEGRAM_BOT_TOKEN` — Create bot via @BotFather
- [ ] `TELEGRAM_CHAT_ID` — Your chat/group ID (message @userinfobot to get it)
