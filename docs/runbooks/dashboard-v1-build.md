# Dashboard V1 Build Guide

Step-by-step instructions for building the Home Assistant V1 dashboard entirely from the GUI. No YAML required.

**Design reference:** [docs/dashboard-design.md](../dashboard-design.md)

---

## Prerequisites

Complete these before starting. The dashboard will have broken cards if these are missing.

- [ ] HACS installed
- [ ] **Mushroom Cards** installed via HACS → Frontend
- [ ] **Frigate Card** installed via HACS → Frontend
- [ ] **mini-graph-card** installed via HACS → Frontend
- [ ] Browser hard-refreshed after each install (Ctrl+Shift+R)
- [ ] Person entities created for Thomas, Nils, Hugo
- [ ] All Areas created (see [naming-conventions.md](../naming-conventions.md))

> **Note on Frigate cards:** Cameras view and Security detections require Frigate to be running with cameras configured (Phase 2). Build those sections after Phase 2. All other sections can be built now.

---

## Step 1 — Create the Dashboard

1. Go to **Settings → Dashboards**
2. Click **+ Add Dashboard** (bottom right)
3. Fill in:
   - **Title:** `Home`
   - **Icon:** `mdi:home`
   - **URL path:** `home` (auto-fills, leave as-is)
4. Enable **Show in sidebar**
5. Click **Create**
6. Click the new dashboard in the list to open it
7. Click the **pencil icon** (top right) to enter edit mode
8. Click **⋮ (three dots) → Edit dashboard**
9. Check **Start with an empty dashboard**
10. Click **Take control**

The dashboard now uses the **Sections** layout by default in HA 2024.3+. If it shows "Panel" or "Masonry", click **⋮ → Change layout → Sections**.

---

## Step 2 — Add the Five Views

While in edit mode:

1. Click **+ Add View** (tab at the top)
2. Repeat for each view below:

| View # | Title | Icon | Path |
|---|---|---|---|
| 1 | Home | `mdi:home-variant` | `home` (rename the default) |
| 2 | Cameras | `mdi:cctv` | `cameras` |
| 3 | Rooms | `mdi:floor-plan` | `rooms` |
| 4 | Security | `mdi:shield-home` | `security` |
| 5 | Operations | `mdi:cog` | `ops` |

To configure a view: click the view tab → click **pencil icon** next to the tab name.

---

## View 1 — Home

Select the **Home** tab. You'll build 4 sections.

---

### Section 1.1 — Greeting and Presence

**Add a section:**
Click **+ Add Section**. Leave column width at default (full width).

**Card 1 — Greeting title**

