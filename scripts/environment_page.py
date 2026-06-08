"""Environment metrics UI — shared time range + multi-series charts."""

ENVIRONMENT_HTML = """<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Environment</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f1117; color: #e8eaed; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    header { padding: 0.75rem 1.25rem; border-bottom: 1px solid #2d2f36; flex-shrink: 0; display: flex; align-items: baseline; gap: 0.75rem; }
    h1 { font-size: 1rem; font-weight: 600; }
    .sub { color: #9aa0a6; font-size: 0.75rem; }
    header a { margin-left: auto; color: #8ab4f8; font-size: 0.78rem; text-decoration: none; padding: 0.3rem 0.7rem; border-radius: 1rem; background: #2d2f36; }
    .toolbar { display: flex; gap: 0.4rem; flex-wrap: wrap; padding: 0.5rem 1.25rem; align-items: center; border-bottom: 1px solid #2d2f36; flex-shrink: 0; }
    .toolbar button { padding: 0.3rem 0.7rem; border: none; border-radius: 1rem; background: #2d2f36; color: #bdc1c6; cursor: pointer; font-size: 0.75rem; white-space: nowrap; }
    .toolbar button:hover { background: #3d3f46; }
    .toolbar button.active { background: #8ab4f8; color: #0f1117; font-weight: 600; }
    .toolbar input[type="datetime-local"] { padding: 0.28rem 0.45rem; border: 1px solid #3d3f46; border-radius: 0.5rem; background: #16181d; color: #e8eaed; font-size: 0.72rem; }
    .toolbar .sep { width: 1px; height: 18px; background: #2d2f36; margin: 0 0.2rem; }
    .toolbar .range-label { color: #9aa0a6; font-size: 0.72rem; }
    .stats { color: #9aa0a6; font-size: 0.72rem; margin-left: auto; white-space: nowrap; }
    .live { display: flex; gap: 0.5rem; flex-wrap: wrap; padding: 0.55rem 1.25rem; border-bottom: 1px solid #2d2f36; flex-shrink: 0; }
    .live-chip { background: #1e2028; border: 1px solid #2d2f36; border-radius: 0.6rem; padding: 0.35rem 0.65rem; font-size: 0.72rem; min-width: 5.5rem; }
    .live-chip strong { display: block; color: #e8eaed; font-size: 0.95rem; font-weight: 600; }
    .live-chip span { color: #9aa0a6; font-size: 0.65rem; }
    main { flex: 1; overflow-y: auto; padding: 0.75rem 1.25rem 1.25rem; display: flex; flex-direction: column; gap: 1rem; }
    .chart-card { background: #16181d; border: 1px solid #2d2f36; border-radius: 10px; padding: 0.75rem; }
    .chart-title { font-size: 0.8rem; font-weight: 600; margin-bottom: 0.35rem; }
    .chart-sub { color: #9aa0a6; font-size: 0.68rem; margin-bottom: 0.5rem; }
    .chart-wrap { position: relative; height: 220px; }
    .empty { color: #9aa0a6; font-size: 0.82rem; text-align: center; padding: 2rem; }
  </style>
</head>
<body>
  <header>
    <h1>Environment</h1>
    <span class="sub">Driveway D6210 · camera SPL · shared time range</span>
    <a href="/timeline">→ Analytics</a>
  </header>
  <div class="toolbar" id="toolbar">
    <button data-hours="6">6 h</button>
    <button data-hours="24" class="active">24 h</button>
    <button data-hours="168">7 d</button>
    <button data-hours="720">30 d</button>
    <button data-hours="2160">90 d</button>
    <div class="sep"></div>
    <span class="range-label">Från</span>
    <input type="datetime-local" id="from-input">
    <span class="range-label">Till</span>
    <input type="datetime-local" id="to-input">
    <button type="button" id="apply-range">Apply</button>
    <span class="stats" id="stats"></span>
  </div>
  <div class="live" id="live"></div>
  <main id="charts">
    <div class="chart-card">
      <div class="chart-title">Climate</div>
      <div class="chart-sub">Temperature (°C) and humidity (%) in the same chart</div>
      <div class="chart-wrap"><canvas id="chart-climate"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Air quality</div>
      <div class="chart-sub">CO₂, AQI and PM2.5 — click legend to hide series</div>
      <div class="chart-wrap"><canvas id="chart-air"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Sound pressure level</div>
      <div class="chart-sub">Front · driveway · backyard (dB)</div>
      <div class="chart-wrap"><canvas id="chart-spl"></canvas></div>
    </div>
  </main>

  <script>
  (function() {
    const SERIES = [
      { key: 'driveway_env:temperature', label: 'Temperature', unit: '°C', color: '#f6aea9', chart: 'climate', yAxis: 'y' },
      { key: 'driveway_env:humidity', label: 'Humidity', unit: '%', color: '#8ab4f8', chart: 'climate', yAxis: 'y1' },
      { key: 'driveway_env:co2', label: 'CO₂', unit: 'ppm', color: '#78d9ec', chart: 'air', yAxis: 'y' },
      { key: 'driveway_env:aqi', label: 'AQI', unit: '', color: '#fdd663', chart: 'air', yAxis: 'y1' },
      { key: 'driveway_env:pm2_5', label: 'PM2.5', unit: 'µg/m³', color: '#c58af9', chart: 'air', yAxis: 'y1' },
      { key: 'front:spl', label: 'Front SPL', unit: 'dB', color: '#aecbfa', chart: 'spl', yAxis: 'y' },
      { key: 'driveway_wide:spl', label: 'Driveway SPL', unit: 'dB', color: '#81c995', chart: 'spl', yAxis: 'y' },
      { key: 'backyard:spl', label: 'Backyard SPL', unit: 'dB', color: '#e8c4a0', chart: 'spl', yAxis: 'y' },
    ];

    let hours = 24, customFrom = null, customTo = null;
    let charts = { climate: null, air: null, spl: null };

    const chartDefaults = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#bdc1c6', boxWidth: 12, font: { size: 11 } } },
        tooltip: {
          backgroundColor: '#1e2028',
          titleColor: '#e8eaed',
          bodyColor: '#bdc1c6',
          borderColor: '#3d3f46',
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          type: 'time',
          ticks: { color: '#9aa0a6', maxTicksLimit: 8, font: { size: 10 } },
          grid: { color: '#2d2f36' },
        },
        y: {
          ticks: { color: '#9aa0a6', font: { size: 10 } },
          grid: { color: '#2d2f36' },
        },
        y1: {
          position: 'right',
          ticks: { color: '#9aa0a6', font: { size: 10 } },
          grid: { drawOnChartArea: false },
        },
      },
    };

    function queryString() {
      if (customFrom && customTo) {
        return `from=${encodeURIComponent(customFrom)}&to=${encodeURIComponent(customTo)}`;
      }
      return `hours=${hours}`;
    }

    function downsample(points, maxPts) {
      if (points.length <= maxPts) return points;
      const step = Math.ceil(points.length / maxPts);
      const out = [];
      for (let i = 0; i < points.length; i += step) {
        const slice = points.slice(i, Math.min(i + step, points.length));
        const avg = slice.reduce((s, p) => s + p.y, 0) / slice.length;
        out.push({ x: slice[slice.length - 1].x, y: avg });
      }
      return out;
    }

    function groupMetrics(rows) {
      const map = {};
      SERIES.forEach(s => { map[s.key] = []; });
      rows.forEach(r => {
        const k = `${r.zone}:${r.metric}`;
        if (!map[k]) return;
        map[k].push({ x: new Date(r.timestamp), y: Number(r.value) });
      });
      Object.values(map).forEach(arr => arr.sort((a, b) => a.x - b.x));
      return map;
    }

    function latestValue(map, key) {
      const pts = map[key];
      if (!pts || !pts.length) return null;
      const v = pts[pts.length - 1].y;
      const meta = SERIES.find(s => s.key === key);
      const unit = meta ? meta.unit : '';
      return unit ? `${v} ${unit}` : String(v);
    }

    function renderLive(map) {
      const el = document.getElementById('live');
      el.innerHTML = SERIES.map(s => {
        const val = latestValue(map, s.key);
        if (val === null) return '';
        return `<div class="live-chip"><strong>${val}</strong><span>${s.label}</span></div>`;
      }).join('');
    }

    function ensureCanvas(id) {
      const wrap = document.getElementById(id).parentElement;
      if (!wrap.querySelector('canvas')) {
        wrap.innerHTML = `<canvas id="${id}"></canvas>`;
      }
    }

    function makeChart(id, chartKey, datasets, dualAxis) {
      if (charts[chartKey]) {
        charts[chartKey].destroy();
        charts[chartKey] = null;
      }
      ensureCanvas(id);
      const canvas = document.getElementById(id);
      const hasData = datasets.some(d => d.data.length);
      if (!hasData) {
        canvas.parentElement.innerHTML = '<p class="empty">No data in this range — check bridges on dev PC</p>';
        return;
      }
      const scales = { ...chartDefaults.scales };
      if (!dualAxis) delete scales.y1;
      charts[chartKey] = new Chart(canvas, {
        type: 'line',
        data: { datasets },
        options: { ...chartDefaults, scales },
      });
    }

    function buildDatasets(map, chartKey, maxPts) {
      return SERIES.filter(s => s.chart === chartKey).map(s => ({
        label: s.label,
        data: downsample(map[s.key] || [], maxPts),
        borderColor: s.color,
        backgroundColor: s.color + '33',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2,
        yAxisID: s.yAxis,
      }));
    }

    async function load() {
      const res = await fetch(`/api/v1/metrics?${queryString()}`);
      const rows = await res.json();
      const map = groupMetrics(rows);
      const maxPts = hours >= 720 ? 500 : hours >= 168 ? 400 : 300;
      renderLive(map);
      document.getElementById('stats').textContent =
        `${rows.length} samples · ${SERIES.filter(s => (map[s.key] || []).length).length} active series`;

      makeChart('chart-climate', 'climate', buildDatasets(map, 'climate', maxPts), true);
      makeChart('chart-air', 'air', buildDatasets(map, 'air', maxPts), true);
      makeChart('chart-spl', 'spl', buildDatasets(map, 'spl', maxPts), false);
    }

    document.querySelectorAll('#toolbar button[data-hours]').forEach(btn => {
      btn.addEventListener('click', () => {
        hours = parseFloat(btn.dataset.hours);
        customFrom = customTo = null;
        document.getElementById('from-input').value = '';
        document.getElementById('to-input').value = '';
        document.querySelectorAll('#toolbar button[data-hours]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        load();
      });
    });

    document.getElementById('apply-range').addEventListener('click', () => {
      const f = document.getElementById('from-input').value;
      const t = document.getElementById('to-input').value;
      if (!f || !t) return;
      customFrom = new Date(f).toISOString();
      customTo = new Date(t).toISOString();
      document.querySelectorAll('#toolbar button[data-hours]').forEach(b => b.classList.remove('active'));
      load();
    });

    load();
  })();
  </script>
</body>
</html>"""
