#!/usr/bin/env python3
"""
Danielsson Insights — Event Normalizer

Subscribes to MQTT and writes canonical events to events/.

Sources:
  - frigate/events        → person, vehicle
  - axis/driveway_env/air/# → environment (every 15 min)
  - axis/+/audio/spl      → metrics (SPL)
  - axis/+/scene/frame    → scene events
  - axis/+/event/ObjectAnalytics/ScenarioOccupancy/# → occupancy start/end
  - homeassistant/lock/+/state → door lock/unlock (Yale via HA MQTT)
  - homeassistant/binary_sensor/+/state → smoke alerts (ZHA via HA MQTT)
  - homeassistant/sensor/+/state → indoor temperature (smoke detectors via HA MQTT)

Run: python scripts/event_normalizer.py
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion

# Allow import from scripts/
sys.path.insert(0, str(Path(__file__).parent))
from correlation_engine import CorrelationEngine  # noqa: E402
from event_store import (  # noqa: E402
    CAMERA_ZONE,
    FRIGATE_LABEL_TYPE,
    MIN_OCCUPANCY_SECONDS,
    OCCUPANCY_COOLDOWN_SECONDS,
    OCCUPANCY_SCENARIOS,
    EventStore,
    TZ,
    make_summary,
)

load_dotenv(Path(__file__).parent.parent / ".env")

MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
FRIGATE_URL = os.environ.get("FRIGATE_URL", f"http://{MQTT_HOST}:5000")

ENV_INTERVAL = 900  # 15 minutes
INDOOR_TEMP_INTERVAL = 900  # 15 min per room — smoke sensors update slowly
INDOOR_TEMP_MIN_DELTA = 0.3  # °C — still write if change exceeds this

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("event_normalizer")

store = EventStore()
correlator = CorrelationEngine(store)
_env_cache: dict[str, float | int] = {}
_last_env_event = 0.0
# zone:scenario → (active, started_at, start_event_written)
_aoa_state: dict[str, tuple[bool, datetime | None, bool]] = {}
_aoa_cooldown: dict[str, datetime] = {}
_scene_last: dict[str, tuple[int, int, int]] = {}
_spl_last_written: dict[str, float] = {}
_lock_state: dict[str, str] = {}
_smoke_state: dict[str, str] = {}
_indoor_temp_last: dict[str, tuple[float, float]] = {}

HA_LOCK_TOPIC_RE = re.compile(r"homeassistant/lock/(?P<entity>[^/]+)/state")
HA_BINARY_TOPIC_RE = re.compile(r"homeassistant/binary_sensor/(?P<entity>[^/]+)/state")
HA_SENSOR_TOPIC_RE = re.compile(r"homeassistant/sensor/(?P<entity>[^/]+)/state")
BIKE_TYPES = frozenset({"Bike", "bike", "Bicycle", "bicycle"})


def _door_zone_map() -> dict[str, str]:
    raw = os.environ.get("YALE_LOCK_ENTITIES", "front_door:front,yale_doorman:front")
    out: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        entity, zone = part.split(":", 1)
        out[entity.strip()] = zone.strip()
    return out


DOOR_ZONE_BY_ENTITY = _door_zone_map()


def _smoke_zone_map() -> dict[str, str]:
    raw = os.environ.get(
        "SMOKE_ENTITIES",
        "heiman_hs1sa_e_plus_ias_zon_2:kok",
    )
    out: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        entity, zone = part.split(":", 1)
        out[entity.strip()] = zone.strip()
    return out


SMOKE_ZONE_BY_ENTITY = _smoke_zone_map()


def _indoor_temp_map() -> dict[str, str]:
    raw = os.environ.get(
        "INDOOR_TEMP_ENTITIES",
        "heiman_hs1sa_e_plus_temperatur_3:kok",
    )
    out: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        entity, zone = part.split(":", 1)
        out[entity.strip()] = zone.strip()
    return out


INDOOR_TEMP_BY_ENTITY = _indoor_temp_map()

AOA_TOPIC_RE = re.compile(
    r"axis/(?P<zone>[^/]+)/event/ObjectAnalytics/ScenarioOccupancy/(?P<scenario>[^/]+)/Active"
)
SPL_METRIC_INTERVAL = 300  # 5 min per zone

# Scene track state: track_id → {zone, type, started_at, positions}
_scene_tracks: dict[str, dict] = {}

# Behavior classification thresholds (seconds)
_BEHAVIOR_RULES = [
    # (max_dur, obj_types, behavior)  — first match wins
    (5,   {"Human", "Person"},  "passthrough"),
    (30,  {"Human", "Person"},  "approach"),
    (120, {"Human", "Person"},  "loitering"),
    (3600,{"Human", "Person"},  "loitering"),
    (60,  {"Car", "Vehicle", "Truck"}, "stopped"),
    (3600,{"Car", "Vehicle", "Truck"}, "parked"),
    (5,   None,                 "passthrough"),
]


def _classify_behavior(obj_type: str, duration_sec: float) -> str:
    for max_dur, types, behavior in _BEHAVIOR_RULES:
        if types is not None and obj_type not in types:
            continue
        if duration_sec <= max_dur:
            return behavior
    return "present"


def _ts_now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def _correlate(event: dict, event_id: str | None) -> None:
    if event_id and not event.get("enriched"):
        correlator.process({**event, "event_id": event_id})


def _download_snapshot(frigate_event_id: str, dest: Path) -> bool:
    """Try HA Frigate proxy, then direct Frigate API."""
    urls = []
    if HA_TOKEN:
        urls.append(
            f"http://{MQTT_HOST}:8123/api/frigate/notifications/"
            f"{frigate_event_id}/snapshot.jpg"
        )
    urls.append(f"{FRIGATE_URL}/api/events/{frigate_event_id}/snapshot.jpg")

    headers = {"Authorization": f"Bearer {HA_TOKEN}"} if HA_TOKEN else {}
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                return True
        except (requests.RequestException, OSError) as exc:
            log.debug("Snapshot fetch failed %s: %s", url, exc)
    return False


def handle_frigate_event(payload: dict) -> None:
    if payload.get("type") != "end":
        return

    after = payload.get("after") or {}
    label = after.get("label")
    camera = after.get("camera")
    if not label or not camera:
        return

    event_type = FRIGATE_LABEL_TYPE.get(label)
    if not event_type:
        return

    zone = CAMERA_ZONE.get(camera, camera)
    frigate_id = after.get("id", "")
    score = after.get("top_score", 0)
    dt = datetime.now(TZ)
    ts = dt.isoformat(timespec="seconds")
    event_id = store.make_event_id(dt, camera, event_type)

    snapshot_rel = None
    if frigate_id:
        snap_path = (
            store.events_root / event_type
            / dt.strftime("%Y/%m/%d")
            / f"{event_id}.jpg"
        )
        if _download_snapshot(frigate_id, snap_path):
            snapshot_rel = str(snap_path.relative_to(store.events_root.parent)).replace("\\", "/")

    event = {
        "event_id": event_id,
        "timestamp": ts,
        "type": event_type,
        "location": {"zone": zone, "camera": camera},
        "confidence": round(float(score), 3),
        "identity": {},
        "metadata": {
            "frigate_id": frigate_id,
            "frigate_label": label,
            "duration": after.get("end_time", 0) - after.get("start_time", 0)
            if after.get("end_time") and after.get("start_time") else None,
        },
        "source": "frigate",
        "enriched": False,
    }
    if snapshot_rel:
        event["snapshot"] = {
            "best_picture": snapshot_rel,
            "thumbnail": snapshot_rel,
        }

    event["summary"] = make_summary(event)
    eid = store.write(event)
    _correlate(event, eid)


def reset_env_state() -> None:
    """Clear caches (for tests)."""
    global _last_env_event, _env_cache, _aoa_state, _aoa_cooldown, _scene_last, _spl_last_written, _lock_state, _smoke_state, _scene_tracks, _indoor_temp_last
    _env_cache = {}
    _last_env_event = 0.0
    _aoa_state = {}
    _aoa_cooldown = {}
    _scene_last = {}
    _spl_last_written = {}
    _lock_state = {}
    _smoke_state = {}
    _indoor_temp_last = {}
    _scene_tracks = {}


def handle_env_metric(topic: str, value: str) -> None:
    global _last_env_event, _env_cache

    metric = topic.split("/")[-1]
    try:
        if metric == "aqi":
            _env_cache[metric] = int(float(value))
        else:
            _env_cache[metric] = round(float(value), 2)
    except ValueError:
        return

    # air_quality_bridge publishes aqi last each 60 s cycle — emit then
    if metric != "aqi":
        return

    now = time.time()
    if now - _last_env_event < ENV_INTERVAL:
        return
    if "temperature" not in _env_cache:
        return

    _last_env_event = now
    ts = _ts_now()
    event = {
        "timestamp": ts,
        "type": "environment",
        "location": {"zone": "driveway_env", "camera": None},
        "metadata": {
            "temperature": _env_cache.get("temperature"),
            "humidity": _env_cache.get("humidity"),
            "co2": _env_cache.get("co2"),
            "voc": _env_cache.get("voc"),
            "nox": _env_cache.get("nox"),
            "pm25": _env_cache.get("pm2_5") or _env_cache.get("pm25"),
            "aqi": _env_cache.get("aqi"),
        },
        "source": "d6210",
        "enriched": False,
        "identity": {},
    }
    event["summary"] = make_summary(event)
    eid = store.write(event)
    if eid:
        store.write_metric(ts, "driveway_env", dict(_env_cache))


def _emit_aoa_occupancy(
    zone: str,
    scenario: str,
    phase: str,
    timestamp: str,
    *,
    duration_seconds: int | None = None,
) -> None:
    meta: dict = {"scenario": scenario, "phase": phase, "active": phase == "start"}
    if duration_seconds is not None:
        meta["duration_seconds"] = duration_seconds
    event = {
        "timestamp": timestamp,
        "type": "occupancy",
        "location": {"zone": zone, "camera": zone},
        "metadata": meta,
        "source": "axis_aoa",
        "enriched": False,
        "identity": {},
    }
    event["summary"] = make_summary(event)
    eid = store.write(event)
    _correlate(event, eid)


def handle_aoa_occupancy(topic: str, payload: str) -> None:
    m = AOA_TOPIC_RE.match(topic)
    if not m:
        return
    zone = m.group("zone")
    scenario = m.group("scenario")
    if scenario not in OCCUPANCY_SCENARIOS:
        return
    try:
        data = json.loads(payload)
        active = bool(data.get("Data", {}).get("active"))
    except json.JSONDecodeError:
        return

    key = f"{zone}:{scenario}"
    was_active, started_at, confirmed = _aoa_state.get(key, (False, None, False))
    now = datetime.now(TZ)

    if active and not was_active:
        cooled = _aoa_cooldown.get(key)
        if cooled and (now - cooled).total_seconds() < OCCUPANCY_COOLDOWN_SECONDS:
            return
        _aoa_state[key] = (True, now, False)
        return

    if active and was_active:
        if not confirmed and started_at:
            elapsed = (now - started_at).total_seconds()
            if elapsed >= MIN_OCCUPANCY_SECONDS:
                _emit_aoa_occupancy(
                    zone,
                    scenario,
                    "start",
                    started_at.isoformat(timespec="seconds"),
                )
                _aoa_state[key] = (True, started_at, True)
        return

    if not active and was_active:
        duration = int((now - started_at).total_seconds()) if started_at else 0
        _aoa_state[key] = (False, None, False)
        _aoa_cooldown[key] = now
        if duration < MIN_OCCUPANCY_SECONDS:
            return
        ts_end = now.isoformat(timespec="seconds")
        if not confirmed and started_at:
            _emit_aoa_occupancy(
                zone,
                scenario,
                "start",
                started_at.isoformat(timespec="seconds"),
            )
        _emit_aoa_occupancy(zone, scenario, "end", ts_end, duration_seconds=duration)


def handle_scene_frame(topic: str, payload: str) -> None:
    zone = topic.split("/")[1]
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return
    detections = data.get("detections") or data.get("data", {}).get("detections") or []
    persons = sum(1 for d in detections if d.get("type") in ("Human", "human", "Person"))
    vehicles = sum(1 for d in detections if d.get("type") in ("Car", "car", "Vehicle", "Truck"))
    bicycles = sum(1 for d in detections if d.get("type") in BIKE_TYPES)
    if persons == 0 and vehicles == 0 and bicycles == 0:
        return
    last = _scene_last.get(zone)
    if last == (persons, vehicles, bicycles):
        return
    _scene_last[zone] = (persons, vehicles, bicycles)

    ts = _ts_now()
    event = {
        "timestamp": ts,
        "type": "scene",
        "location": {"zone": zone, "camera": zone},
        "metadata": {
            "persons": persons,
            "vehicles": vehicles,
            "bicycles": bicycles,
            "detections": len(detections),
        },
        "source": "axis_scene",
        "enriched": False,
        "identity": {},
    }
    event["summary"] = make_summary(event)
    eid = store.write(event)
    _correlate(event, eid)


def handle_scene_track(topic: str, payload: str) -> None:
    """Process Axis scene/track events and classify behavior on LOST."""
    zone = topic.split("/")[1]
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return

    # Support both top-level and nested data formats
    track_id = data.get("track_id") or data.get("id")
    event_type = (data.get("event") or data.get("type", "")).upper()
    obj_type = data.get("type") or data.get("objectType") or "Unknown"
    duration_sec = data.get("duration_sec") or data.get("duration_seconds")

    if not track_id:
        return

    key = f"{zone}:{track_id}"

    if event_type == "NEW":
        _scene_tracks[key] = {
            "zone": zone,
            "obj_type": obj_type,
            "started_at": datetime.now(TZ),
        }
        return

    if event_type in ("LOST", "ENDED", "END"):
        track = _scene_tracks.pop(key, None)
        started_at = track["started_at"] if track else None
        if duration_sec is None and started_at:
            duration_sec = (datetime.now(TZ) - started_at).total_seconds()
        if duration_sec is None:
            duration_sec = 0.0

        behavior = _classify_behavior(obj_type, duration_sec)

        ts = _ts_now()
        # Map Axis object type to our event type vocabulary
        event_obj_type = "vehicle" if obj_type in ("Car", "car", "Vehicle", "Truck") else (
            "bicycle" if obj_type in BIKE_TYPES else "person"
        )
        meta = {
            "track_id": track_id,
            "obj_type": obj_type,
            "duration_seconds": round(duration_sec, 1),
            "behavior": behavior,
            "track_event": "LOST",
        }

        # Write a raw person/vehicle/bicycle event for correlation
        raw_event = {
            "timestamp": ts,
            "type": event_obj_type,
            "location": {"zone": zone, "camera": zone},
            "metadata": meta,
            "source": "axis_scene_track",
            "enriched": False,
            "identity": {},
        }
        raw_event["summary"] = make_summary(raw_event)
        eid = store.write(raw_event)
        _correlate(raw_event, eid)

        # Write a dedicated behavior event for the behavior timeline lane
        # (skips passthrough — too noisy)
        if behavior != "passthrough":
            bev = {
                "timestamp": ts,
                "type": "behavior",
                "location": {"zone": zone, "camera": zone},
                "metadata": meta,
                "source": "axis_scene_track",
                "enriched": False,
                "identity": {},
            }
            bev["summary"] = f"{behavior.capitalize()} · {event_obj_type} at {zone} ({int(duration_sec)}s)"
            store.write(bev)

        log.info("Scene track LOST: %s %s %s (%.0fs → %s)", zone, obj_type, track_id, duration_sec, behavior)


def handle_door_lock(topic: str, payload: str) -> None:
    m = HA_LOCK_TOPIC_RE.match(topic)
    if not m:
        return
    entity = m.group("entity")
    zone = DOOR_ZONE_BY_ENTITY.get(entity)
    if not zone:
        log.debug("Door entity %s not in YALE_LOCK_ENTITIES — skip", entity)
        return

    state = payload.strip().lower()
    if state not in ("locked", "unlocked"):
        return

    prev = _lock_state.get(entity)
    _lock_state[entity] = state
    if prev == state:
        return

    action = "unlocked" if state == "unlocked" else "locked"
    ts = _ts_now()
    event = {
        "timestamp": ts,
        "type": "door",
        "location": {"zone": zone, "camera": None},
        "metadata": {
            "action": action,
            "entity_id": f"lock.{entity}",
            "lock_state": state,
        },
        "source": "ha_mqtt",
        "enriched": False,
        "identity": {},
    }
    event["summary"] = make_summary(event)
    eid = store.write(event)
    _correlate(event, eid)


def handle_smoke_sensor(topic: str, payload: str) -> None:
    m = HA_BINARY_TOPIC_RE.match(topic)
    if not m:
        return
    entity = m.group("entity")
    zone = SMOKE_ZONE_BY_ENTITY.get(entity)
    if not zone:
        return

    state = payload.strip().lower()
    if state not in ("on", "off"):
        return

    prev = _smoke_state.get(entity)
    _smoke_state[entity] = state
    if prev == state:
        return
    if state != "on":
        return

    ts = _ts_now()
    event = {
        "timestamp": ts,
        "type": "smoke",
        "location": {"zone": zone, "camera": None},
        "metadata": {
            "entity_id": f"binary_sensor.{entity}",
            "alarm_state": state,
        },
        "source": "ha_mqtt",
        "enriched": False,
        "identity": {},
    }
    event["summary"] = make_summary(event)
    store.write(event)


def handle_indoor_temp(topic: str, payload: str) -> None:
    m = HA_SENSOR_TOPIC_RE.match(topic)
    if not m:
        return
    entity = m.group("entity")
    zone = INDOOR_TEMP_BY_ENTITY.get(entity)
    if not zone:
        return
    try:
        temp = round(float(payload.strip()), 2)
    except ValueError:
        return

    now = time.time()
    last_ts, last_val = _indoor_temp_last.get(zone, (0.0, temp))
    if (
        now - last_ts < INDOOR_TEMP_INTERVAL
        and abs(temp - last_val) < INDOOR_TEMP_MIN_DELTA
    ):
        return
    _indoor_temp_last[zone] = (now, temp)
    store.write_metric(_ts_now(), zone, {"temperature": temp, "source": "smoke_detector"})


def handle_audio_spl(topic: str, payload: str) -> None:
    zone = topic.split("/")[1]
    try:
        data = json.loads(payload)
        spl = float(data.get("max_spl") or data.get("spl"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return
    now = time.time()
    last = _spl_last_written.get(zone, 0.0)
    if now - last < SPL_METRIC_INTERVAL:
        return
    _spl_last_written[zone] = now
    store.write_metric(_ts_now(), zone, {"spl": round(spl, 1)})


def on_message(client, userdata, msg):
    try:
        if msg.topic == "frigate/events":
            handle_frigate_event(json.loads(msg.payload))
        elif msg.topic.startswith("axis/driveway_env/air/"):
            handle_env_metric(msg.topic, msg.payload.decode())
        elif msg.topic.endswith("/audio/spl"):
            handle_audio_spl(msg.topic, msg.payload.decode())
        elif msg.topic.endswith("/scene/frame"):
            handle_scene_frame(msg.topic, msg.payload.decode())
        elif msg.topic.endswith("/scene/track"):
            handle_scene_track(msg.topic, msg.payload.decode())
        elif "/ScenarioOccupancy/" in msg.topic:
            handle_aoa_occupancy(msg.topic, msg.payload.decode())
        elif HA_LOCK_TOPIC_RE.match(msg.topic):
            handle_door_lock(msg.topic, msg.payload.decode())
        elif HA_BINARY_TOPIC_RE.match(msg.topic):
            handle_smoke_sensor(msg.topic, msg.payload.decode())
        elif HA_SENSOR_TOPIC_RE.match(msg.topic):
            handle_indoor_temp(msg.topic, msg.payload.decode())
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.warning("Bad message on %s: %s", msg.topic, exc)


def main() -> None:
    if not MQTT_USER or not MQTT_PASS:
        raise SystemExit("MQTT_USER and MQTT_PASS must be set in .env")

    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="event_normalizer")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_message = on_message
    client.connect(MQTT_HOST, 1883, 60)

    client.subscribe("frigate/events")
    client.subscribe("axis/driveway_env/air/#")
    client.subscribe("axis/+/audio/spl")
    client.subscribe("axis/+/scene/frame")
    client.subscribe("axis/+/scene/track")
    client.subscribe("axis/+/event/ObjectAnalytics/ScenarioOccupancy/#")
    client.subscribe("homeassistant/lock/+/state")
    client.subscribe("homeassistant/binary_sensor/+/state")
    client.subscribe("homeassistant/sensor/+/state")

    log.info("Event normalizer started  mqtt=%s  store=%s", MQTT_HOST, store.events_root)
    client.loop_forever()


if __name__ == "__main__":
    main()
