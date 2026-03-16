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
