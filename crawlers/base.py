from __future__ import annotations

from dataclasses import dataclass
from datetime import date


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
