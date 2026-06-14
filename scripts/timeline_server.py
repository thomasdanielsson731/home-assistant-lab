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
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
    parse_time_range,
)
from environment_page import ENVIRONMENT_HTML  # noqa: E402
from insights_paths import INSIGHTS_BASE_SCRIPT  # noqa: E402
from story_engine import generate_story  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
STATIC_DIR = Path(__file__).parent / "static"
TIMELINE_JSONL = REPO_ROOT / "events" / "timeline.jsonl"
EVENTS_ROOT = REPO_ROOT / "events"
STORIES_DIR = REPO_ROOT / "events" / "stories"
PORT = 8765

STATIC_MIME = {
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".map": "application/json; charset=utf-8",
}

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
HTTPServer = ThreadingHTTPServer  # backward-compatible name for tests

__all__ = ["load_events", "Handler", "HTTPServer", "PORT"]


def _hours_from_qs(qs: dict) -> float:
    return float(qs.get("hours", ["24"])[0])


def _range_from_qs(qs: dict) -> tuple:
    since, until, hours = parse_time_range(qs)
    return since, until, hours


def _insights_page(html: str) -> bytes:
    return html.replace("__INSIGHTS_BASE__", INSIGHTS_BASE_SCRIPT).encode("utf-8")


TIMELINE_V1_HTML = """<!DOCTYPE html>
<html lang="sv">
<head>
  __INSIGHTS_BASE__
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analytics</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f1117; color: #e8eaed; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    header { padding: 0.75rem 1.25rem; border-bottom: 1px solid #2d2f36; flex-shrink: 0; display: flex; align-items: baseline; gap: 0.75rem; }
    h1 { font-size: 1rem; font-weight: 600; }
    .sub { color: #9aa0a6; font-size: 0.75rem; }
    .toolbar { display: flex; gap: 0.4rem; flex-wrap: wrap; padding: 0.5rem 1.25rem; align-items: center; border-bottom: 1px solid #2d2f36; flex-shrink: 0; }
    .toolbar button { padding: 0.3rem 0.7rem; border: none; border-radius: 1rem; background: #2d2f36; color: #bdc1c6; cursor: pointer; font-size: 0.75rem; white-space: nowrap; }
    .toolbar button:hover { background: #3d3f46; }
    .toolbar button.active { background: #8ab4f8; color: #0f1117; font-weight: 600; }
    .toolbar input[type="datetime-local"] { padding: 0.28rem 0.45rem; border: 1px solid #3d3f46; border-radius: 0.5rem; background: #16181d; color: #e8eaed; font-size: 0.72rem; }
    .toolbar .sep { width: 1px; height: 18px; background: #2d2f36; margin: 0 0.2rem; }
    .toolbar .range-label { color: #9aa0a6; font-size: 0.72rem; }
    .stats { color: #9aa0a6; font-size: 0.72rem; margin-left: auto; white-space: nowrap; }
    main { display: grid; grid-template-columns: 1fr 300px; flex: 1; min-height: 0; }
    @media (max-width: 860px) { main { grid-template-columns: 1fr; } aside { display: none; } }
    #canvas-wrap { overflow: hidden; position: relative; cursor: grab; }
    #canvas-wrap.dragging { cursor: grabbing; }
    canvas { display: block; }
    aside { border-left: 1px solid #2d2f36; display: flex; flex-direction: column; overflow: hidden; }
    .aside-tabs { display: flex; border-bottom: 1px solid #2d2f36; flex-shrink: 0; }
    .aside-tab { flex: 1; padding: 0.5rem; text-align: center; font-size: 0.72rem; color: #9aa0a6; cursor: pointer; border-bottom: 2px solid transparent; }
    .aside-tab.active { color: #8ab4f8; border-bottom-color: #8ab4f8; }
    .aside-pane { flex: 1; overflow-y: auto; padding: 0.75rem; display: none; }
    .aside-pane.active { display: block; }
    .detail-empty { color: #9aa0a6; font-size: 0.82rem; }
    #detail-content img { max-width: 100%; border-radius: 6px; margin-top: 0.5rem; }
    .detail-title { font-size: 0.9rem; font-weight: 600; margin-bottom: 0.3rem; }
    .detail-meta { color: #9aa0a6; font-size: 0.72rem; line-height: 1.6; }
    .detail-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 1rem; font-size: 0.68rem; margin: 0.25rem 0.1rem 0 0; font-weight: 600; }
    .occ-block { background: #1e2a3a; border-left: 3px solid #fdd663; border-radius: 3px; padding: 0.4rem 0.5rem; margin-bottom: 0.35rem; font-size: 0.72rem; }
    .occ-block strong { color: #fdd663; font-size: 0.75rem; }
    .occ-dur { color: #9aa0a6; font-size: 0.68rem; }
    .legend { display: flex; gap: 0.6rem; flex-wrap: wrap; font-size: 0.68rem; color: #9aa0a6; padding: 0.4rem 1.25rem; border-bottom: 1px solid #2d2f36; flex-shrink: 0; }
    .legend-item { display: flex; align-items: center; gap: 0.3rem; }
    .legend-dot { width: 8px; height: 8px; border-radius: 50%; }
    .legend-bar { width: 14px; height: 7px; border-radius: 2px; opacity: 0.7; }
    .legend-line { width: 16px; height: 2px; border-radius: 1px; }
    .group-label { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; color: #5f6368; text-transform: uppercase; }
    #tooltip { position: fixed; background: #1e2028; border: 1px solid #3d3f46; border-radius: 6px; padding: 0.4rem 0.6rem; font-size: 0.75rem; pointer-events: none; display: none; z-index: 100; max-width: 220px; box-shadow: 0 4px 12px #0007; }
  </style>
</head>
<body>
  <header>
    <h1>Analytics</h1>
    <span class="sub">What happened — not just current state</span>
    <a href="story" style="margin-left:auto;color:#8ab4f8;font-size:0.78rem;text-decoration:none;padding:0.3rem 0.7rem;border-radius:1rem;background:#2d2f36">📖 Story</a>
  </header>
  <div class="toolbar" id="toolbar">
    <button data-hours="0.25">15 m</button>
    <button data-hours="1">1 h</button>
    <button data-hours="6">6 h</button>
    <button data-hours="24" class="active">24 h</button>
    <button data-hours="168">7 d</button>
    <div class="sep"></div>
    <span class="range-label">Från</span>
    <input type="datetime-local" id="from-input">
    <span class="range-label">Till</span>
    <input type="datetime-local" id="to-input">
    <button type="button" id="apply-range">Apply</button>
    <div class="sep"></div>
    <button type="button" id="goto-now">→ Nu</button>
    <button type="button" id="zoom-reset">Reset</button>
    <span class="stats" id="stats"></span>
  </div>
  <div class="legend">
    <span class="group-label">Activity</span>
    <span class="legend-item"><span class="legend-dot" style="background:#f28b82"></span>Arrival</span>
    <span class="legend-item"><span class="legend-dot" style="background:#fdcfe8"></span>Delivery</span>
    <span class="legend-item"><span class="legend-dot" style="background:#a8dab5"></span>Bicycle</span>
    <span class="group-label" style="margin-left:0.5rem">Presence</span>
    <span class="legend-item"><span class="legend-dot" style="background:#8ab4f8"></span>Person</span>
    <span class="legend-item"><span class="legend-dot" style="background:#81c995"></span>Vehicle</span>
    <span class="legend-item"><span class="legend-bar" style="background:#fdd663"></span>Occupancy</span>
    <span class="legend-item"><span class="legend-dot" style="background:#e8c4a0"></span>Door</span>
    <span class="group-label" style="margin-left:0.5rem">Environment</span>
    <span class="legend-item"><span class="legend-line" style="background:#78d9ec"></span>Env metrics</span>
    <span class="legend-item"><span class="legend-dot" style="background:#c58af9"></span>Scene</span>
    <span class="legend-item"><span class="legend-dot" style="background:#f9ab00"></span>Anomali (baseline)</span>
  </div>
  <main>
    <div id="canvas-wrap"><canvas id="timeline"></canvas></div>
    <aside>
      <div class="aside-tabs">
        <div class="aside-tab active" data-pane="detail">Details</div>
        <div class="aside-tab" data-pane="occupancy">Occupancy</div>
      </div>
      <div class="aside-pane active" id="pane-detail">
        <div id="detail-content" class="detail-empty">Click an event to inspect it</div>
      </div>
      <div class="aside-pane" id="pane-occupancy">
        <div id="occupancy-list"><p class="detail-empty">Loading…</p></div>
      </div>
    </aside>
  </main>
  <div id="tooltip"></div>

  <script>
  (function() {
    const canvas = document.getElementById('timeline');
    const ctx = canvas.getContext('2d');
    const wrap = document.getElementById('canvas-wrap');
    const tooltip = document.getElementById('tooltip');

    // ── State ──────────────────────────────────────────────────
    let hours = 24, customFrom = null, customTo = null;
    let events = [], blocks = [], metrics = [];
    let viewStart = 0, viewEnd = 0;
    let dragging = false, dragStartX = 0, dragViewStart = 0;
    let hoveredEvent = null;

    // ── Layout constants ───────────────────────────────────────
    const LABEL_W = 72;
    const TIME_H = 28;
    const GROUP_H = 18;
    const LANE_H = 28;
    const METRIC_H = 36;
    const PAD_TOP = 8;
    const PAD_RIGHT = 12;

    // Lane groups: [groupLabel, lanes...]
    // Lane types: {name, type:'event'|'block'|'metric', color, shape}
    const GROUPS = [
      { label: 'ACTIVITY', lanes: [
        { name: 'arrival',  type: 'event', color: '#f28b82', shape: 'diamond' },
        { name: 'delivery', type: 'event', color: '#fdcfe8', shape: 'diamond' },
        { name: 'bicycle',  type: 'event', color: '#a8dab5', shape: 'circle'  },
      ]},
      { label: 'PRESENCE', lanes: [
        { name: 'person',   type: 'event', color: '#8ab4f8', shape: 'circle'  },
        { name: 'vehicle',  type: 'event', color: '#81c995', shape: 'rect'    },
        { name: 'occupancy',type: 'block', color: '#fdd663', shape: 'bar'     },
        { name: 'door',     type: 'event', color: '#e8c4a0', shape: 'triangle'},
        { name: 'behavior', type: 'event', color: '#f9ab00', shape: 'diamond' },
      ]},
      { label: 'ENVIRONMENT', lanes: [
        { name: 'environment', type: 'event', color: '#78d9ec', shape: 'triangle' },
        { name: 'scene',      type: 'event',  color: '#c58af9', shape: 'circle' },
        { name: 'co2',        type: 'metric', color: '#78d9ec', metricKey: 'co2' },
        { name: 'temperature',type: 'metric', color: '#f6aea9', metricKey: 'temperature' },
        { name: 'audio',      type: 'metric', color: '#aecbfa', metricKey: 'spl' },
      ]},
    ];

    // Build flat lane index
    const ALL_LANES = [];
    GROUPS.forEach(g => g.lanes.forEach(l => ALL_LANES.push(l)));

    const COLORS = {};
    ALL_LANES.forEach(l => { COLORS[l.name] = l.color; });

    // Lanes hidden when the loaded period has no events of that type —
    // core lanes (person, vehicle, occupancy, scene, metrics) always show.
    const HIDEABLE = ['arrival', 'delivery', 'bicycle', 'door', 'behavior', 'environment'];
    const ANOMALY_COLOR = '#f9ab00';

    function activeGroups() {
      return GROUPS
        .map(g => ({
          label: g.label,
          lanes: g.lanes.filter(l =>
            !HIDEABLE.includes(l.name) || events.some(e => e.type === l.name)),
        }))
        .filter(g => g.lanes.length);
    }

    // Occupancy sub-rows (logical zones — matches CAMERA_ZONE in event_store.py)
    const OCC_STACK = ['driveway', 'backyard', 'storage_ext', 'storage_int', 'front'];

    // ── Canvas sizing ──────────────────────────────────────────
    function calcHeight() {
      let h = PAD_TOP + TIME_H;
      activeGroups().forEach(g => {
        h += GROUP_H;
        g.lanes.forEach(l => { h += l.type === 'metric' ? METRIC_H : LANE_H; });
      });
      return h + 8;
    }

    function resizeCanvas() {
      const rect = wrap.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = calcHeight();
      draw();
    }

    // ── Lane Y positions ───────────────────────────────────────
    function laneYMap() {
      const map = {};
      let y = PAD_TOP + TIME_H;
      activeGroups().forEach(g => {
        y += GROUP_H;
        g.lanes.forEach(l => {
          const h = l.type === 'metric' ? METRIC_H : LANE_H;
          map[l.name] = { y: y + h / 2, h, lh: h, top: y };
          y += h;
        });
      });
      return map;
    }

    // ── Coordinate helpers ─────────────────────────────────────
    function xFor(ts) {
      const t = typeof ts === 'number' ? ts : new Date(ts).getTime();
      const span = viewEnd - viewStart || 1;
      return LABEL_W + ((t - viewStart) / span) * (canvas.width - LABEL_W - PAD_RIGHT);
    }

    function tsForX(x) {
      const span = viewEnd - viewStart;
      return viewStart + ((x - LABEL_W) / (canvas.width - LABEL_W - PAD_RIGHT)) * span;
    }

    // ── Time axis ticks ────────────────────────────────────────
    function tickInterval(spanMs) {
      const targets = [60e3, 5*60e3, 15*60e3, 30*60e3, 3600e3, 3*3600e3, 6*3600e3, 12*3600e3, 24*3600e3];
      const ideal = spanMs / 8;
      return targets.find(t => t >= ideal) || 24*3600e3;
    }

    function formatTick(t, spanMs) {
      const d = new Date(t);
      if (spanMs < 2 * 3600e3) return d.toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
      if (spanMs < 48 * 3600e3) return d.toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
      return d.toLocaleDateString('sv-SE', {month:'short', day:'numeric'}) + ' ' + d.getHours() + 'h';
    }

    // ── Draw shapes ────────────────────────────────────────────
    function drawShape(shape, x, y, color, r = 5) {
      ctx.fillStyle = color;
      ctx.strokeStyle = color + 'cc';
      ctx.lineWidth = 1;
      if (shape === 'circle') {
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI*2); ctx.fill();
      } else if (shape === 'rect') {
        ctx.fillRect(x - r, y - r * 0.7, r * 2, r * 1.4);
      } else if (shape === 'diamond') {
        ctx.beginPath(); ctx.moveTo(x, y - r*1.2); ctx.lineTo(x + r, y);
        ctx.lineTo(x, y + r*1.2); ctx.lineTo(x - r, y); ctx.closePath(); ctx.fill();
      } else if (shape === 'triangle') {
        ctx.beginPath(); ctx.moveTo(x, y - r); ctx.lineTo(x + r, y + r*0.7);
        ctx.lineTo(x - r, y + r*0.7); ctx.closePath(); ctx.fill();
      }
    }

    // ── Metric sparkline ───────────────────────────────────────
    function drawMetricLine(laneInfo, metricKey, color) {
      const pts = metrics.filter(m => {
        if (m.metric !== metricKey) return false;
        const t = new Date(m.timestamp).getTime();
        return t >= viewStart && t <= viewEnd;
      });
      if (pts.length < 2) return;
      const vals = pts.map(m => m.value);
      const min = Math.min(...vals), max = Math.max(...vals);
      const range = max - min || 1;
      const top = laneInfo.top + 4, bot = laneInfo.top + laneInfo.lh - 4;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      pts.forEach((m, i) => {
        const x = xFor(m.timestamp);
        const y = bot - ((m.value - min) / range) * (bot - top);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.globalAlpha = 1;
      // label current value
      if (pts.length) {
        const last = pts[pts.length - 1];
        ctx.fillStyle = color;
        ctx.font = '9px system-ui';
        ctx.fillText(last.value.toFixed(1), canvas.width - PAD_RIGHT - 30, laneInfo.top + 11);
      }
    }

    // ── Main draw ──────────────────────────────────────────────
    function draw() {
      if (!canvas.width) return;
      const W = canvas.width, H = canvas.height;
      const span = viewEnd - viewStart || 1;
      const ymap = laneYMap();

      ctx.fillStyle = '#0f1117';
      ctx.fillRect(0, 0, W, H);

      // Time axis background
      ctx.fillStyle = '#13151b';
      ctx.fillRect(LABEL_W, PAD_TOP, W - LABEL_W - PAD_RIGHT, TIME_H);

      // Draw group separators and lane backgrounds
      let gy = PAD_TOP + TIME_H;
      activeGroups().forEach(g => {
        // Group label row
        ctx.fillStyle = '#181a21';
        ctx.fillRect(0, gy, W, GROUP_H);
        ctx.fillStyle = '#5f6368';
        ctx.font = 'bold 9px system-ui';
        ctx.fillText(g.label, LABEL_W + 6, gy + GROUP_H - 5);
        gy += GROUP_H;

        g.lanes.forEach(l => {
          const lh = l.type === 'metric' ? METRIC_H : LANE_H;
          // Subtle alternating background
          ctx.fillStyle = '#0f1117';
          ctx.fillRect(LABEL_W, gy, W - LABEL_W - PAD_RIGHT, lh);
          // Hairline separator
          ctx.fillStyle = '#1e2028';
          ctx.fillRect(LABEL_W, gy + lh - 1, W - LABEL_W - PAD_RIGHT, 1);
          // Lane label
          ctx.fillStyle = '#6e737a';
          ctx.font = '10px system-ui';
          ctx.textAlign = 'right';
          ctx.fillText(l.name, LABEL_W - 6, gy + lh / 2 + 4);
          ctx.textAlign = 'left';
          gy += lh;
        });
      });

      // Vertical "now" line
      const nowX = xFor(Date.now());
      if (nowX > LABEL_W && nowX < W - PAD_RIGHT) {
        ctx.strokeStyle = '#8ab4f822';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath(); ctx.moveTo(nowX, PAD_TOP + TIME_H); ctx.lineTo(nowX, H); ctx.stroke();
        ctx.setLineDash([]);
      }

      // Time ticks
      const interval = tickInterval(span);
      const firstTick = Math.ceil(viewStart / interval) * interval;
      ctx.fillStyle = '#9aa0a6';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      for (let t = firstTick; t <= viewEnd; t += interval) {
        const x = xFor(t);
        if (x < LABEL_W || x > W - PAD_RIGHT) continue;
        ctx.fillStyle = '#2d2f36';
        ctx.fillRect(x, PAD_TOP + TIME_H - 4, 1, 4);
        ctx.fillStyle = '#9aa0a6';
        ctx.fillText(formatTick(t, span), x, PAD_TOP + TIME_H - 6);
        // Vertical grid line
        ctx.strokeStyle = '#1e2028';
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(x, PAD_TOP + TIME_H); ctx.lineTo(x, H); ctx.stroke();
      }
      ctx.textAlign = 'left';

      // Occupancy blocks (one sub-row per logical zone)
      const stackN = OCC_STACK.length;
      blocks.forEach(b => {
        const info = ymap['occupancy'];
        if (!info) return;
        const x1 = Math.max(xFor(b.start), LABEL_W);
        const x2 = Math.min(xFor(b.end), W - PAD_RIGHT);
        if (x2 <= x1) return;
        ctx.fillStyle = COLORS.occupancy + '55';
        ctx.strokeStyle = COLORS.occupancy + 'cc';
        ctx.lineWidth = 1;
        const row = Math.max(0, OCC_STACK.indexOf(b.zone));
        const rowH = (info.h - 2) / stackN;
        const bh = Math.max(rowH - 2, 4);
        const by = info.top + row * rowH + 1;
        ctx.fillRect(x1, by, x2 - x1, bh);
        ctx.strokeRect(x1, by, x2 - x1, bh);
        if (x2 - x1 > 48) {
          ctx.fillStyle = '#0f1117';
          ctx.font = 'bold 8px system-ui';
          ctx.fillText(b.zone, x1 + 4, by + bh - 3);
        }
        b._x1 = x1; b._x2 = x2; b._y = by + bh / 2;
      });

      // Metric sparklines
      activeGroups().forEach(g => g.lanes.forEach(l => {
        if (l.type !== 'metric') return;
        drawMetricLine(ymap[l.name], l.metricKey, l.color);
      }));

      // Events
      events.forEach(ev => {
        const lane = ALL_LANES.find(l => l.name === ev.type);
        if (!lane) return;
        const info = ymap[ev.type];
        if (!info) return;
        const x = xFor(ev.timestamp);
        if (x < LABEL_W - 6 || x > W - PAD_RIGHT + 6) return;
        const isHovered = hoveredEvent === ev;
        const isAnomaly = !!(ev.metadata && ev.metadata.anomaly);
        const color = isAnomaly ? ANOMALY_COLOR : lane.color;
        const r = isHovered ? 7 : (isAnomaly ? 6 : 5);
        if (isHovered || isAnomaly) {
          ctx.shadowColor = color;
          ctx.shadowBlur = isHovered ? 8 : 5;
        }
        drawShape(lane.shape, x, info.y, color, r);
        ctx.shadowBlur = 0;
        ev._x = x; ev._y = info.y;
      });
    }

    // ── Hit testing ────────────────────────────────────────────
    function hitEvent(cx, cy) {
      let best = null, bestD = 18;
      events.forEach(ev => {
        if (ev._x == null) return;
        const d = Math.hypot(ev._x - cx, ev._y - cy);
        if (d < bestD) { bestD = d; best = ev; }
      });
      return best;
    }

    function hitBlock(cx, cy) {
      return blocks.find(b => b._x1 != null && cx >= b._x1 && cx <= b._x2 && Math.abs(cy - b._y) < 12);
    }

    // ── Detail panel ───────────────────────────────────────────
    function showEventDetail(ev) {
      const el = document.getElementById('detail-content');
      const ts = new Date(ev.timestamp);
      const timeStr = ts.toLocaleString('sv-SE', {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'});
      const snap = ev.snapshot?.best_picture;
      const identity = ev.identity?.name && ev.identity.name !== 'Someone' ? ev.identity.name : null;
      const conf = ev.confidence ? `${Math.round(ev.confidence * 100)}%` : '';
      const zone = ev.location?.zone || '?';
      const typeColor = COLORS[ev.type] || '#fff';
      el.innerHTML = `
        <div class="detail-title">${ev.summary || ev.type}</div>
        <div style="margin-bottom:0.4rem">
          <span class="detail-badge" style="background:${typeColor}22;color:${typeColor}">${ev.type}</span>
          ${ev.enriched ? '<span class="detail-badge" style="background:#c58af922;color:#c58af9">enriched</span>' : ''}
          ${ev.metadata?.anomaly ? '<span class="detail-badge" style="background:#f9ab0022;color:#f9ab00">anomali</span>' : ''}
        </div>
        <div class="detail-meta">
          <b>Time:</b> ${timeStr}<br>
          <b>Zone:</b> ${zone}<br>
          <b>Source:</b> ${ev.source || '?'}<br>
          ${identity ? `<b>Identity:</b> ${identity} ${conf ? '(' + conf + ')' : ''}<br>` : ''}
          ${ev.metadata?.metric ? `<b>Metric:</b> ${ev.metadata.metric} = ${ev.metadata.value}<br>` : ''}
          ${ev.metadata?.baseline_mean != null ? `<b>Baseline:</b> ${ev.metadata.baseline_mean}±${ev.metadata.baseline_std}<br>` : ''}
          ${ev.metadata?.duration ? `<b>Duration:</b> ${Math.round(ev.metadata.duration)}s<br>` : ''}
          ${ev.metadata?.scenario ? `<b>Scenario:</b> ${ev.metadata.scenario}<br>` : ''}
          ${ev.metadata?.behavior ? `<b>Behavior:</b> ${ev.metadata.behavior}<br>` : ''}
          ${ev.metadata?.rule ? `<b>Rule:</b> ${ev.metadata.rule}<br>` : ''}
        </div>
        ${snap ? `<img src="media/${snap}" alt="" style="margin-top:0.5rem;max-width:100%;border-radius:6px">` : ''}
      `;
      switchPane('detail');
    }

    function switchPane(name) {
      document.querySelectorAll('.aside-tab').forEach(t => t.classList.toggle('active', t.dataset.pane === name));
      document.querySelectorAll('.aside-pane').forEach(p => p.classList.toggle('active', p.id === 'pane-' + name));
    }

    // ── Occupancy panel ────────────────────────────────────────
    function renderOccupancy() {
      const el = document.getElementById('occupancy-list');
      if (!blocks.length) { el.innerHTML = '<p class="detail-empty">No occupancy blocks in range</p>'; return; }
      el.innerHTML = blocks.slice(0, 15).map(b => {
        const s = new Date(b.start).toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
        const e = new Date(b.end).toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
        const dur = b.duration_seconds ? `${Math.round(b.duration_seconds / 60)} min` : '';
        const typeLabel = b.scenario.includes('Vehicle') ? 'Vehicle' : 'Person';
        return `<div class="occ-block">
          <strong>${b.zone}</strong> · ${typeLabel}<br>
          ${s} → ${e} ${dur ? '<span class="occ-dur">(' + dur + ')</span>' : ''}
        </div>`;
      }).join('');
    }

    // ── Data loading ───────────────────────────────────────────
    function apiQuery() {
      if (customFrom && customTo) return `from=${encodeURIComponent(customFrom)}&to=${encodeURIComponent(customTo)}`;
      return `hours=${hours}`;
    }

    async function load() {
      const q = apiQuery();
      try {
        const [ev, occ, met] = await Promise.all([
          fetch(`api/v1/events?${q}`).then(r => { if (!r.ok) throw new Error('events'); return r.json(); }),
          fetch(`api/v1/occupancy?${q}`).then(r => { if (!r.ok) throw new Error('occupancy'); return r.json(); }),
          fetch(`api/v1/metrics?${q}`).then(r => { if (!r.ok) throw new Error('metrics'); return r.json(); }),
        ]);
        events = Array.isArray(ev) ? ev.filter(e => e.type !== 'occupancy') : [];
        blocks = Array.isArray(occ) ? occ : [];
        metrics = Array.isArray(met) ? met : [];
      } catch (err) {
        document.getElementById('stats').textContent =
          'Cannot load timeline — check Danielsson Insights add-on on HA';
        events = []; blocks = []; metrics = [];
        resizeCanvas();
        return;
      }
      document.getElementById('stats').textContent =
        `${events.length} events · ${blocks.length} occupancy blocks · ${metrics.length} metric samples`;
      resetViewToData();
      renderOccupancy();
      resizeCanvas();
    }

    function resetViewToData() {
      const now = Date.now();
      viewEnd = customTo ? new Date(customTo).getTime() : now;
      viewStart = customFrom ? new Date(customFrom).getTime() : now - hours * 3600000;
    }

    function clampView() {
      const minSpan = 60000;
      if (viewEnd - viewStart < minSpan) { viewEnd = viewStart + minSpan; }
      const maxPast = Date.now() - 366 * 24 * 3600000;
      if (viewStart < maxPast) viewStart = maxPast;
      if (viewEnd > Date.now() + 3600000) viewEnd = Date.now() + 3600000;
    }

    function zoomView(factor, anchorRatio) {
      const span = viewEnd - viewStart;
      const anchor = viewStart + span * anchorRatio;
      const newSpan = Math.max(span * factor, 60000);
      viewStart = anchor - newSpan * anchorRatio;
      viewEnd = viewStart + newSpan;
      clampView();
      draw();
    }

    // ── Resize observer ────────────────────────────────────────
    const ro = new ResizeObserver(() => resizeCanvas());
    ro.observe(wrap);

    // ── Mouse / touch events ───────────────────────────────────
    canvas.addEventListener('mousemove', ev => {
      const rect = canvas.getBoundingClientRect();
      const cx = ev.clientX - rect.left, cy = ev.clientY - rect.top;
      const hit = hitEvent(cx, cy) || hitBlock(cx, cy);
      const prev = hoveredEvent;
      hoveredEvent = hit && hit.type ? hit : null;

      if (hit) {
        canvas.style.cursor = 'pointer';
        let label = '';
        if (hit.summary) label = hit.summary;
        else if (hit.zone) label = `${hit.zone} ${hit.scenario || ''}`;
        const anomalyTag = hit.metadata?.anomaly ? ' <span style="color:#f9ab00">⚠ anomali</span>' : '';
        const ts = new Date(hit.timestamp || hit.start).toLocaleTimeString('sv-SE', {hour:'2-digit', minute:'2-digit'});
        tooltip.innerHTML = `<strong>${ts}</strong> ${label}${anomalyTag}`;
        tooltip.style.display = 'block';
        tooltip.style.left = (ev.clientX + 12) + 'px';
        tooltip.style.top = (ev.clientY - 8) + 'px';
      } else {
        canvas.style.cursor = dragging ? 'grabbing' : 'grab';
        tooltip.style.display = 'none';
      }

      if (prev !== hoveredEvent) draw();

      if (dragging) {
        const dx = ev.clientX - dragStartX;
        const span = viewEnd - viewStart;
        const shift = (dx / (canvas.width - LABEL_W - PAD_RIGHT)) * span;
        viewStart = dragViewStart - shift;
        viewEnd = viewStart + span;
        clampView();
        draw();
      }
    });

    canvas.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; hoveredEvent = null; draw(); });

    canvas.addEventListener('mousedown', ev => {
      dragging = true; dragStartX = ev.clientX; dragViewStart = viewStart;
      wrap.classList.add('dragging');
    });
    window.addEventListener('mouseup', () => { dragging = false; wrap.classList.remove('dragging'); });

    canvas.addEventListener('click', ev => {
      const rect = canvas.getBoundingClientRect();
      const cx = ev.clientX - rect.left, cy = ev.clientY - rect.top;
      const hit = hitEvent(cx, cy);
      if (hit) { showEventDetail(hit); return; }
      const blk = hitBlock(cx, cy);
      if (blk) switchPane('occupancy');
    });

    canvas.addEventListener('wheel', ev => {
      ev.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left - LABEL_W) / (canvas.width - LABEL_W - PAD_RIGHT)));
      zoomView(ev.deltaY < 0 ? 0.8 : 1.25, ratio);
    }, { passive: false });

    // ── Toolbar events ─────────────────────────────────────────
    document.getElementById('toolbar').addEventListener('click', ev => {
      const btn = ev.target.closest('button[data-hours]');
      if (!btn) return;
      document.querySelectorAll('.toolbar button[data-hours]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      hours = parseFloat(btn.dataset.hours);
      customFrom = null; customTo = null;
      document.getElementById('from-input').value = '';
      document.getElementById('to-input').value = '';
      load();
    });

    document.getElementById('apply-range').addEventListener('click', () => {
      const f = document.getElementById('from-input').value;
      const t = document.getElementById('to-input').value;
      if (!f || !t) return;
      customFrom = new Date(f).toISOString();
      customTo = new Date(t).toISOString();
      document.querySelectorAll('.toolbar button[data-hours]').forEach(b => b.classList.remove('active'));
      load();
    });

    document.getElementById('zoom-reset').addEventListener('click', () => { resetViewToData(); draw(); });
    document.getElementById('goto-now').addEventListener('click', () => {
      const span = viewEnd - viewStart;
      viewEnd = Date.now();
      viewStart = viewEnd - span;
      clampView(); draw();
    });

    document.querySelectorAll('.aside-tab').forEach(tab => {
      tab.addEventListener('click', () => switchPane(tab.dataset.pane));
    });

    load();
  })();
  </script>
</body>
</html>"""

