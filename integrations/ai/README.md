# AI Integrations

Part of the Personal Data Insights Lab vision — see [docs/vision.md](../../docs/vision.md).

Phase 6 (AI) builds on Phase 7 (data platform). Storage before analysis.

## Planned Capabilities

### 1. Local LLM (Natural Language Automations)

Run a local LLM via Ollama or LM Studio and expose it to HA via the
`extended_openai_conversation` custom integration or a custom REST command.

**Use cases:**
- "Turn on the bedroom lights in 30 minutes" → parsed intent → HA service call
- Summarise overnight events from logbook
- Explain why an automation fired

**Candidate models:**
- `mistral:7b` — good balance of size and instruction following
- `llama3:8b` — strong general capability
- `phi3:mini` — very fast, lower accuracy

**Integration path:**
```
HA Assist pipeline → Wyoming protocol → Ollama REST → LLM response → HA action
```

### 2. Vision Model (Scene Understanding)

Go beyond Frigate's object classes with a vision-language model for richer descriptions.

**Use cases:**
- "Describe what's happening at the front door"
- Detect package delivery vs. person loitering
- Smoke/fire visual confirmation

**Candidate approach:**
- LLaVA or MiniCPM-V via Ollama
- Triggered by Frigate event → snapshot → LLM caption → HA notification

### 3. Anomaly Detection

Flag unusual motion patterns based on time-of-day and historical frequency.

**Approach:**
- Collect Frigate event metadata into InfluxDB/Grafana
- Train a simple statistical baseline (hour-of-day × zone × object type)
- Alert when event rate deviates significantly from baseline

### 4. Voice Assistant (Wyoming)

Replace cloud voice with a fully local pipeline:
- **STT**: Whisper (via Wyoming-Whisper add-on)
- **Intent**: Local LLM or HA's built-in intent engine
- **TTS**: Piper (via Wyoming-Piper add-on)

## Implementation Notes

- All AI workloads should run on a separate machine if the Dell Latitude 3120
  is CPU-only — inference is heavy.
- GPU acceleration (NVIDIA/AMD) dramatically improves throughput.
- Start with scene caption enrichment before adding broader LLM features. Face recognition removed — [ADR-006](../../docs/decisions/006-no-face-no-companion-presence.md).
