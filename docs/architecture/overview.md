# System Architecture

## Production Environment

```
┌─────────────────────────────────────────────────────────┐
│  Dell Latitude 3120 — Home Assistant OS                 │
│                                                         │
│  ┌─────────────────┐   ┌─────────────────────────────┐ │
│  │  Home Assistant │   │  Frigate Add-on             │ │
│  │  Core           │◄──│  NVR + Object Detection     │ │
│  │  :8123          │   │  :5000 / :8554 (RTSP)       │ │
│  └────────┬────────┘   └──────────┬──────────────────┘ │
│           │ MQTT                  │ RTSP                │
│  ┌────────▼────────┐   ┌──────────▼──────────────────┐ │
│  │  Mosquitto      │   │  Double Take Add-on         │ │
│  │  MQTT Broker    │   │  Face Recognition Middleware │ │
│  │  :1883          │   │  :3000                      │ │
│  └─────────────────┘   └─────────────────────────────┘ │
│                                                         │
│  Storage: External 1 TB SSD  (Frigate recordings)       │
└─────────────────────────────────────────────────────────┘
              ▲ RTSP streams
┌─────────────────────────────────────────────────────────┐
│  Axis Camera Network (PoE)                              │
│  P3288  Q3558-LVE  M2036  Q1656×2  M1055  D6210        │
└─────────────────────────────────────────────────────────┘
```

## Development Environment

```
┌──────────────────────────────────────────────────┐
│  Windows PC — Development Machine                │
│                                                  │
│  VS Code + Cursor  ──►  config/ (this repo)      │
│  Claude Code       ──►  AI-assisted development  │
│  Ollama + Qwen     ──►  Local LLM experiments    │
│                                                  │
│  scripts/sync-config.sh ──SSH──► HAOS :22222     │
└──────────────────────────────────────────────────┘
```

---

## Camera Architecture

```mermaid
graph LR
    subgraph Cameras["Axis Camera Network (PoE)"]
        P3288["P3288\nfront"]
        Q3558["Q3558-LVE\ndriveway_wide"]
        M2036["M2036\ndriveway_id"]
        Q1656B["Q1656\nbackyard"]
        Q1656S["Q1656\nstorage_ext"]
        M1055["M1055\nstorage_int"]
        D6210["D6210 (radar)\ndriveway_env"] -->|"I/O port"| M2036
    end

    subgraph HAOS["Home Assistant OS"]
        Frigate["Frigate\nNVR + Detection"]
        HA["Home Assistant Core"]
        MQTT["Mosquitto MQTT"]
    end

    P3288 -->|RTSP| Frigate
    Q3558 -->|RTSP| Frigate
    M2036 -->|RTSP| Frigate
    Q1656B -->|RTSP| Frigate
    Q1656S -->|RTSP| Frigate
    M1055 -->|RTSP| Frigate

    Frigate -->|events| MQTT
    MQTT --> HA
    HA -->|Frigate integration| Frigate
```

---

## Frigate Architecture

```mermaid
graph TD
    A[Axis Camera RTSP] -->|detect sub-stream| B[Frigate Detector]
    A -->|main stream| C[Frigate Recorder]

    B -->|bounding boxes| D[Frigate Event Engine]
    C -->|H.264 segments| E[1TB SSD Storage]

    D -->|snapshots| F["/media/frigate/clips"]
    D -->|MQTT events| G[Mosquitto]
    D -->|HTTP webhook| H[Double Take]

    G --> I[HA Core]
    H -->|face match result| G

    I -->|binary_sensor, camera entities| J[Dashboard / Automations]
```

**Dual-stream per camera:**
- **Detect stream** — sub-resolution (e.g. 640×360), low FPS, feeds the ML detector
- **Record stream** — full resolution, continuous or motion-triggered recording to SSD

---

## Current Detection Stack

| Camera | Detect Resolution | Detect FPS | Objects |
|---|---|---|---|
| front | 640×360 | 5 | person, face |
| driveway_wide | 1280×720 | 5 | person, car |
| driveway_id | 640×360 | 10 | person, face, car |
| backyard | 640×360 | 5 | person |
| storage_ext | 640×360 | 5 | person |
| storage_int | 640×360 | 5 | person |

---

## Face Recognition Architecture (Planned)

```mermaid
sequenceDiagram
    participant Cam as Axis Camera
    participant Fri as Frigate
    participant DT as Double Take
    participant CF as CompreFace
    participant HA as Home Assistant

    Cam->>Fri: RTSP stream
    Fri->>Fri: Detect person
    Fri->>DT: Webhook (snapshot)
    DT->>CF: POST /api/v1/recognition/recognize
    CF-->>DT: {subject, similarity}
    DT->>HA: MQTT double_take/matches
    HA->>HA: Fire automation (known / unknown)
```

**Recognizer:** CompreFace (self-hosted, runs on a separate container or VM)

**Training flow:**
1. Capture face crops from Frigate snapshots
2. Label and upload via CompreFace API
3. Double Take auto-retrains on next restart

**HA events produced:**
- `double_take/matches` — known person with confidence score
- `double_take/cameras` — per-camera status

---

## AI Integration Architecture (Planned)

```mermaid
graph TD
    subgraph Dev["Development Machine"]
        Ollama["Ollama + Qwen\nLocal LLM"]
        Claude["Claude Code\nDev AI"]
    end

    subgraph HAOS["Home Assistant OS"]
        HA["HA Core"]
        Fri["Frigate"]
    end

    subgraph AxisNet["Axis Camera Network"]
        ACAP["Axis ACAP Apps\nCustom detection models"]
        MQTT2["Axis MQTT\nMetadata stream"]
    end

    Ollama -->|REST API| HA
    HA -->|"Assist pipeline\n(Wyoming)"| Ollama
    Fri -->|snapshots| Ollama
    ACAP -->|MQTT| HA
    MQTT2 --> HA
    Claude -->|config authoring| Dev
```

**Phases:**
1. Axis ACAP analytics → MQTT → HA (metadata enrichment)
2. Ollama LLM → HA Assist pipeline (natural language automations)
3. Vision-language model (LLaVA/Qwen-VL) → scene descriptions on events
4. AI agent loop: event → context → decision → HA action

---

## Network Topology

See [network.md](network.md) for IP assignments, VLAN design, and port table.

## Data Flows

See [data-flows.md](data-flows.md) for detailed per-integration data flow documentation.
