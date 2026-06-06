#!/usr/bin/env python3
"""
Danielsson Home Intelligence — Timeline server.

List UI (v0):  http://localhost:8765/
Timeline (v1): http://localhost:8765/timeline
API:           /api/v1/events | /api/v1/metrics | /api/v1/occupancy
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys

sys.path.insert(0, str(Path(__file__).parent))
from event_store import TZ  # noqa: E402
from timeline_api import (  # noqa: E402
    build_occupancy_blocks,
    event_summary_stats,
    load_events,
    load_metrics,
)

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
    "arrival": "🏠",
    "environment": "🌡️",
    "occupancy": "📍",
    "scene": "👁️",
    "door": "🚪",
    "smoke": "🔥",
}

# Re-export for backward-compatible tests
__all__ = ["load_events", "Handler", "HTTPServer", "PORT"]


def _hours_from_qs(qs: dict) -> int:
    return int(qs.get("hours", ["24"])[0])


TIMELINE_V1_HTML = """<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>House Intelligence Timeline</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #0f1117; color: #e8eaed; }
    header { padding: 1rem 1.25rem; border-bottom: 1px solid #2d2f36; }
    h1 { font-size: 1.1rem; }
    .sub { color: #9aa0a6; font-size: 0.8rem; margin-top: 0.2rem; }
    .toolbar { display: flex; gap: 0.5rem; flex-wrap: wrap; padding: 0.75rem 1.25rem; align-items: center; }
    .toolbar button { padding: 0.35rem 0.85rem; border: none; border-radius: 1rem; background: #2d2f36; color: #bdc1c6; cursor: pointer; font-size: 0.8rem; }
    .toolbar button.active { background: #8ab4f8; color: #0f1117; }
    .stats { color: #9aa0a6; font-size: 0.75rem; margin-left: auto; }
    main { display: grid; grid-template-columns: 1fr 280px; min-height: calc(100vh - 120px); }
    @media (max-width: 800px) { main { grid-template-columns: 1fr; } }
    #canvas-wrap { padding: 1rem 1.25rem; overflow-x: auto; }
    canvas { background: #16181d; border-radius: 8px; display: block; }
    aside { border-left: 1px solid #2d2f36; padding: 1rem; font-size: 0.85rem; }
    aside h2 { font-size: 0.9rem; margin-bottom: 0.5rem; }
    .detail-empty { color: #9aa0a6; }
    .detail img { max-width: 100%; border-radius: 6px; margin-top: 0.5rem; }
    .detail .meta { color: #9aa0a6; font-size: 0.75rem; margin-top: 0.35rem; }
    .occ-block { background: #2d3a4f; border-radius: 4px; padding: 0.35rem 0.5rem; margin-bottom: 0.35rem; font-size: 0.75rem; }
    .legend { display: flex; gap: 0.75rem; flex-wrap: wrap; font-size: 0.7rem; color: #9aa0a6; padding: 0 1.25rem 1rem; }
    .legend span::before { content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
    .legend .person::before { background: #8ab4f8; }
    .legend .vehicle::before { background: #81c995; }
    .legend .occupancy::before { background: #fdd663; border-radius: 2px; width: 12px; height: 6px; }
    .legend .scene::before { background: #c58af9; }
    .legend .environment::before { background: #78d9ec; }
  </style>
</head>
<body>
  <header>
    <h1>House Intelligence Timeline</h1>
    <p class="sub">What happened — not just current state</p>
  </header>
  <div class="toolbar" id="toolbar">
    <button data-hours="1">1 h</button>
    <button data-hours="24" class="active">24 h</button>
    <button data-hours="168">7 d</button>
    <span class="stats" id="stats"></span>
  </div>
  <div class="legend">
    <span class="person">Person</span>
    <span class="vehicle">Vehicle</span>
    <span class="occupancy">Occupancy block</span>
    <span class="scene">Scene</span>
    <span class="environment">Environment</span>
  </div>
  <main>
    <div id="canvas-wrap"><canvas id="timeline" width="900" height="320"></canvas></div>
    <aside>
      <h2>Details</h2>
      <div id="detail" class="detail-empty">Click an event</div>
      <h2 style="margin-top:1rem">Occupancy</h2>
      <div id="occupancy"></div>
    </aside>
  </main>
  <script>
    const canvas = document.getElementById('timeline');
    const ctx = canvas.getContext('2d');
    let hours = 24;
    let events = [];
    let blocks = [];
    let metrics = [];

    const LANES = ['arrival', 'delivery', 'occupancy', 'person', 'vehicle', 'scene', 'environment'];
    const COLORS = { arrival: '#f28b82', delivery: '#fdcfe8', person: '#8ab4f8', vehicle: '#81c995', scene: '#c58af9', environment: '#78d9ec', occupancy: '#fdd663' };

    async function load() {
      const [ev, occ, met] = await Promise.all([
        fetch(`/api/v1/events?hours=${hours}`).then(r => r.json()),
        fetch(`/api/v1/occupancy?hours=${hours}`).then(r => r.json()),
        fetch(`/api/v1/metrics?hours=${hours}`).then(r => r.json()),
      ]);
      events = ev;
      blocks = occ;
      metrics = met;
      document.getElementById('stats').textContent =
        `${events.length} events · ${blocks.length} occupancy blocks · ${metrics.length} metric samples`;
      renderOccupancy();
      draw();
    }

    function renderOccupancy() {
      const el = document.getElementById('occupancy');
      if (!blocks.length) { el.innerHTML = '<p class="detail-empty">No blocks</p>'; return; }
      el.innerHTML = blocks.slice(0, 12).map(b => {
        const s = new Date(b.start).toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
        const e = new Date(b.end).toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
        return `<div class="occ-block"><strong>${b.zone}</strong> ${b.scenario}<br>${s} → ${e}</div>`;
      }).join('');
    }

    function draw() {
      const w = canvas.width, h = canvas.height;
      ctx.fillStyle = '#16181d';
      ctx.fillRect(0, 0, w, h);
      const now = Date.now();
      const start = now - hours * 3600000;
      const pad = 48;
      const laneH = (h - pad - 40) / LANES.length;

      ctx.strokeStyle = '#2d2f36';
      ctx.beginPath();
      ctx.moveTo(pad, h - 30);
      ctx.lineTo(w - 12, h - 30);
      ctx.stroke();

      LANES.forEach((lane, i) => {
        const y = pad + i * laneH + laneH / 2;
        ctx.fillStyle = '#9aa0a6';
        ctx.font = '11px system-ui';
        ctx.fillText(lane, 4, y + 4);
      });

      function xFor(ts) {
        const t = new Date(ts).getTime();
        return pad + ((t - start) / (now - start)) * (w - pad - 20);
      }

      blocks.forEach(b => {
        const lane = 0;
        const y = pad + lane * laneH + laneH / 2;
        const x1 = xFor(b.start), x2 = xFor(b.end);
        ctx.fillStyle = COLORS.occupancy + '99';
        ctx.fillRect(x1, y - 8, Math.max(x2 - x1, 4), 16);
      });

      events.forEach(e => {
        const lane = LANES.indexOf(e.type);
        if (lane < 0) return;
        const y = pad + lane * laneH + laneH / 2;
        const x = xFor(e.timestamp);
        ctx.fillStyle = COLORS[e.type] || '#fff';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
        e._x = x; e._y = y;
      });

      if (metrics.length) {
        const co2 = metrics.filter(m => m.metric === 'co2');
        if (co2.length > 1) {
          const baseY = h - 28;
          const vals = co2.map(m => m.value);
          const min = Math.min(...vals), max = Math.max(...vals) || 1;
          ctx.strokeStyle = '#78d9ec55';
          ctx.beginPath();
          co2.forEach((m, i) => {
            const x = xFor(m.timestamp);
            const y = baseY - ((m.value - min) / (max - min)) * 22;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.stroke();
        }
      }
    }

    canvas.addEventListener('click', ev => {
      const rect = canvas.getBoundingClientRect();
      const cx = ev.clientX - rect.left, cy = ev.clientY - rect.top;
      let best = null, bestD = 20;
      events.forEach(e => {
        if (e._x == null) return;
        const d = Math.hypot(e._x - cx, e._y - cy);
        if (d < bestD) { bestD = d; best = e; }
      });
      const el = document.getElementById('detail');
      if (!best) { el.innerHTML = '<p class="detail-empty">No event here</p>'; return; }
      const snap = best.snapshot && best.snapshot.best_picture;
      el.innerHTML = `<strong>${best.summary || best.type}</strong>
        <div class="meta">${best.timestamp} · ${best.location?.zone || '?'} · ${best.source || '?'}</div>
        ${snap ? `<img src="/media/${snap}" alt="">` : ''}
        <pre class="meta">${JSON.stringify(best.metadata || {}, null, 2)}</pre>`;
    });

    document.getElementById('toolbar').addEventListener('click', e => {
      const btn = e.target.closest('button[data-hours]');
      if (!btn) return;
      document.querySelectorAll('.toolbar button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      hours = +btn.dataset.hours;
      load();
    });

    load();
  </script>
</body>
</html>"""

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
    .nav {{ margin-bottom: 1rem; }}
    .nav a {{ color: #8ab4f8; font-size: 0.85rem; }}
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
  <p class="sub">Event list · {period_label}</p>
  <p class="nav"><a href="/timeline">→ House Intelligence Timeline (v1)</a></p>
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

    def _json_response(self, data, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path in ("/api/events", "/api/v1/events"):
            hours = _hours_from_qs(qs)
            etype = qs.get("type", [None])[0]
            data = load_events(hours=hours, event_type=etype, timeline_path=TIMELINE_JSONL)
            self._json_response(data)
            return

        if parsed.path == "/api/v1/metrics":
            hours = _hours_from_qs(qs)
            metrics = qs.get("metric", None)
            data = load_metrics(hours=hours, metrics=metrics)
            self._json_response(data)
            return

        if parsed.path == "/api/v1/occupancy":
            hours = _hours_from_qs(qs)
            events = load_events(hours=hours * 2, event_type="occupancy", timeline_path=TIMELINE_JSONL, newest_first=False)
            self._json_response(build_occupancy_blocks(events, hours=hours))
            return

        if parsed.path == "/timeline":
            page = TIMELINE_V1_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return

        if parsed.path.startswith("/media/"):
            rel = parsed.path[len("/media/"):]
            path = REPO_ROOT / rel.replace("/", "\\") if "\\" in str(REPO_ROOT) else REPO_ROOT / rel
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

        hours = _hours_from_qs(qs)
        active_type = qs.get("type", [None])[0]
        events = load_events(hours=hours, event_type=active_type, timeline_path=TIMELINE_JSONL)

        period_label = "Senaste 7 dagarna" if hours <= 168 else f"Senaste {hours}h"
        stats = " · ".join(f"{k}: {v}" for k, v in sorted(event_summary_stats(events).items())) or "Inga events ännu"

        types = ["", "arrival", "delivery", "person", "vehicle", "occupancy", "scene", "environment"]
        filters = ""
        for t in types:
            label = t or "Alla"
            q = f"?hours={hours}" + (f"&type={t}" if t else "")
            cls = "active" if t == (active_type or "") else ""
            filters += f'<a class="{cls}" href="/{q}">{label}</a>'

        entries_html = ""
        if not events:
            entries_html = '<p class="empty">Inga events i perioden.</p>'
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
    log.info("Timeline → http://localhost:%d/timeline", PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
