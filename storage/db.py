from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
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
                    signal.source, signal.source_id, signal.signal_type,
                    signal.title, signal.url, signal.description,
                    json.dumps(signal.metadata), signal.raw_content,
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
             datetime.now(timezone.utc).isoformat()),
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
            (report_type, content, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def get_reports_by_type(self, report_type: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM reports WHERE report_type = ? ORDER BY generated_at DESC",
            (report_type,),
        ).fetchall()
        return [dict(r) for r in rows]
