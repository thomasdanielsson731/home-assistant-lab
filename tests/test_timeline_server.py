"""Tests for scripts/timeline_server.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from urllib.parse import quote

import pytest

from event_store import TZ
from timeline_server import Handler, HTTPServer, load_events, PORT


@pytest.fixture
def timeline_file(tmp_path: Path) -> Path:
    path = tmp_path / "timeline.jsonl"
    now = datetime.now(TZ)
    old = now - timedelta(days=10)
    events = [
        {
            "timestamp": now.isoformat(),
            "type": "person",
            "location": {"zone": "front", "camera": "front"},
            "summary": "Person detected at front",
            "event_id": "evt_recent",
            "source": "frigate",
        },
        {
            "timestamp": old.isoformat(),
            "type": "vehicle",
            "location": {"zone": "driveway", "camera": "driveway_wide"},
            "summary": "Vehicle at driveway",
            "event_id": "evt_old",
            "source": "frigate",
        },
        {
            "timestamp": now.isoformat(),
            "type": "environment",
            "location": {"zone": "driveway_env"},
            "summary": "Air · 18°C CO₂ 400",
            "event_id": "evt_env",
            "source": "d6210",
        },
    ]
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return path


class TestLoadEvents:
    def test_returns_recent_within_hours(self, timeline_file: Path):
        events = load_events(hours=24, timeline_path=timeline_file)
        ids = {e["event_id"] for e in events}
        assert "evt_recent" in ids
        assert "evt_env" in ids
        assert "evt_old" not in ids

    def test_filters_by_type(self, timeline_file: Path):
        events = load_events(hours=24, event_type="person", timeline_path=timeline_file)
        assert len(events) == 1
        assert events[0]["type"] == "person"

    def test_missing_file_returns_empty(self, tmp_path: Path):
        assert load_events(timeline_path=tmp_path / "missing.jsonl") == []

    def test_skips_malformed_lines(self, tmp_path: Path):
        path = tmp_path / "timeline.jsonl"
        now = datetime.now(TZ).isoformat()
        path.write_text(f"{{broken\n{json.dumps({'timestamp': now, 'type': 'person', 'event_id': 'ok'})}\n")
        events = load_events(hours=24, timeline_path=path)
        assert len(events) == 1
        assert events[0]["event_id"] == "ok"

    def test_sorts_newest_first(self, timeline_file: Path):
        events = load_events(hours=168, timeline_path=timeline_file)
        timestamps = [e["timestamp"] for e in events]
        assert timestamps == sorted(timestamps, reverse=True)


class TestTimelineHTTP:
    @pytest.fixture
    def server(self, timeline_file: Path, monkeypatch):
        monkeypatch.setattr("timeline_server.TIMELINE_JSONL", timeline_file)
        srv = HTTPServer(("127.0.0.1", 0), Handler)
        port = srv.server_address[1]
        thread = Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        yield port
        srv.shutdown()

    def test_api_events_json(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/events?hours=24")
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert isinstance(data, list)
        assert any(e["type"] == "person" for e in data)

    def test_html_index(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/")
        resp = conn.getresponse()
        body = resp.read().decode()
        assert resp.status == 200
        assert "Danielsson Insights" in body
        assert "Person detected at front" in body

    def test_html_type_filter(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/?type=environment")
        body = conn.getresponse().read().decode()
        assert "Air ·" in body
        assert "Vehicle at driveway" not in body

    def test_timeline_v1_page(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/timeline")
        body = conn.getresponse().read().decode()
        assert "Analytics" in body

    def test_environment_page(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/environment")
        resp = conn.getresponse()
        body = resp.read().decode()
        assert resp.status == 200
        assert "Environment" in body
        assert "chart-climate" in body
        assert 'data-hours="168"' in body

    def test_api_v1_occupancy(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/occupancy?hours=24")
        resp = conn.getresponse()
        assert resp.status == 200
        assert isinstance(json.loads(resp.read().decode()), list)

    def test_api_v1_events_custom_range(self, server):
        now = datetime.now(TZ)
        since = (now - timedelta(hours=1)).isoformat()
        until = (now + timedelta(minutes=1)).isoformat()
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", f"/api/v1/events?from={quote(since)}&to={quote(until)}")
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert any(e["event_id"] == "evt_recent" for e in data)

    def test_timeline_v1_has_zoom_controls(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/timeline")
        body = conn.getresponse().read().decode()
        assert "goto-now" in body       # Go to now button
        assert "zoom-reset" in body     # Reset button
        assert "from-input" in body
        assert "bicycle" in body
        assert "15 m" in body           # 15-minute range button

    def test_story_page_returns_html(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/story")
        resp = conn.getresponse()
        body = resp.read().decode()
        assert resp.status == 200
        assert "House Story" in body

    def test_story_today_endpoint(self, server, tmp_path, monkeypatch):
        import story_engine
        import timeline_server
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        monkeypatch.setattr(story_engine, "STORIES_DIR", stories_dir)
        monkeypatch.setattr(timeline_server, "STORIES_DIR", stories_dir)
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/story/today")
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "beats" in data
        assert "date" in data

    def test_story_date_endpoint_returns_cached(self, server, tmp_path, monkeypatch):
        import timeline_server
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        monkeypatch.setattr(timeline_server, "STORIES_DIR", stories_dir)
        cached = {
            "date": "2026-06-06",
            "generated_at": "2026-06-06T00:00:00+02:00",
            "title": "Friday 6 June",
            "summary": "A quiet day.",
            "beats": [],
            "stats": {},
        }
        (stories_dir / "2026-06-06.json").write_text(
            json.dumps(cached), encoding="utf-8"
        )
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/story/2026-06-06")
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["title"] == "Friday 6 June"

    def test_story_week_endpoint(self, server, tmp_path, monkeypatch):
        import timeline_server
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        monkeypatch.setattr(timeline_server, "STORIES_DIR", stories_dir)
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/story/week")
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert isinstance(data, list)

    def test_api_v1_metrics(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/metrics?hours=24")
        resp = conn.getresponse()
        assert resp.status == 200
        assert isinstance(json.loads(resp.read().decode()), list)

    def test_story_invalid_date_returns_400(self, server):
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/story/not-a-date")
        resp = conn.getresponse()
        resp.read()
        assert resp.status == 400

    def test_story_date_generates_when_no_cache(self, server, tmp_path, monkeypatch):
        import story_engine
        import timeline_server
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        monkeypatch.setattr(story_engine, "STORIES_DIR", stories_dir)
        monkeypatch.setattr(timeline_server, "STORIES_DIR", stories_dir)
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/api/v1/story/2026-06-06")
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "beats" in data

    def test_html_index_high_hours(self, server):
        # hits "Senaste {hours}h" branch (hours > 168)
        conn = HTTPConnection("127.0.0.1", server)
        conn.request("GET", "/?hours=200")
        resp = conn.getresponse()
        body = resp.read().decode()
        assert resp.status == 200
        # float renders as "200.0h" or similar — just check "200" appears and not the 7-day label
        assert "200" in body
        assert "7 dagarna" not in body
