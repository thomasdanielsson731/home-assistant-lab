#!/usr/bin/env python3
"""
Danielsson Insights — Timeline v0

Simple local web UI reading events/timeline.jsonl.

Run: python scripts/timeline_server.py
Open: http://localhost:8765
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys

sys.path.insert(0, str(Path(__file__).parent))
from event_store import TZ  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
TIMELINE_JSONL = REPO_ROOT / "events" / "timeline.jsonl"
EVENTS_ROOT = REPO_ROOT / "events"
PORT = 8765

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("timeline")

TYPE_ICON = {
    "person": "👤",
    "vehicle": "🚗",
    "bicycle": "🚲",
    "cat": "🐈",
    "delivery": "📦",
    "environment": "🌡️",
    "door": "🚪",
    "smoke": "🔥",
}


def load_events(
    hours: int = 168,
    event_type: str | None = None,
    timeline_path: Path | None = None,
) -> list[dict]:
    path = timeline_path or TIMELINE_JSONL
    if not path.exists():
        return []
    cutoff = datetime.now(TZ) - timedelta(hours=hours)
    events = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = datetime.fromisoformat(e["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=TZ)
        if ts < cutoff:
            continue
        if event_type and e.get("type") != event_type:
            continue
        events.append(e)
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    return events


HTML = """<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Danielsson Insights — Timeline</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #0f1117; color: #e8eaed; padding: 1rem; max-width: 640px; margin: 0 auto; }}
    h1 {{ font-size: 1.25rem; margin-bottom: 0.25rem; }}
    .sub {{ color: #9aa0a6; font-size: 0.85rem; margin-bottom: 1rem; }}
    .filters {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }}
    .filters a {{ padding: 0.35rem 0.75rem; border-radius: 1rem; background: #2d2f36; color: #bdc1c6; text-decoration: none; font-size: 0.8rem; }}
    .filters a.active {{ background: #8ab4f8; color: #0f1117; }}
    .entry {{ display: flex; gap: 0.75rem; padding: 0.75rem 0; border-bottom: 1px solid #2d2f36; align-items: flex-start; }}
    .time {{ color: #9aa0a6; font-size: 0.8rem; min-width: 3.5rem; padding-top: 0.1rem; }}
    .icon {{ font-size: 1.25rem; }}
    .body {{ flex: 1; }}
    .summary {{ font-size: 0.95rem; }}
    .meta {{ color: #9aa0a6; font-size: 0.75rem; margin-top: 0.15rem; }}
    .thumb {{ width: 56px; height: 56px; object-fit: cover; border-radius: 6px; background: #2d2f36; }}
    .empty {{ color: #9aa0a6; padding: 2rem 0; text-align: center; }}
    .stats {{ display: flex; gap: 1rem; margin-bottom: 1rem; font-size: 0.8rem; color: #9aa0a6; }}
  </style>
</head>
<body>
  <h1>Danielsson Insights</h1>
  <p class="sub">Timeline · {period_label}</p>
  <div class="stats">{stats}</div>
  <div class="filters">{filters}</div>
  {entries}
</body>
</html>"""


ENTRY = """
<div class="entry">
  <div class="time">{time}</div>
  <div class="icon">{icon}</div>
  <div class="body">
    <div class="summary">{summary}</div>
    <div class="meta">{zone} · {etype} · {source}</div>
  </div>
  {thumb_html}
</div>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.debug(fmt, *args)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            qs = parse_qs(parsed.query)
            hours = int(qs.get("hours", ["168"])[0])
            etype = qs.get("type", [None])[0]
            data = load_events(hours=hours, event_type=etype)
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path.startswith("/media/"):
            rel = parsed.path[len("/media/"):]
            path = EVENTS_ROOT.parent / rel.replace("/", "\\") if "\\" in str(EVENTS_ROOT) else EVENTS_ROOT.parent / rel
            if path.exists() and path.is_file():
                data = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404)
            return

        qs = parse_qs(parsed.query)
        hours = int(qs.get("hours", ["168"])[0])
        active_type = qs.get("type", [None])[0]
        events = load_events(hours=hours, event_type=active_type)

        period_label = "Senaste 7 dagarna" if hours <= 168 else "Senaste 90 dagarna" if hours >= 2000 else f"Senaste {hours}h"

        counts: dict[str, int] = {}
        for e in events:
            counts[e.get("type", "?")] = counts.get(e.get("type", "?"), 0) + 1
        stats = " · ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "Inga events ännu"

        types = ["", "person", "vehicle", "environment", "cat", "bicycle", "delivery"]
        filters = ""
        for t in types:
            label = t or "Alla"
            q = f"?hours={hours}" + (f"&type={t}" if t else "")
            cls = "active" if t == (active_type or "") else ""
            filters += f'<a class="{cls}" href="/{q}">{label}</a>'

        entries_html = ""
        if not events:
            entries_html = '<p class="empty">Inga events i perioden. Kör event_normalizer.py och vänta på detektioner.</p>'
        else:
            for e in events[:200]:
                ts = datetime.fromisoformat(e["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=TZ)
                thumb_html = ""
                snap = (e.get("snapshot") or {}).get("best_picture")
                if snap:
                    thumb_html = f'<img class="thumb" src="/media/{snap}" alt="">'
                entries_html += ENTRY.format(
                    time=ts.strftime("%H:%M"),
                    icon=TYPE_ICON.get(e.get("type", ""), "•"),
                    summary=e.get("summary", e.get("type", "?")),
                    zone=e.get("location", {}).get("zone", "?"),
                    etype=e.get("type", "?"),
                    source=e.get("source", "?"),
                    thumb_html=thumb_html,
                )

        page = HTML.format(
            period_label=period_label,
            stats=stats,
            filters=filters,
            entries=entries_html,
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


def main() -> None:
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    log.info("Timeline v0 → http://localhost:%d", PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
