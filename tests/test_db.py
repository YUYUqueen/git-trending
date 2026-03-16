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
        db.insert_signal(signal)
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
            signal_id=s1_id, domain="Web", summary="s", insight="i",
            trend_status="stable", rating=2,
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
