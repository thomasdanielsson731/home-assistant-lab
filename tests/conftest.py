"""Shared pytest fixtures for Danielsson Insights scripts."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from event_store import EventStore, TZ  # noqa: E402


@pytest.fixture
def events_dir(tmp_path: Path) -> Path:
    return tmp_path / "events"


@pytest.fixture
def store(events_dir: Path) -> EventStore:
    return EventStore(events_root=events_dir)


@pytest.fixture
def person_event() -> dict:
    ts = datetime(2026, 6, 6, 14, 0, 0, tzinfo=TZ)
    return {
        "timestamp": ts.isoformat(),
        "type": "person",
        "location": {"zone": "front", "camera": "front"},
        "identity": {},
        "metadata": {},
        "source": "test",
    }


@pytest.fixture
def normalizer(monkeypatch, store: EventStore):
    """Import event_normalizer with isolated store and no MQTT credentials required."""
    import importlib

    monkeypatch.setenv("MQTT_USER", "test")
    monkeypatch.setenv("MQTT_PASS", "test")
    import event_normalizer

    importlib.reload(event_normalizer)
    event_normalizer.store = store
    event_normalizer.reset_env_state()
    return event_normalizer
