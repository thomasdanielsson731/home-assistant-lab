# Vision — Danielsson Insights

This is not a smart-home automation project. It is **Danielsson Insights** — a personal Home Analytics Platform where the house is the data source, everything is an event, and AI turns signals into understanding.

> Detailed product vision and Cursor prompts: [vision/danielsson-insights.md](vision/danielsson-insights.md)
> Event schema: [analytics/event-model.md](analytics/event-model.md)

---

## One-Sentence Goal

Build an AI-driven observatory for the home: sensors and cameras generate events, data is stored and analysed, and the result is actionable context — not lamp control.

---

## Two Parallel Goals

| Goal | What it means |
|---|---|
| **Hobby lab** | Fun to build, explore, and demo. Frigate, Axis analytics, dashboards, agents. |
| **Professional learning** | Practice the same patterns used in VSaaS and Data Insights: event processing, secure storage, APIs, dashboards, digital twins. |

HomeKit already handles lights and blinds. This project answers different questions:

- What can we learn from the data?
- Can AI find patterns?
- How do you structure a modern data/AI platform?
- How do you build and operate it with Cursor and Claude Code?

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  INSIGHTS — AI agents, dashboards, natural-language queries │
├─────────────────────────────────────────────────────────────┤
│  ANALYSIS — LLM, anomaly detection, scene understanding     │
├─────────────────────────────────────────────────────────────┤
│  STORAGE — time-series DB, event history, retention policy    │
├─────────────────────────────────────────────────────────────┤
│  EVENTS — MQTT, Frigate, AOA, scene/frame, HA state changes  │
├─────────────────────────────────────────────────────────────┤
│  SOURCES — cameras, env sensors, energy, presence, weather    │
└─────────────────────────────────────────────────────────────┘
```

Same shape as a commercial Data Insights platform — just smaller and local-first.

---

## What "Digital Twin" Means Here

Not a 3D model. A **live state model** of the house:

| Dimension | Examples |
|---|---|
| Who | Thomas / Nils / Hugo / Anna — home, away, at front door |
| Environment | Temperature, humidity, CO₂, AQI per zone |
| Activity | Motion, person/vehicle counts, loitering |
| Energy | Consumption patterns, cost drivers |
| History | Trends, baselines, anomalies |

The twin answers questions like:

- "Why was electricity higher this week?"
- "Which rooms are used least?"
- "When should we ventilate?"
- "Is anyone home?"

---

## Scope Boundaries

### In scope

- Home Assistant as the central event and state hub
- Local-first processing (no cloud for security data)
- Camera analytics (Frigate + Axis AOA + scene metadata)
- Environmental sensing (D6210 air quality)
- Face recognition for **context** (who arrived), not surveillance
- Time-series storage and dashboards for insight
- Local LLM experiments (Ollama + Qwen)
- Cursor/Claude agents for development and analysis
- Config-as-code, runbooks, ADRs

### Out of scope (for now)

- Automating every light, blind, and switch (HomeKit handles this)
- Cloud face recognition or cloud LLM for security paths
- ALPR unless a specific need arises
- Nabu Casa / remote access until local setup is stable
- Production-grade HA clustering or multi-site

---

## Development Environment

```
Windows PC (dev)                    Dell Latitude 3120 (prod)
├─ VS Code + Cursor                 ├─ Home Assistant OS
├─ Claude Code / Cursor agents      ├─ Frigate + Mosquitto
├─ Ollama + Qwen                    ├─ Double Take
├─ CodeProject.AI (face recognizer) ├─ 6× Axis cameras (RTSP + MQTT)
├─ air_quality_bridge.py            └─ 1 TB SSD (recordings)
└─ Git (this repo)
```

---

## Phase Map

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation — HAOS, MQTT, naming, backups | Done |
| 2 | Cameras + Frigate — 6 cameras, detection, recording | Done |
| 3 | Dashboard — 5 views, mobile-first | Done |
| 4 | Face recognition — who is at the door | In progress |
| 5 | Axis analytics — AOA, scene, air quality via MQTT | In progress |
| 6 | AI integration — local LLM, scene understanding | Future |
| 7 | Data platform — InfluxDB, Grafana, event history | Future |
| 8 | Digital twin — unified house state + NL queries | Future |

See [roadmap.md](roadmap.md) for task-level detail and [backlog.md](backlog.md) for prioritized work items.

---

## Principles

1. **Local first** — security-relevant data stays on the LAN
2. **Insights over automation** — prefer "what happened?" over "turn on the light"
3. **Config as code** — every HA change lives in this repo
4. **One phase at a time** — stabilise before expanding
5. **Learn by building** — each phase should teach something transferable to professional work
6. **Document decisions** — ADRs, runbooks, and agent context files are first-class artefacts

---

## Key Documents

| Document | Purpose |
|---|---|
| [vision/danielsson-insights.md](vision/danielsson-insights.md) | Product vision + Cursor prompts |
| [analytics/](analytics/) | Event model, timeline, floorplan, cat/bike analytics |
| [scope.md](scope.md) | In/out-of-scope boundaries |
| [roadmap.md](roadmap.md) | Phase plan |
| [backlog.md](backlog.md) | Work queue |
| [current-focus.md](current-focus.md) | AI assistant entry point |
| [architecture/overview.md](architecture/overview.md) | System diagrams |
| [../events/README.md](../events/README.md) | Event store layout |
| [../agents/](../agents/) | Cursor agent roles |
| [../projects/](../projects/) | Sub-project briefs |
