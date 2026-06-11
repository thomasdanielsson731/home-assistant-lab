"""Shared assertions for HA Ingress-safe Insights HTML."""

from __future__ import annotations

import re

# Client-side absolute paths break when Analytics/Environment load in HA iframes.
FORBIDDEN_CLIENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"""fetch\s*\(\s*[`'"]/api/v1"""), "fetch('/api/v1/…')"),
    (re.compile(r"""src\s*=\s*["']/static/"""), 'src="/static/…"'),
    (re.compile(r"""href\s*=\s*["']/timeline"""), 'href="/timeline"'),
    (re.compile(r"""href\s*=\s*["']/environment"""), 'href="/environment"'),
    (re.compile(r"""href\s*=\s*["']/story"""), 'href="/story"'),
    (re.compile(r"""src\s*=\s*["']/media/"""), 'src="/media/…"'),
]

REQUIRED_RELATIVE_FETCHES = (
    "api/v1/events",
    "api/v1/occupancy",
    "api/v1/metrics",
)

REQUIRED_BASE_SCRIPT_MARKERS = (
    "document.createElement('base')",
    "lastIndexOf(needle)",
    "'timeline'",
    "'environment'",
    "'story'",
)


def assert_ingress_safe_html(html: str, *, served: bool) -> None:
    """Fail if HTML would break behind HA Ingress."""
    for pattern, label in FORBIDDEN_CLIENT_PATTERNS:
        match = pattern.search(html)
        assert match is None, f"Forbidden {label} at pos {match.start()!r}: {match.group()!r}"

    if served:
        assert "__INSIGHTS_BASE__" not in html
        for marker in REQUIRED_BASE_SCRIPT_MARKERS:
            assert marker in html, f"Served page missing ingress base script marker: {marker}"
    else:
        assert "__INSIGHTS_BASE__" in html, "Template must keep __INSIGHTS_BASE__ placeholder"


def assert_relative_api_fetches(html: str, *endpoints: str) -> None:
    for endpoint in endpoints:
        assert endpoint in html, f"Missing relative fetch target: {endpoint}"
        assert f"fetch(`/{endpoint}" not in html
        assert f"fetch('/{endpoint}" not in html
