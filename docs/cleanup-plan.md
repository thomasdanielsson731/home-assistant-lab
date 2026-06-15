# Home Assistant Cleanup Plan

> **Archived (2026-06-14):** Pre-Frigate checklist from early lab setup. Phases 1–3 and most Phase 5 items are complete. Use [backlog.md](backlog.md) for current work. Kept for historical reference only.

Step-by-step checklist for bringing an existing HA installation to a clean, consistent baseline before adding Frigate or analytics features. Face recognition removed — [ADR-006](decisions/006-no-face-no-companion-presence.md).

Work through sections in order. Complete each section fully before moving to the next.

---

## Phase 1 — Quick Wins (1–2 hours)

These have no dependencies and immediately improve the experience.

### 1.1 — Rename entities to match naming conventions

- [ ] Open **Settings → Devices & Services** and review all integrations
- [ ] Open **Settings → Areas** — verify areas match the [naming conventions](naming-conventions.md) area list
- [ ] Rename any entity that doesn't follow `<domain>.<integration>_<zone_id>_<attribute>` pattern
- [ ] Use HA Developer Tools (States tab) to audit all current entity IDs
- [ ] Note: renaming entity IDs breaks existing dashboards and automations — fix those immediately after

**Goal:** Every entity ID is readable, predictable, and zone-referenced.

### 1.2 — Clean up Areas

- [ ] Create all areas from the approved list (see [naming-conventions.md](naming-conventions.md))
- [ ] Assign every device to the correct area
- [ ] Remove or merge any duplicate or improperly named areas

**Areas to create:**
- Ground Floor: `Kitchen / Living Room`, `Hall (Ground Floor)`, `Bedroom`, `Bathroom (Ground Floor)`
- Upper Floor: `TV Room`, `Nils' Room`, `Hugo's Room`, `Hall (Upper Floor)`, `Office`, `Bathroom (Upper Floor)`
- Outdoor: `Front`, `Driveway`, `Backyard`, `Storage Building`

### 1.3 — Delete unused entities and integrations

- [ ] Go to **Settings → Devices & Services → Entities** — filter by "unavailable"
- [ ] Delete entities that have been unavailable for more than 7 days (they're stale)
- [ ] Disable or remove integrations you don't actively use
- [ ] Clear the logbook of ghost devices

**Goal:** Unavailable entities = 0.

### 1.4 — Enable automatic backups

- [ ] Go to **Settings → System → Backups**
- [ ] Enable automatic backups: daily, retain 7 copies
- [ ] Confirm backup destination (local or network share)
- [ ] Take a manual backup now before making further changes

---

## Phase 2 — Naming and Structure (2–4 hours)

Requires care — entity renames cascade.

### 2.1 — Customise entity names and icons

- [ ] For every light entity: set a friendly name matching the area + fixture (e.g. "Kitchen Ceiling")
- [ ] For every switch: name after what it controls, not the device model
- [ ] Assign icons using `mdi:` icon names that match the entity type
- [ ] Set `entity_id` to snake_case per convention (do this via Developer Tools → Template or via `customize.yaml`)

### 2.2 — Organise automations

- [ ] Export all existing automations (download from **Settings → Automations**)
- [ ] Review each automation:
  - Does it have a clear `alias` in `<domain>_<trigger>_<action>` format?
  - Does it have a `description`?
  - Is it enabled and still relevant?
- [ ] Delete automations that are test or no longer used
- [ ] Group automations by domain using the `id` field prefix

### 2.3 — Clean up the default dashboard

- [ ] Delete the auto-generated "Overview" dashboard (or rename it to "Home")
- [ ] Remove all unused or duplicate views
- [ ] Remove badge entities that reference unavailable or renamed entities

---

## Phase 3 — MQTT Foundation (1 hour)

Required before adding Frigate.

### 3.1 — Install and configure Mosquitto

- [ ] Install **Mosquitto Broker** add-on from the Add-on Store
- [ ] In **Settings → Devices & Services → MQTT**, configure:
  - Broker: `localhost`
  - Port: `1883`
- [ ] Test MQTT using Developer Tools → MQTT (publish and subscribe to `test/topic`)
- [ ] Verify HA discovers the MQTT broker add-on automatically

### 3.2 — Verify MQTT is not exposed externally

- [ ] Confirm port 1883 is not forwarded through the router
- [ ] MQTT should be LAN-only

---

## Phase 4 — Frigate Prerequisites (1–2 hours)

Before installing Frigate.

### 4.1 — Mount external SSD

- [ ] Confirm the 1 TB SSD is visible to HAOS: **Settings → System → Storage**
- [ ] Format as ext4 if not already
- [ ] Mount at `/media/frigate` using HA OS filesystem settings or SSH

### 4.2 — Verify camera access

For each Axis camera:
- [ ] Confirm the camera is reachable at its IP address from the HA host
- [ ] Test RTSP stream manually:
  ```bash
  ffprobe rtsp://user:pass@<camera-ip>/axis-media/media.amp
  ```
- [ ] Record each camera's IP, username, and password in `secrets.yaml` on the host (not in git)

### 4.3 — Add cameras to secrets.yaml

```yaml
# /config/secrets.yaml on the HAOS host — never commit this file
front_camera_ip: "192.168.x.x"
front_camera_user: "admin"
front_camera_password: "..."
# ... repeat for each camera
```

---

## Phase 5 — Pre-Dashboard Hygiene (1 hour)

Quick cleanup before building dashboards.

### 5.1 — Set home location and elevation

- [ ] **Settings → System → General** — verify coordinates are correct
- [ ] Verify timezone is correct (e.g. `Europe/Stockholm`)

### 5.2 — Person entities (optional)

> **ADR-006:** Family members do not use the Companion app. Person entities are optional for Thomas (push notifications only).

- [ ] Thomas: Companion app linked only if security push is desired
- [ ] Do **not** require home/away tracking for Nils, Hugo, Anna
- [ ] Dashboard uses `binary_sensor.house_outdoor_presence` for outdoor activity — not `person.*`

### 5.3 — Install required dashboard card packages via HACS

- [ ] Install **HACS** if not already installed
- [ ] Install: Mushroom Cards
- [ ] Install: Frigate Card
- [x] Install: mini-graph-card — `scripts/install-mini-graph-card.ps1`
- [ ] Restart HA frontend after each install

---

## Done Criteria

Before moving to Frigate integration, all of the following must be true:

- [ ] Zero unavailable entities
- [ ] All areas created and all devices assigned
- [ ] All entity IDs follow naming conventions
- [ ] Automatic backups enabled and tested
- [ ] MQTT broker running and tested
- [ ] External SSD mounted and accessible
- [ ] Camera IPs confirmed and documented in secrets.yaml
- [ ] HACS cards installed
- [ ] Outdoor presence template verified (`binary_sensor.house_outdoor_presence`)
