# Dashboard Design

Visual layout for the Home Assistant Sections dashboard using Mushroom Cards. Mobile-first. Five views.

**Stack:** Mushroom Cards + Sections layout + custom:mini-graph-card for history.

---

## View 1 — Home

Primary at-a-glance view. Outdoor activity, recent events, quick controls.

```
┌─────────────────────────────────┐
│  ● Good morning, Thomas         │  ← Static greeting (no household presence)
│  Thursday · May 30              │
├─────────────────────────────────┤
│  OUTDOOR ACTIVITY               │
│  ┌────────────────────────┐    │
│  │ 🏠 No one outside      │    │  ← binary_sensor.house_outdoor_presence
│  └────────────────────────┘    │
├─────────────────────────────────┤
│  QUICK STATUS                   │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ 🔒   │ │ 🚗   │ │ 🏠   │   │  ← Security armed / Driveway clear / Mode
│  │ Armed│ │ Clear│ │ Home │   │
│  └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────┤
│  RECENT EVENTS                  │
│  ┌─────────────────────────┐   │
│  │ 🎥 Person at front door  │   │  ← Frigate event list (last 3)
│  │     Today 08:14          │   │
│  │ 🎥 Car in driveway       │   │
│  │     Today 07:52          │   │
│  └─────────────────────────┘   │
├─────────────────────────────────┤
│  LIGHTS ON NOW                  │
│  ┌──────────────────────────┐  │
│  │ Kitchen · Bedroom · Hall │  │  ← Mushroom light chip row
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

**Design notes:**
- No clutter — only active-state information surfaces here
- Household "who is home" is out of scope — [ADR-006](decisions/006-no-face-no-companion-presence.md); use outdoor presence only
- Frigate event list collapses when no recent events
- Quick status row uses color: green = OK, amber = attention, red = alert

---

## View 2 — Cameras

All six feeds in a scannable grid. Tap to expand.

```
┌─────────────────────────────────┐
│  CAMERAS                        │
├─────────────────────────────────┤
│  DRIVEWAY                       │
│  ┌────────────────────────┐    │
│  │  [driveway_wide feed]  │    │  ← Full-width Frigate card, main overview
│  │  Q3558-LVE             │    │
│  └────────────────────────┘    │
│  ┌──────────────┐ ┌──────────┐ │
│  │[driveway_id] │ │[driveway]│ │  ← M2036 + D6210 air quality chip
│  │ M2036        │ │ env ●    │ │
│  └──────────────┘ └──────────┘ │
├─────────────────────────────────┤
│  FRONT                          │
│  ┌────────────────────────┐    │
│  │    [front feed]        │    │  ← P3288 — full width (most important)
│  │    P3288               │    │
│  └────────────────────────┘    │
├─────────────────────────────────┤
│  BACKYARD & STORAGE             │
│  ┌──────────────┐ ┌──────────┐ │
│  │ [backyard]   │ │[stor ext]│ │  ← Side-by-side
│  │  Q1656       │ │  Q1656   │ │
│  └──────────────┘ └──────────┘ │
│  ┌──────────────┐              │
│  │ [stor int]   │              │  ← Interior alone (smaller)
│  │  M1055       │              │
│  └──────────────┘              │
└─────────────────────────────────┘
```

**Design notes:**
- Driveway at the top — highest security relevance
- Each Frigate card shows: live feed, last event chip, motion badge
- Tap any card → full-screen with event history timeline
- D6210 air quality shown as status chips (CO₂, AQI, temp) — not a camera feed

---

## View 3 — Rooms

Room-by-room controls. Organized by floor. Mushroom room cards.

```
┌─────────────────────────────────┐
│  ROOMS                          │
├─────────────────────────────────┤
│  GROUND FLOOR                   │
│  ┌──────────────┐ ┌──────────┐ │
│  │ Kitchen /    │ │  Hall    │ │  ← Mushroom room summary cards
│  │ Living Room  │ │  Ground  │ │
│  │ 💡 3 on      │ │ 💡 Off   │ │
│  └──────────────┘ └──────────┘ │
│  ┌──────────────┐ ┌──────────┐ │
│  │  Bedroom     │ │ Bathroom │ │
│  │ 💡 Off  🌡22°│ │ 💡 Off   │ │
│  └──────────────┘ └──────────┘ │
├─────────────────────────────────┤
│  UPPER FLOOR                    │
│  ┌──────────────┐ ┌──────────┐ │
│  │  TV Room     │ │  Office  │ │
│  │ 💡 On  📺    │ │ 💡 On    │ │
│  └──────────────┘ └──────────┘ │
│  ┌──────────────┐ ┌──────────┐ │
│  │ Nils' Room   │ │Hugo's Rm │ │
│  │ 💡 Off       │ │ 💡 Off   │ │
│  └──────────────┘ └──────────┘ │
│  ┌──────────────┐ ┌──────────┐ │
│  │  Hall Upper  │ │ Bathroom │ │
│  │ 💡 Off       │ │ 💡 Off   │ │
│  └──────────────┘ └──────────┘ │
├─────────────────────────────────┤
│  OUTDOOR                        │
│  ┌──────────────┐ ┌──────────┐ │
│  │  Front       │ │ Driveway │ │
│  │ 💡 Off  🎥   │ │ 🚗 Clear │ │
│  └──────────────┘ └──────────┘ │
│  ┌──────────────┐ ┌──────────┐ │
│  │  Backyard    │ │ Storage  │ │
│  │ 💡 Off  🎥   │ │ 🔒 Closed│ │
│  └──────────────┘ └──────────┘ │
└─────────────────────────────────┘
```

**Design notes:**
- Tap a room card → inline expand with full controls (lights, temp, etc.)
- Show only what's active in the card summary — no noise when everything is off
- Outdoor cards show camera status chip and last event time

---

## View 4 — Security

All security-relevant information in one view. Events, alerts, arm/disarm.

```
┌─────────────────────────────────┐
│  SECURITY                       │
├─────────────────────────────────┤
│  STATUS                         │
│  ┌────────────────────────┐    │
│  │  🔒 ARMED — HOME       │    │  ← Mushroom alarm card, tap to change mode
│  │  Since 22:14           │    │
│  └────────────────────────┘    │
├─────────────────────────────────┤
│  LIVE DETECTIONS                │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │front │ │drive │ │ back │   │  ← Per-zone motion chips, green/amber/red
│  │  ●   │ │  ○   │ │  ○   │   │
│  └──────┘ └──────┘ └──────┘   │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │stor  │ │stor  │ │radar │   │
│  │ext ○ │ │int ○ │ │env ○ │   │
│  └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────┤
│  OUTDOOR PRESENCE               │
│  ┌────────────────────────┐    │
│  │ Someone outside        │    │  ← binary_sensor.house_outdoor_presence
│  │ front · 08:14          │    │
│  └────────────────────────┘    │
├─────────────────────────────────┤
│  EVENT LOG                      │
│  ┌────────────────────────┐    │
│  │ 08:14 · front · Person │    │  ← Logbook filtered to security domain
│  │ 07:52 · driveway · Car │    │
│  │ 07:30 · front · Person │    │
│  │ 23:45 · back · Motion  │    │
│  │            [Show more] │    │
│  └────────────────────────┘    │
└─────────────────────────────────┘
```

**Design notes:**
- Arm/disarm at the top — primary action on this view
- Detection chips update in real-time; tap to see camera feed
- Outdoor presence from camera analytics (`binary_sensor.house_outdoor_presence`) — no face ID ([ADR-006](decisions/006-no-face-no-companion-presence.md))
- Event log is the most valuable persistent element — keep it prominent

---

## View 5 — Operations

System health, admin tasks, config info. Not for daily use.

```
┌─────────────────────────────────┐
│  OPERATIONS                     │
├─────────────────────────────────┤
│  SYSTEM                         │
│  ┌──────────────────────────┐  │
│  │ HA  ●  Running  v2025.x  │  │  ← HA version + uptime
│  │ Uptime: 14d 3h           │  │
│  └──────────────────────────┘  │
├─────────────────────────────────┤
│  ADD-ONS                        │
│  ┌──────────┐ ┌──────────────┐ │
│  │ Frigate  │ │ Insights     │ │
│  │ ● Running│ │ ● Running    │ │
│  └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────────┐ │
│  │ Mosquitto│ │ SSH Terminal │ │
│  │ ● Running│ │ ● Running    │ │
│  └──────────┘ └──────────────┘ │
├─────────────────────────────────┤
│  STORAGE                        │
│  ┌────────────────────────┐    │
│  │ SSD  ████████░░  78%   │    │  ← Storage gauge (Frigate recordings)
│  │ 780 GB / 1 TB used     │    │
│  └────────────────────────┘    │
├─────────────────────────────────┤
│  QUICK ACTIONS                  │
│  ┌────────┐ ┌────────┐         │
│  │Restart │ │Backup  │         │  ← Mushroom button cards
│  │  HA    │ │ Now    │         │
│  └────────┘ └────────┘         │
├─────────────────────────────────┤
│  CAMERAS — CONNECTIVITY         │
│  ┌────────────────────────┐    │
│  │ front          ● OK    │    │  ← Per-camera online/offline status
│  │ driveway_wide  ● OK    │    │
│  │ driveway_id    ● OK    │    │
│  │ backyard       ✕ FAIL  │    │  ← Red when RTSP stream lost
│  │ storage_ext    ● OK    │    │
│  │ storage_int    ● OK    │    │
│  └────────────────────────┘    │
└─────────────────────────────────┘
```

**Design notes:**
- Add-on status tiles are simple: green dot = running, red = stopped
- Storage gauge warns at 85% (trigger cleanup automation)
- Camera connectivity list is critical for ops — shows at a glance if any stream is dead
- No decorative elements — purely functional

---

## Mobile Considerations

- All sections use single-column on narrow screens
- Camera feeds use 16:9 aspect ratio cards — stack vertically on mobile
- Security view chips wrap to 2×3 grid on mobile
- Bottom tab bar for view navigation (built-in Sections layout behavior)

## Card Library Required

| Card | Source | Use |
|---|---|---|
| Mushroom Cards | HACS | Chips, rooms, persons, buttons |
| Frigate Card | HACS | Camera feeds with event overlay |
| mini-graph-card | HACS | History sparklines |
| Sections layout | HA built-in (2024+) | Grid layout engine |
