"""Tests for scripts/environment_page.py embedded UI."""

from __future__ import annotations

from environment_page import ENVIRONMENT_HTML


class TestEnvironmentPageHtml:
    def test_includes_chart_series_and_toolbar(self):
        assert "chart-climate" in ENVIRONMENT_HTML
        assert "chart-air" in ENVIRONMENT_HTML
        assert "chart-spl" in ENVIRONMENT_HTML
        assert 'data-hours="168"' in ENVIRONMENT_HTML
        assert "driveway_env:temperature" in ENVIRONMENT_HTML
        assert "front:spl" in ENVIRONMENT_HTML

    def test_includes_error_handling_and_nav(self):
        assert "Cannot load metrics" in ENVIRONMENT_HTML
        assert "start-bridges.ps1" in ENVIRONMENT_HTML
        assert 'href="/timeline"' in ENVIRONMENT_HTML
        assert "/api/v1/metrics" in ENVIRONMENT_HTML

    def test_uses_local_chart_js_not_cdn(self):
        assert "/static/chart.umd.min.js" in ENVIRONMENT_HTML
        assert "/static/chartjs-adapter-date-fns.bundle.min.js" in ENVIRONMENT_HTML
        assert "cdn.jsdelivr.net" not in ENVIRONMENT_HTML

    def test_breaks_line_at_data_gaps(self):
        assert "insertGaps" in ENVIRONMENT_HTML
        assert "spanGaps: false" in ENVIRONMENT_HTML
        assert "senaste sample" in ENVIRONMENT_HTML