HTML = """<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Danielsson Insights — Analytics</title>
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
    .entry-anomaly {{ background: #f9ab000f; border-left: 3px solid #f9ab00; padding-left: calc(0.75rem - 3px); }}
    .entry-anomaly .summary {{ color: #fdd663; }}
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
  <p class="nav"><a href="timeline">→ Analytics</a></p>
  <div class="stats">{stats}</div>
  <div class="filters">{filters}</div>
  {entries}
</body>
</html>"""

ENTRY = """
<div class="entry{entry_class}">
  <div class="time">{time}</div>
  <div class="icon">{icon}</div>
  <div class="body">
    <div class="summary">{summary}</div>
    <div class="meta">{zone} · {etype} · {source}{anomaly_tag}</div>
  </div>
  {thumb_html}
</div>"""


STORY_HTML = """<!DOCTYPE html>
<html lang="sv">
<head>
  __INSIGHTS_BASE__
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>House Story</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #0f1117; color: #e8eaed; max-width: 680px; margin: 0 auto; padding: 1rem; }
    header { padding: 1rem 0; border-bottom: 1px solid #2d2f36; margin-bottom: 1rem; }
    h1 { font-size: 1.1rem; }
    .sub { color: #9aa0a6; font-size: 0.8rem; margin-top: 0.2rem; }
    .nav { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .nav a { padding: 0.3rem 0.7rem; border-radius: 1rem; background: #2d2f36; color: #bdc1c6; text-decoration: none; font-size: 0.78rem; }
    .nav a.active { background: #8ab4f8; color: #0f1117; }
    .story-title { font-size: 1rem; font-weight: 600; margin-bottom: 0.2rem; }
    .story-summary { color: #9aa0a6; font-size: 0.82rem; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #2d2f36; }
    .beat { display: flex; gap: 0.75rem; padding: 0.65rem 0; border-bottom: 1px solid #1e2028; }
    .beat-time { color: #8ab4f8; font-size: 0.78rem; min-width: 2.8rem; font-weight: 600; padding-top: 0.1rem; }
    .beat-text { font-size: 0.9rem; line-height: 1.4; }
    .beat-cat { font-size: 0.65rem; color: #9aa0a6; margin-top: 0.2rem; }
    .empty { color: #9aa0a6; text-align: center; padding: 3rem 0; }
    .cat-arrival { color: #f28b82; }
    .cat-security { color: #fdcfe8; }
    .cat-environment { color: #78d9ec; }
    .cat-access { color: #e8c4a0; }
    a { color: #8ab4f8; }
  </style>
</head>
<body>
  <header>
    <h1>House Story</h1>
    <p class="sub">What happened — in plain language</p>
  </header>
  <div class="nav" id="nav"></div>
  <div id="story-title" class="story-title"></div>
  <div id="story-summary" class="story-summary"></div>
  <div id="beats"></div>
  <script>
    const CAT_CLASS = { arrival:'cat-arrival', security:'cat-security', environment:'cat-environment', access:'cat-access' };
    let currentDate = null;

    function fmtDate(d) {
      return new Date(d + 'T12:00:00').toLocaleDateString('sv-SE', {weekday:'long', month:'long', day:'numeric'});
    }

    async function loadStory(date) {
      currentDate = date;
      const url = date === 'today' ? 'api/v1/story/today' : `api/v1/story/${date}`;
      const story = await fetch(url).then(r => r.json());
      document.getElementById('story-title').textContent = story.title || fmtDate(story.date);
      document.getElementById('story-summary').textContent = story.summary || '';
      const el = document.getElementById('beats');
      if (!story.beats || !story.beats.length) {
        el.innerHTML = '<p class="empty">No notable events on this day.</p>';
        return;
      }
      el.innerHTML = story.beats.map(b => {
        const cls = CAT_CLASS[b.category] || '';
        return `<div class="beat">
          <div class="beat-time">${b.time}</div>
          <div>
            <div class="beat-text">${b.text}</div>
            <div class="beat-cat ${cls}">${b.category}</div>
          </div>
        </div>`;
      }).join('');
    }

    async function buildNav() {
      const nav = document.getElementById('nav');
      const dates = ['today'];
      const now = new Date();
      for (let i = 1; i <= 6; i++) {
        const d = new Date(now); d.setDate(d.getDate() - i);
        dates.push(d.toISOString().slice(0, 10));
      }
      nav.innerHTML = dates.map((d, i) => {
        const label = i === 0 ? 'Idag' : (i === 1 ? 'Igår' : new Date(d + 'T12:00:00').toLocaleDateString('sv-SE', {weekday:'short', day:'numeric'}));
        return `<a href="#" data-date="${d}">${label}</a>`;
      }).join('');
      nav.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', e => {
          e.preventDefault();
          nav.querySelectorAll('a').forEach(x => x.classList.remove('active'));
          a.classList.add('active');
          loadStory(a.dataset.date);
        });
      });
      nav.querySelector('a').classList.add('active');
    }

    buildNav().then(() => loadStory('today'));
  </script>
</body>
</html>"""


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
            since, until, hours = _range_from_qs(qs)
            etype = qs.get("type", [None])[0]
            data = load_events(
                hours=hours,
                since=since,
                until=until,
                event_type=etype,
                timeline_path=TIMELINE_JSONL,
            )
            self._json_response(data)
            return

        if parsed.path == "/api/v1/metrics":
            since, until, hours = _range_from_qs(qs)
            metrics = qs.get("metric", None)
            data = load_metrics(hours=hours, since=since, until=until, metrics=metrics)
            self._json_response(data)
            return

        if parsed.path == "/api/v1/occupancy":
            since, until, _hours = _range_from_qs(qs)
            window = until - since
            occ_since = since - window
            events = load_events(
                hours=None,
                since=occ_since,
                until=until,
                event_type="occupancy",
                timeline_path=TIMELINE_JSONL,
                newest_first=False,
            )
            self._json_response(build_occupancy_blocks(events, since=since, until=until))
            return

        if parsed.path == "/timeline":
            page = _insights_page(TIMELINE_V1_HTML)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return

        if parsed.path == "/environment":
            page = _insights_page(ENVIRONMENT_HTML)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return

        # ── Story API ─────────────────────────────────────────────────
        if parsed.path == "/api/v1/story/today":
            date_str = datetime.now(TZ).strftime("%Y-%m-%d")
            try:
                story = generate_story(date_str)
                self._json_response(story)
            except Exception as exc:
                self._json_response({"error": str(exc)}, status=500)
            return

        if parsed.path.startswith("/api/v1/story/") and parsed.path != "/api/v1/story/":
            date_str = parsed.path[len("/api/v1/story/"):].strip("/")
            # Handle "week" alias
            if date_str == "week":
                today = datetime.now(TZ)
                week_stories = []
                for i in range(7):
                    d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                    cached = STORIES_DIR / f"{d}.json"
                    if cached.exists():
                        try:
                            week_stories.append(json.loads(cached.read_text(encoding="utf-8")))
                        except json.JSONDecodeError:
                            pass
                self._json_response(week_stories)
                return
            # Validate date format
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self._json_response({"error": "Invalid date format, use YYYY-MM-DD"}, status=400)
                return
            # Try cache first, then generate
            cached = STORIES_DIR / f"{date_str}.json"
            if cached.exists():
                try:
                    story = json.loads(cached.read_text(encoding="utf-8"))
                    self._json_response(story)
                    return
                except json.JSONDecodeError:
                    pass
            try:
                story = generate_story(date_str)
                self._json_response(story)
            except Exception as exc:
                self._json_response({"error": str(exc)}, status=500)
            return

        if parsed.path in ("/story", "/story/"):
            page = _insights_page(STORY_HTML)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return

        if parsed.path.startswith("/static/"):
            rel = parsed.path[len("/static/"):]
            if ".." in rel or rel.startswith("/"):
                self.send_error(403)
                return
            path = STATIC_DIR / rel
            if path.exists() and path.is_file():
                data = path.read_bytes()
                mime = STATIC_MIME.get(path.suffix.lower(), "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404)
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
                    thumb_html = f'<img class="thumb" src="media/{snap}" alt="">'
                is_anomaly = bool((e.get("metadata") or {}).get("anomaly"))
                entries_html += ENTRY.format(
                    time=ts.strftime("%H:%M"),
                    icon=TYPE_ICON.get(e.get("type", ""), "•"),
                    summary=e.get("summary", e.get("type", "?")),
                    zone=e.get("location", {}).get("zone", "?"),
                    etype=e.get("type", "?"),
                    source=e.get("source", "?"),
                    entry_class=" entry-anomaly" if is_anomaly else "",
                    anomaly_tag=" · ⚠ anomali" if is_anomaly else "",
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
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log.info("Timeline → http://localhost:%d/timeline", PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