1. Click **+ Add Card** in the section
2. Search: `Mushroom Title`
3. Select **Mushroom: Title card**
4. Settings:
   - **Title:** `Good morning` *(We'll make this dynamic later — for now a static title is fine)*
   - **Subtitle:** Leave empty
5. Click **Save**

**Card 2 — Person presence chips**

1. Click **+ Add Card**
2. Search: `Mushroom Chips`
3. Select **Mushroom: Chips card**
4. Click **+ Add chip → Entity**
5. Add three entity chips, one per person:
   - **Entity:** `person.thomas`
   - **Content info:** `state`
   - Click **+ Add chip → Entity** again
   - **Entity:** `person.nils`
   - **Content info:** `state`
   - Click **+ Add chip → Entity** again
   - **Entity:** `person.hugo`
   - **Content info:** `state`
6. Click **Save**

---

### Section 1.2 — Quick Status

**Add a section:** Click **+ Add Section**

**Card 1 — Quick status chips**

1. Click **+ Add Card → Mushroom Chips**
2. Add three chips:

   **Chip A — Security status**
   - Click **+ Add chip → Template chip**
   - **Icon:** `mdi:shield-lock`
   - **Content:** `{{ states('alarm_control_panel.home_alarm') | title }}`
   - **Icon color:** *(leave default — set later once alarm entity exists)*

   **Chip B — Driveway motion**
   - Click **+ Add chip → Entity chip**
   - **Entity:** `binary_sensor.frigate_driveway_wide_motion`
   - **Content info:** `state`
   - *(skip if Frigate not yet configured)*

   **Chip C — Home mode**
   - Click **+ Add chip → Template chip**
   - **Icon:** `mdi:home`
   - **Content:** `{{ states('input_select.home_mode') }}`

3. Click **Save**

---

### Section 1.3 — Recent Frigate Events

**Add a section:** Click **+ Add Section**

**Card 1 — Event log**

1. Click **+ Add Card**
2. Search: `Logbook`
3. Select **Logbook card**
4. Settings:
   - **Title:** `Recent Events`
   - **Entities:** Add `binary_sensor.frigate_front_person`, `binary_sensor.frigate_driveway_wide_car`, `binary_sensor.frigate_driveway_id_person`
   - **Hours to show:** `24`
5. Click **Save**

> Skip or leave as placeholder if Frigate entities don't exist yet. Come back after Phase 2.

---

### Section 1.4 — Lights On Now

**Add a section:** Click **+ Add Section**

**Card 1 — Active lights chip row**

1. Click **+ Add Card → Mushroom Chips**
2. For each light in the house, add an **Entity chip**:
   - Set **Entity** to each `light.*` entity
   - Set **Visibility** → **Condition: State equals** `on` (so the chip only shows when the light is on)
3. Click **Save**

---

## View 2 — Cameras

Select the **Cameras** tab. Three sections: Driveway, Front, Backyard & Storage.

> **Requires Frigate (Phase 2).** Build this view after all cameras are running in Frigate.

---

### Section 2.1 — Driveway

**Add a section:** Click **+ Add Section**

**Card 1 — Section header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Driveway`
3. Click **Save**

**Card 2 — Driveway wide camera (full width)**

1. **+ Add Card**
2. Search: `Frigate`
3. Select **Frigate card**
4. Settings:
   - **Camera entity:** `camera.frigate_driveway_wide`
   - **Live provider:** `ha` (or `jsmpeg` if ha is slow)
   - **Controls:** Enable **Thumbnails**, **Timeline**, **Fullscreen**
   - **Aspect ratio:** `16:9`
5. Click **Save**

**Card 3 — Driveway ID camera (left half)**

1. **+ Add Card → Frigate card**
2. **Camera entity:** `camera.frigate_driveway_id`
3. **Aspect ratio:** `16:9`
4. Click **Save**

**Card 4 — D6210 radar status (right half)**

1. **+ Add Card → Mushroom Entity card**
2. **Entity:** `binary_sensor.driveway_env_motion`
3. **Name:** `Driveway Radar`
4. **Icon:** `mdi:radar`
5. **Color when active:** `amber`
6. Click **Save**

> To place Cards 3 and 4 side-by-side: in the section settings, set **Columns: 2**.

---

### Section 2.2 — Front

**Add a section:** Click **+ Add Section**

**Card 1 — Section header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Front`
3. Click **Save**

**Card 2 — Front camera (full width)**

1. **+ Add Card → Frigate card**
2. **Camera entity:** `camera.frigate_front`
3. **Aspect ratio:** `16:9`
4. Enable **Thumbnails** and **Timeline**
5. Click **Save**

---

### Section 2.3 — Backyard and Storage

**Add a section:** Click **+ Add Section** → set **Columns: 2**

**Card 1 — Section header (spans full width)**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Backyard & Storage`
3. Click **Save**

**Card 2 — Backyard camera**

1. **+ Add Card → Frigate card**
2. **Camera entity:** `camera.frigate_backyard`
3. **Aspect ratio:** `16:9`
4. Click **Save**

**Card 3 — Storage exterior camera**

1. **+ Add Card → Frigate card**
2. **Camera entity:** `camera.frigate_storage_ext`
3. **Aspect ratio:** `16:9`
4. Click **Save**

**Card 4 — Storage interior camera (place below, spans left column)**

1. **+ Add Card → Frigate card**
2. **Camera entity:** `camera.frigate_storage_int`
3. **Aspect ratio:** `16:9`
4. Click **Save**

---

## View 3 — Rooms

Select the **Rooms** tab. Three sections: Ground Floor, Upper Floor, Outdoor.

---

### Section 3.1 — Ground Floor

**Add a section:** Click **+ Add Section** → **Columns: 2**

**Card 1 — Section header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Ground Floor`
3. Click **Save**

**Cards 2–5 — Room cards** (one per room, 2-column grid)

For each room, add a **Mushroom: Title card** — there is no native "room summary card" in Mushroom; use an entity card per room to show room state.

**Kitchen / Living Room:**

1. **+ Add Card → Mushroom Entity card**
2. **Entity:** `light.kitchen_ceiling` *(or the area's main light)*
3. **Name:** `Kitchen / Living Room`
4. **Icon:** `mdi:sofa`
5. **Secondary info:** `last-changed`
6. Click **Save**

Repeat for:
- **Hall (Ground Floor)** → entity: `light.hall_ground_ceiling`, icon: `mdi:door`
- **Bedroom** → entity: `light.bedroom_main`, icon: `mdi:bed`
- **Bathroom (Ground Floor)** → entity: `light.bathroom_ground_mirror`, icon: `mdi:shower`

> Use the most representative entity per room (main light, or a climate entity if there is one). The card title becomes the room name.

---

### Section 3.2 — Upper Floor

**Add a section:** Click **+ Add Section** → **Columns: 2**

**Card 1 — Section header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Upper Floor`

Room cards (same pattern as ground floor):
- **TV Room** → icon: `mdi:television`
- **Nils' Room** → icon: `mdi:bed`
- **Hugo's Room** → icon: `mdi:bed`
- **Hall (Upper Floor)** → icon: `mdi:door`
- **Office** → icon: `mdi:desk`
- **Bathroom (Upper Floor)** → icon: `mdi:shower`

---

### Section 3.3 — Outdoor

**Add a section:** Click **+ Add Section** → **Columns: 2**

**Card 1 — Section header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Outdoor`

Room cards:
- **Front** → entity: `binary_sensor.frigate_front_motion`, icon: `mdi:gate`
- **Driveway** → entity: `binary_sensor.frigate_driveway_wide_motion`, icon: `mdi:car`
- **Backyard** → entity: `binary_sensor.frigate_backyard_motion`, icon: `mdi:tree`
- **Storage Building** → entity: `binary_sensor.frigate_storage_ext_motion`, icon: `mdi:warehouse`

---

## View 4 — Security

Select the **Security** tab. Four sections.

---

### Section 4.1 — Alarm Status

**Add a section:** Click **+ Add Section**

**Card 1 — Alarm panel**

1. **+ Add Card**
2. Search: `Mushroom Alarm`
3. Select **Mushroom: Alarm control panel card**
4. **Entity:** `alarm_control_panel.home_alarm`
5. **Name:** `Security`
6. Click **Save**

> If you don't have a dedicated alarm panel entity, use a **Mushroom Template card** showing the current armed state as a status badge. Create the alarm entity first via the HA Alarm Control Panel integration or a helper input.

---

### Section 4.2 — Live Detections

**Add a section:** Click **+ Add Section**

**Card 1 — Detection status header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Live Detections`

**Card 2 — Per-zone detection chips**

1. **+ Add Card → Mushroom Chips**
2. Add one **Entity chip** per camera zone:
   - `binary_sensor.frigate_front_person` — label: `Front`
   - `binary_sensor.frigate_driveway_wide_motion` — label: `Driveway Wide`
   - `binary_sensor.frigate_driveway_id_person` — label: `Driveway ID`
   - `binary_sensor.frigate_backyard_person` — label: `Backyard`
   - `binary_sensor.frigate_storage_ext_person` — label: `Storage Ext`
   - `binary_sensor.frigate_storage_int_person` — label: `Storage Int`
   - `binary_sensor.driveway_env_motion` — label: `Radar`
3. For each chip, set **Icon color when active:** `red`
4. Click **Save**

---

### Section 4.3 — Face Recognition

**Add a section:** Click **+ Add Section**

> **Requires Phase 4 (Double Take + CompreFace).** Build this section after face recognition is working. Skip for now or add a placeholder title.

**Placeholder card:**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Face Recognition`
3. **Subtitle:** `Coming in Phase 4`
4. Click **Save**

**When Phase 4 is ready, replace with:**

Card 1 — Last match:
- **Mushroom Entity card**
- **Entity:** `sensor.dt_thomas_confidence` *(Double Take sensor)*
- **Name:** `Last Face Match`
- **Secondary info:** `last-changed`

Card 2 — Per-person presence chips:
- **Mushroom Chips** with one entity chip per person:
  - `binary_sensor.dt_thomas_present`
  - `binary_sensor.dt_nils_present`
  - `binary_sensor.dt_hugo_present`

---

### Section 4.4 — Event Log

**Add a section:** Click **+ Add Section**

**Card 1 — Security logbook**

1. **+ Add Card → Logbook**
2. Settings:
   - **Title:** `Event Log`
   - **Entities:** Add all Frigate `binary_sensor.frigate_*_person` and `*_motion` entities
   - **Hours to show:** `48`
3. Click **Save**

---

## View 5 — Operations

Select the **Operations** tab. Five sections.

---

### Section 5.1 — System Health

**Add a section:** Click **+ Add Section**

**Card 1 — HA version and uptime**

1. **+ Add Card → Mushroom Entity card**
2. **Entity:** `update.home_assistant_core_update`
3. **Name:** `Home Assistant`
4. **Icon:** `mdi:home-assistant`
5. Click **Save**

**Card 2 — System uptime**

1. **+ Add Card → Mushroom Entity card**
2. **Entity:** `sensor.uptime` *(requires the Uptime integration — enable via Settings → Devices & Services → Add Integration → Uptime)*
3. **Name:** `Uptime`
4. **Icon:** `mdi:clock-outline`
5. Click **Save**

---

### Section 5.2 — Add-on Status

**Add a section:** Click **+ Add Section** → **Columns: 2**

**Card 1 — Header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Add-ons`

**Cards 2–4 — One per add-on**

For each add-on, add a **Mushroom Entity card**:

| Add-on | Entity | Icon |
|---|---|---|
| Frigate | `binary_sensor.frigate_running` *(or check add-on sensor in HA)* | `mdi:cctv` |
| Double Take | add-on state entity | `mdi:face-recognition` |
| Mosquitto | add-on state entity | `mdi:lan` |
| SSH Terminal | add-on state entity | `mdi:console` |

> Add-on state entities are created automatically by HAOS. Find them in **Settings → Devices & Services → Home Assistant Supervisor → Entities** and search for the add-on name.

---

### Section 5.3 — Storage

**Add a section:** Click **+ Add Section**

**Card 1 — Storage header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Storage`

**Card 2 — SSD usage gauge**

1. **+ Add Card**
2. Search: `Gauge`
3. Select **Gauge card** (built-in)
4. Settings:
   - **Entity:** `sensor.frigate_storage` *(created by the Frigate integration)*
   - **Name:** `Frigate SSD`
   - **Min:** `0` / **Max:** `100`
   - **Severity:** Green 0–70, Amber 70–85, Red 85–100
5. Click **Save**

---

### Section 5.4 — Quick Actions

**Add a section:** Click **+ Add Section** → **Columns: 2**

**Card 1 — Restart HA**

1. **+ Add Card → Button card** (built-in)
2. Settings:
   - **Entity:** `button.restart` *(or use the HA system actions)*
   - **Name:** `Restart HA`
   - **Icon:** `mdi:restart`
   - **Confirmation:** Enable (**Ask for confirmation before performing action**)
3. Click **Save**

**Card 2 — Manual backup**

1. **+ Add Card → Button card**
2. Settings:
   - **Entity:** `button.create_backup` *(Home Assistant Supervisor)*
   - **Name:** `Backup Now`
   - **Icon:** `mdi:cloud-upload`
   - **Confirmation:** Enable
3. Click **Save**

---

### Section 5.5 — Camera Connectivity

**Add a section:** Click **+ Add Section**

**Card 1 — Header**

1. **+ Add Card → Mushroom Title**
2. **Title:** `Camera Connectivity`

**Card 2 — Camera status list**

1. **+ Add Card → Entities card** (built-in)
2. Settings:
   - **Title:** *(leave blank — header card already has the title)*
   - Add one entity per camera (Frigate creates a connectivity sensor per camera):
     - `binary_sensor.frigate_front_camera_running`
     - `binary_sensor.frigate_driveway_wide_camera_running`
     - `binary_sensor.frigate_driveway_id_camera_running`
     - `binary_sensor.frigate_backyard_camera_running`
     - `binary_sensor.frigate_storage_ext_camera_running`
     - `binary_sensor.frigate_storage_int_camera_running`
   - **State color:** Enable (green = OK, red = offline)
3. Click **Save**

---

## Step 3 — Set as Default Dashboard

1. Go to **Settings → Dashboards**
2. Find your new dashboard
3. Click **⋮ → Set as default for this device**

Or set it per user: **Profile (bottom-left avatar) → Default dashboard → select your dashboard**

---

## Section Layout Reference

This table summarises section column counts per view. Use it when the edit mode asks how many columns a section should have.

| View | Section | Columns |
|---|---|---|
| Home | Greeting | 1 |
| Home | Quick Status | 1 |
| Home | Recent Events | 1 |
| Home | Lights On | 1 |
| Cameras | Driveway | 1 (header + full-width cam) then 2 (ID cam + radar) |
| Cameras | Front | 1 |
| Cameras | Backyard & Storage | 2 |
| Rooms | Ground Floor | 2 |
| Rooms | Upper Floor | 2 |
| Rooms | Outdoor | 2 |
| Security | Alarm Status | 1 |
| Security | Live Detections | 1 |
| Security | Face Recognition | 1 |
| Security | Event Log | 1 |
| Operations | System Health | 1 |
| Operations | Add-ons | 2 |
| Operations | Storage | 1 |
| Operations | Quick Actions | 2 |
| Operations | Camera Connectivity | 1 |

---

## Build Order Recommendation

Build in this order to match what's available at each phase:

| Order | What to build | Phase dependency |
|---|---|---|
| 1 | View 3 — Rooms (full) | None — just light entities |
| 2 | View 1 — Home: Greeting + Presence + Lights sections | None |
| 3 | View 5 — Operations (partial, skip camera connectivity) | None |
| 4 | View 4 — Security: Alarm + Event Log sections | None |
| 5 | View 2 — Cameras (all sections) | Phase 2: Frigate running |
| 6 | View 1 — Home: Recent Events section | Phase 2: Frigate running |
| 7 | View 4 — Security: Live Detections section | Phase 2: Frigate running |
| 8 | View 5 — Operations: Camera Connectivity section | Phase 2: Frigate running |
| 9 | View 4 — Security: Face Recognition section | Phase 4: Double Take live |
