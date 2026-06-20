"""Regression tests for HA Ingress-safe Analytics / Environment / Story pages."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread

import pytest

from environment_page import ENVIRONMENT_HTML
from event_store import TZ
from insights_paths import INSIGHTS_BASE_SCRIPT
from insights_test_helpers import (
    REQUIRED_RELATIVE_FETCHES,
    assert_ingress_safe_html,
    assert_relative_api_fetches,
)
from timeline_server import (
    ENVIRONMENT_HTML as SERVER_ENV_HTML,
    STORY_HTML,
    TIMELINE_V1_HTML,
    Handler,
    HTTPServer,
    _insights_page,
)


class TestInsightsBaseScript:
    def test_covers_all_insights_pages(self):
        for page in ("timeline", "environment", "story"):
            assert f"'{page}'" in INSIGHTS_BASE_SCRIPT

    def test_inserts_base_before_other_head_content(self):
        assert "document.head.insertBefore(b, document.head.firstChild)" in INSIGHTS_BASE_SCRIPT

    def test_uses_last_index_of_page_suffix(self):
        assert "lastIndexOf(needle)" in INSIGHTS_BASE_SCRIPT

    def test_root_timeline_path_uses_site_base(self):
        assert "idx >= 0" in INSIGHTS_BASE_SCRIPT
        assert "idx === 0 ? '/'" in INSIGHTS_BASE_SCRIPT

    def test_root_event_list_gets_base_href(self):
        assert "p.endsWith('/')" in INSIGHTS_BASE_SCRIPT


class TestInsightsPageHelper:
    @pytest.mark.parametrize(
        "template",
        [TIMELINE_V1_HTML, ENVIRONMENT_HTML, STORY_HTML],
        ids=["timeline", "environment", "story"],
    )
    def test_replaces_placeholder_with_script(self, template: str):
        served = _insights_page(template).decode("utf-8")
        assert "__INSIGHTS_BASE__" not in served
        assert INSIGHTS_BASE_SCRIPT in served
        assert served.index(INSIGHTS_BASE_SCRIPT) < served.index("<meta charset")

    def test_idempotent_when_already_served(self):
        once = _insights_page(TIMELINE_V1_HTML).decode("utf-8")
        # Placeholder already gone — second pass must not duplicate script.
        assert once.count("__INSIGHTS_BASE__") == 0
        assert once.count("document.createElement('base')") >= 1


class TestIngressSafeTemplates:
    @pytest.mark.parametrize(
        ("name", "html", "api_endpoints"),
        [
            ("timeline", TIMELINE_V1_HTML, ("api/v1/events", "api/v1/occupancy", "api/v1/metrics")),
            ("environment", ENVIRONMENT_HTML, ("api/v1/metrics",)),
            ("story", STORY_HTML, ("api/v1/story/today",)),
        ],
        ids=["timeline", "environment", "story"],
    )
    def test_templates_avoid_absolute_client_paths(self, name, html, api_endpoints):
        assert_ingress_safe_html(html, served=False)
        assert_relative_api_fetches(html, *api_endpoints)

    @pytest.mark.parametrize(
        ("name", "html"),
        [
            ("timeline", TIMELINE_V1_HTML),
            ("environment", ENVIRONMENT_HTML),
            ("story", STORY_HTML),
        ],
        ids=["timeline", "environment", "story"],
    )
    def test_templates_use_relative_static_and_nav(self, name, html):
        if name == "environment":
            assert 'src="static/chart.umd.min.js"' in html
            assert 'href="timeline"' in html
        if name == "timeline":
            assert 'href="story"' in html
            assert "media/${snap}" in html or 'src="media/' in html


@pytest.fixture
def insights_server(tmp_path: Path, monkeypatch):
    timeline = tmp_path / "timeline.jsonl"
    now = datetime.now(TZ).isoformat()
    timeline.write_text(
        json.dumps(
            {
                "timestamp": now,
                "type": "person",
                "location": {"zone": "front", "camera": "front"},
                "summary": "Ingress test event",
                "event_id": "evt_ingress",
                "source": "frigate",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("timeline_server.TIMELINE_JSONL", timeline)
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    thread = Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield port
    srv.shutdown()


class TestIngressSafeHTTP:
    @pytest.mark.parametrize("path", ["/timeline", "/environment", "/story"])
    def test_served_pages_inject_base_script(self, insights_server, path):
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert_ingress_safe_html(body, served=True)

    @pytest.mark.parametrize(
        ("path", "api_endpoints"),
        [
            ("/timeline", REQUIRED_RELATIVE_FETCHES),
            ("/environment", ("api/v1/metrics",)),
            ("/story", ("api/v1/story/today",)),
        ],
    )
    def test_served_pages_use_relative_api_paths(self, insights_server, path, api_endpoints):
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", path)
        body = conn.getresponse().read().decode("utf-8")
        assert_relative_api_fetches(body, *api_endpoints)

    def test_environment_served_page_loads_chart_js_relatively(self, insights_server):
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", "/environment")
        body = conn.getresponse().read().decode("utf-8")
        assert 'src="static/chart.umd.min.js"' in body
        assert 'src="static/chartjs-adapter-date-fns.bundle.min.js"' in body

    @pytest.mark.parametrize(
        "api_path",
        [
            "/api/v1/events?hours=24",
            "/api/v1/metrics?hours=24",
            "/api/v1/occupancy?hours=24",
        ],
    )
    def test_server_api_still_on_absolute_paths(self, insights_server, api_path):
        """Relative browser fetches resolve to these routes on timeline_server."""
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", api_path)
        resp = conn.getresponse()
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert isinstance(data, list)

    def test_static_assets_served_at_absolute_path(self, insights_server):
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", "/static/chart.umd.min.js")
        resp = conn.getresponse()
        body = resp.read()
        assert resp.status == 200
        assert len(body) > 100_000

    def test_health_endpoint(self, insights_server):
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert data.get("ok") is True

    def test_html_responses_disable_cache(self, insights_server):
        conn = HTTPConnection("127.0.0.1", insights_server)
        conn.request("GET", "/timeline")
        resp = conn.getresponse()
        resp.read()
        assert resp.getheader("Cache-Control") == "no-cache, no-store, must-revalidate"
        csp = resp.getheader("Content-Security-Policy") or ""
        assert "frame-ancestors" in csp
        assert "ha.danielsson.cloud" in csp
        assert "https://192.168.68.175:8123" in csp

    def test_timeline_and_environment_templates_match_imports(self):
        assert ENVIRONMENT_HTML == SERVER_ENV_HTML
