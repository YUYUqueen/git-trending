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
