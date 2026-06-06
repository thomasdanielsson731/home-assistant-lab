#!/usr/bin/env python3
"""
Danielsson Insights — Event Normalizer

Subscribes to MQTT and writes canonical events to events/.

Sources:
  - frigate/events        → person, vehicle
  - double_take/matches   → identity enrichment
  - axis/driveway_env/air/# → environment (every 15 min)

Run: python scripts/event_normalizer.py
"""

from __future__ import annotations

import json
import logging
import os
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
from event_store import (  # noqa: E402
    CAMERA_ZONE,
    FRIGATE_LABEL_TYPE,
    EventStore,
    TZ,
    make_summary,
)

load_dotenv(Path(__file__).parent.parent / ".env")

MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASS"]
HA_TOKEN = os.environ.get("HA_TOKEN", "")
FRIGATE_URL = os.environ.get("FRIGATE_URL", f"http://{MQTT_HOST}:5000")

ENV_INTERVAL = 900  # 15 minutes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("event_normalizer")

store = EventStore()
_env_cache: dict[str, float | int] = {}
_last_env_event = 0.0


def _ts_now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


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
        except requests.RequestException as exc:
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
    store.write(event)


def handle_double_take(payload: dict) -> None:
    match = payload.get("match") or payload.get("payload", {}).get("match")
    if not match:
        return
    name = match.get("name") or match.get("id")
    if not name:
        return
    camera = payload.get("camera", "front")
    conf = match.get("confidence", 0)
    if conf > 1:
        conf = conf / 100.0
    store.attach_identity(camera, name, float(conf))


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
    store.write(event)


def on_message(client, userdata, msg):
    try:
        if msg.topic == "frigate/events":
            handle_frigate_event(json.loads(msg.payload))
        elif msg.topic == "double_take/matches":
            data = json.loads(msg.payload)
            if isinstance(data, list):
                for item in data:
                    handle_double_take(item)
            else:
                handle_double_take(data)
        elif msg.topic.startswith("axis/driveway_env/air/"):
            handle_env_metric(msg.topic, msg.payload.decode())
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.warning("Bad message on %s: %s", msg.topic, exc)


def main() -> None:
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="event_normalizer")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_message = on_message
    client.connect(MQTT_HOST, 1883, 60)

    client.subscribe("frigate/events")
    client.subscribe("double_take/matches")
    client.subscribe("axis/driveway_env/air/#")

    log.info("Event normalizer started  mqtt=%s  store=%s", MQTT_HOST, store.events_root)
    client.loop_forever()


if __name__ == "__main__":
    main()
