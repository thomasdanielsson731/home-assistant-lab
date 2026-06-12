#!/usr/bin/env python3
"""Lab health check — cameras, env sensors, bridges, events. No manual steps."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from event_store import TZ  # noqa: E402

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

HA_HOST = os.environ.get("HA_HOST", "192.168.68.175")
HA_TOKEN = os.environ.get("HA_TOKEN")
if not HA_TOKEN:
    sys.exit("HA_TOKEN not set in .env")

HEADERS = {"Authorization": f"Bearer {HA_TOKEN}"}
BASE = f"http://{HA_HOST}:8123/api"

CAMERAS = [
    "camera.front",
    "camera.driveway_wide",
    "camera.driveway_id",
    "camera.backyard",
    "camera.storage_ext",
    "camera.storage_int",
]

ENV_SENSORS = [
    "sensor.driveway_env_temperature",
    "sensor.driveway_env_humidity",
    "sensor.driveway_env_co2",
    "sensor.driveway_env_aqi",
    "sensor.driveway_env_pm2_5",
]

AOA_SENSORS = [
    "binary_sensor.front_aoa_person",
    "binary_sensor.driveway_wide_aoa_person",
    "binary_sensor.backyard_aoa_person",
]

SPL_SENSORS = [
    "sensor.front_audio_spl",
    "sensor.driveway_wide_audio_spl",
    "sensor.backyard_audio_spl",
]

SCENE_SENSORS = [
    "binary_sensor.front_scene_object_present",
    "binary_sensor.driveway_wide_scene_object_present",
    "binary_sensor.driveway_id_scene_object_present",
    "binary_sensor.backyard_scene_object_present",
    "binary_sensor.storage_ext_scene_object_present",
    "binary_sensor.storage_int_scene_object_present",
    "sensor.front_scene_persons",
    "sensor.driveway_wide_scene_persons",
    "sensor.storage_ext_scene_persons",
    "sensor.storage_int_scene_persons",
]

BRIDGE_SCRIPTS = [
    "air_quality_bridge.py",
    "audio_bridge.py",
    "aoa_bridge.py",
    "event_normalizer.py",
    "timeline_server.py",
    "influx_metrics_bridge.py",
    "bridge_watchdog.py",
]

BRIDGE_SERVICES = [
    "air_quality_bridge",
    "audio_bridge",
    "aoa_bridge",
    "event_normalizer",
    "timeline_server",
]

HEARTBEAT_MAX_AGE_SECONDS = 300
METRIC_MAX_AGE_SECONDS = 600

INSIGHTS_BASE = f"http://{HA_HOST}:8765"


def insights_addon_running() -> bool:
    """True when the platform runs as the HAOS add-on (timeline on HA host)."""
    try:
        r = requests.get(f"{INSIGHTS_BASE}/timeline", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def fetch_insights_json(path: str) -> list | None:
    try:
        r = requests.get(f"{INSIGHTS_BASE}{path}", timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        return data if isinstance(data, list) else None
    except (requests.RequestException, ValueError):
        return None


def get_state(entity_id: str) -> dict | None:
    r = requests.get(f"{BASE}/states/{entity_id}", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def ok_state(state: str) -> bool:
    return state not in ("unavailable", "unknown", "")


def check_entity_group(
    title: str, entities: list[str], issues: list[str], *, required: bool = True
) -> None:
    print(f"\n{title}:")
    for ent in entities:
        s = get_state(ent)
        if not s:
            mark = "FAIL" if required else "WARN"
            print(f"  {mark:4}  {ent} — not found")
            if required:
                issues.append(ent)
            continue
        st = s["state"]
        mark = "OK" if ok_state(st) else "WARN"
        print(f"  {mark:4}  {ent}: {st}")
        if not ok_state(st) and required:
            issues.append(ent)


def is_script_running(script: str) -> bool:
    if sys.platform != "win32":
        return True
    ps = (
        f"Get-CimInstance Win32_Process | "
        f"Where-Object {{ $_.CommandLine -like '*{script}*' }} | "
        f"Select-Object -First 1 | ConvertTo-Json"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps],
            text=True,
            timeout=15,
        ).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return bool(out and out != "null")


def running_bridge_scripts() -> set[str]:
    if sys.platform != "win32":
        return set(BRIDGE_SCRIPTS)
    return {s for s in BRIDGE_SCRIPTS if is_script_running(s)}


def count_timeline_events(timeline: Path, event_type: str) -> int:
    if not timeline.exists():
        return 0
    count = 0
    for line in timeline.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            if json.loads(line).get("type") == event_type:
                count += 1
        except json.JSONDecodeError:
            continue
    return count


def main() -> int:
    issues: list[str] = []
    print("=== Danielsson Insights Health Check ===\n")

    check_entity_group("Cameras (Frigate)", CAMERAS, issues)

    check_entity_group("Outdoor environment", ENV_SENSORS, issues)

    check_entity_group("AOA presence", AOA_SENSORS, issues, required=False)

    check_entity_group("Audio SPL", SPL_SENSORS, issues)

    check_entity_group("Scene analytics", SCENE_SENSORS, issues, required=False)

    addon_mode = insights_addon_running()

    print("\nInsights platform:")
    if addon_mode:
        print(f"  OK    HAOS add-on — {INSIGHTS_BASE}/timeline")
    else:
        print(f"  WARN  {INSIGHTS_BASE}:8765 not responding — checking dev PC bridges")

    if addon_mode:
        rows = fetch_insights_json("/api/v1/metrics?hours=1") or []
        latest: dict[str, datetime] = {}
        for row in rows:
            zone = str(row.get("zone", ""))
            if not zone.startswith("_bridge/"):
                continue
            service = zone.split("/", 1)[1]
            try:
                ts = datetime.fromisoformat(row["timestamp"])
            except (KeyError, ValueError):
                continue
            if service not in latest or ts > latest[service]:
                latest[service] = ts

        print("\nBridge heartbeats (add-on API):")
        if not latest:
            print("  WARN  No _bridge/* heartbeats — bridge_watchdog not running in add-on")
            issues.append("bridge_heartbeats")
        else:
            for service in BRIDGE_SERVICES:
                ts = latest.get(service)
                if not ts:
                    print(f"  WARN  {service} — no heartbeat")
                    issues.append(f"heartbeat:{service}")
                else:
                    age = int((datetime.now(TZ) - ts).total_seconds())
                    if age > HEARTBEAT_MAX_AGE_SECONDS:
                        print(f"  WARN  {service} — stale ({age}s ago)")
                        issues.append(f"heartbeat:{service}")
                    else:
                        print(f"  OK    {service} — {ts.strftime('%H:%M:%S')}")

        env_rows = [r for r in rows if r.get("zone") == "driveway_env"]
        if env_rows:
            print(f"  OK    driveway_env metrics — {len(env_rows)} samples last hour")
        else:
            print("  WARN  driveway_env metrics — none last hour")
            issues.append("metrics:driveway_env")
    else:
        print("\nDev PC bridges:")
        if sys.platform != "win32":
            print("  SKIP  bridge process check (not Windows)")
        else:
            running = running_bridge_scripts()
            for script in BRIDGE_SCRIPTS:
                name = script.replace(".py", "")
                if script in running:
                    print(f"  OK    {name}")
                else:
                    print(f"  WARN  {name} — not running (run start-bridges.ps1)")
                    issues.append(f"bridge:{name}")

        metrics_path = Path(__file__).parent.parent / "events" / "metrics.jsonl"
        print("\nBridge heartbeats (metrics.jsonl):")
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from lab_heartbeat import (  # noqa: E402
                is_stale,
                last_metric_ts_for_zone,
                read_bridge_heartbeats,
            )

            heartbeats = read_bridge_heartbeats(metrics_path)
            if not heartbeats:
                print("  WARN  No bridge heartbeats yet — run bridge_watchdog.py")
                issues.append("bridge_heartbeats")
            else:
                for service in BRIDGE_SERVICES:
                    ts = heartbeats.get(service)
                    if not ts:
                        print(f"  WARN  {service} — no heartbeat")
                        issues.append(f"heartbeat:{service}")
                    elif is_stale(ts, HEARTBEAT_MAX_AGE_SECONDS):
                        age = int((datetime.now(TZ) - ts).total_seconds())
                        print(f"  WARN  {service} — stale ({age}s ago)")
                        issues.append(f"heartbeat:{service}")
                    else:
                        print(f"  OK    {service} — {ts.strftime('%H:%M:%S')}")

            env_ts = last_metric_ts_for_zone(metrics_path, "driveway_env")
            if env_ts is None:
                print("  WARN  driveway_env metrics — none yet")
            elif is_stale(env_ts, METRIC_MAX_AGE_SECONDS):
                age = int((datetime.now(TZ) - env_ts).total_seconds())
                print(f"  WARN  driveway_env metrics — stale ({age}s ago)")
                issues.append("metrics:driveway_env")
            else:
                print(f"  OK    driveway_env metrics — {env_ts.strftime('%H:%M:%S')}")
        except ImportError:
            print("  WARN  lab_heartbeat not importable")

    print("\nInfluxDB metrics:")
    influx_url = os.environ.get("INFLUX_URL", "").strip()
    if not influx_url:
        print("  SKIP  INFLUX_URL not set (metrics stay in metrics.jsonl)")
    else:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            import influx_metrics_bridge as influx_bridge  # noqa: E402

            if influx_bridge.ping():
                print(f"  OK    {influx_url} (ping)")
                # verify-influxdb.py has a hyphen — load via importlib
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "verify_influxdb", Path(__file__).parent / "verify-influxdb.py"
                )
                verify_influxdb = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(verify_influxdb)
                if verify_influxdb.main() != 0:
                    print("  WARN  Influx auth/write — run verify-influxdb.py")
                    issues.append("influxdb_auth")
            else:
                print(f"  WARN  {influx_url} — not reachable")
                issues.append("influxdb")
        except (ImportError, FileNotFoundError):
            print("  WARN  influx_metrics_bridge not importable")

    print("\nTimeline UI:")
    if addon_mode:
        print(f"  OK    {INSIGHTS_BASE}/timeline (HTTP 200)")
    else:
        try:
            with socket.create_connection(("127.0.0.1", 8765), timeout=2):
                print("  OK    http://localhost:8765 (port open)")
        except OSError:
            print("  WARN  http://localhost:8765 — port not listening")
            if "timeline_server.py" not in running_bridge_scripts():
                issues.append("timeline_ui")

    print("\nEvent timeline:")
    if addon_mode:
        events = fetch_insights_json("/api/v1/events?hours=24")
        if events is None:
            print("  WARN  Could not query add-on events API")
            issues.append("timeline")
        else:
            person_n = sum(1 for e in events if e.get("type") == "person")
            vehicle_n = sum(1 for e in events if e.get("type") == "vehicle")
            print(f"  OK    {len(events)} events last 24 h (add-on API)")
            print(f"        Frigate person: {person_n} · vehicle: {vehicle_n}")
            if events:
                last = events[0]
                print(
                    f"        Last: {last.get('type')} @ "
                    f"{last.get('location', {}).get('zone')} — "
                    f"{last.get('timestamp', '')[:19]}"
                )
    else:
        timeline = Path(__file__).parent.parent / "events" / "timeline.jsonl"
        if timeline.exists():
            lines = [ln for ln in timeline.read_text(encoding="utf-8").splitlines() if ln.strip()]
            person_n = count_timeline_events(timeline, "person")
            vehicle_n = count_timeline_events(timeline, "vehicle")
            print(f"  OK    {len(lines)} events in {timeline.name}")
            print(f"        Frigate person: {person_n} · vehicle: {vehicle_n}")
            if person_n == 0:
                print("  WARN  No person events yet — normalizer needs Frigate activity")
            if lines:
                last = json.loads(lines[-1])
                print(
                    f"        Last: {last.get('type')} @ "
                    f"{last.get('location', {}).get('zone')} — "
                    f"{last.get('timestamp', '')[:19]}"
                )
        else:
            print("  WARN  No timeline yet — run event_normalizer.py")
            issues.append("timeline")

    print()
    if issues:
        print(f"Issues: {len(issues)} ({', '.join(issues[:8])}{'...' if len(issues) > 8 else ''})")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
