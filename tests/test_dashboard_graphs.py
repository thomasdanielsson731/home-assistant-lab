"""Regression tests for dashboard graph cards and recorder compatibility."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HA = REPO / "config" / "home-assistant"
DASHBOARDS = HA / "dashboards"

# Entities referenced by history-graph / statistics-graph cards (canonical list).
GRAPH_ENTITIES = frozenset(
    {
        "sensor.driveway_env_temperature",
        "sensor.driveway_env_humidity",
        "sensor.driveway_env_co2",
        "sensor.driveway_env_co2_graph",
        "sensor.driveway_env_aqi",
        "sensor.driveway_env_aqi_graph",
        "sensor.driveway_env_pm2_5",
        "sensor.driveway_env_data_age",
        "sensor.heiman_hs1sa_e_plus_temperatur",
        "sensor.heiman_hs1sa_e_plus_temperatur_2",
        "sensor.heiman_hs1sa_e_plus_temperatur_3",
        "sensor.house_indoor_temperature",
        "sensor.front_audio_spl",
        "sensor.driveway_wide_audio_spl",
        "sensor.backyard_audio_spl",
    }
)

# Declared in mqtt_sensors or templates — graph cards must reference known sources.
DECLARED_SENSOR_SOURCES = frozenset(
    {
        "sensor.driveway_env_temperature",
        "sensor.driveway_env_humidity",
        "sensor.driveway_env_co2",
        "sensor.driveway_env_aqi",
        "sensor.driveway_env_pm2_5",
        "sensor.driveway_env_co2_graph",
        "sensor.driveway_env_aqi_graph",
        "sensor.driveway_env_data_age",
        "sensor.house_indoor_temperature",
        "sensor.heiman_hs1sa_e_plus_temperatur",
        "sensor.heiman_hs1sa_e_plus_temperatur_2",
        "sensor.heiman_hs1sa_e_plus_temperatur_3",
        "sensor.front_audio_spl",
        "sensor.driveway_wide_audio_spl",
        "sensor.backyard_audio_spl",
    }
)

RECORDER_EXCLUDE_GLOBS = [
    "image.*",
    "binary_sensor.*_motion",
    "binary_sensor.*_scene_object_present",
    "sensor.*_scene_persons",
    "sensor.*_scene_vehicles",
]


def _load_dashboard(filename: str) -> dict:
    text = (DASHBOARDS / filename).read_text(encoding="utf-8")
    text = re.sub(r"!secret\s+\S+", '"/secret/placeholder"', text)
    return yaml.safe_load(text)


def _walk_cards(node, found: list[dict]) -> None:
    if isinstance(node, dict):
        if node.get("type") in ("history-graph", "statistics-graph"):
            found.append(node)
        for value in node.values():
            _walk_cards(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_cards(item, found)


def _graph_entities_from_dashboard(filename: str) -> set[str]:
    data = _load_dashboard(filename)
    cards: list[dict] = []
    _walk_cards(data, cards)
    entities: set[str] = set()
    for card in cards:
        card_type = card["type"]
        raw = card.get("entities") or []
        for entry in raw:
            if isinstance(entry, str):
                eid = entry
            elif isinstance(entry, dict):
                eid = entry.get("entity", "")
            else:
                continue
            if eid.startswith("sensor."):
                entities.add(eid)
    return entities


def _recorder_excluded(entity_id: str) -> bool:
    domain, _ = entity_id.split(".", 1)
    if domain in {"automation", "script", "update", "persistent_notification"}:
        return True
    for pattern in RECORDER_EXCLUDE_GLOBS:
        if fnmatch.fnmatch(entity_id, pattern):
            return True
    return False


def test_graph_entities_not_recorder_excluded():
    for eid in GRAPH_ENTITIES:
        assert not _recorder_excluded(eid), f"{eid} matches recorder exclude — graphs will be empty"


def test_dashboard_graph_entities_are_declared():
    used = _graph_entities_from_dashboard("home-tech.yaml") | _graph_entities_from_dashboard(
        "home-rooms.yaml"
    )
    assert used, "expected graph entities in home-tech or home-rooms"
    unknown = used - DECLARED_SENSOR_SOURCES
    assert not unknown, f"graph cards reference undeclared sensors: {unknown}"


def test_home_tech_uses_graph_filtered_co2_aqi():
    text = (DASHBOARDS / "home-tech.yaml").read_text(encoding="utf-8")
    assert "sensor.driveway_env_co2_graph" in text
    assert "sensor.driveway_env_aqi_graph" in text
    # Raw CO2/AQI should not appear in Historik graphs (startup zeros mislead).
    historik = text.split("UTE LUFT (7 DAGAR)", 1)[1].split("UTE LUFT (90 DAGAR)", 1)[0]
    assert "sensor.driveway_env_co2_graph" in historik
    assert "entity: sensor.driveway_env_co2\n" not in historik


def test_home_tech_live_no_cramped_history_grid():
    text = (DASHBOARDS / "home-tech.yaml").read_text(encoding="utf-8")
    live_section = text.split("UTE LUFT (D6210)", 1)[1].split("SENASTE BILDER", 1)[0]
    assert "history-graph" not in live_section
    assert "/house-graphs" in live_section


def test_home_tech_historik_points_to_environment():
    text = (DASHBOARDS / "home-tech.yaml").read_text(encoding="utf-8")
    historik = text.split("path: historik", 1)[1]
    assert "START HÄR" in historik
    assert "Öppna Environment" in historik


def test_home_rooms_has_indoor_history_graph():
    text = (DASHBOARDS / "home-rooms.yaml").read_text(encoding="utf-8")
    assert "type: history-graph" in text
    assert "hours_to_show: 168" in text
    assert "sensor.heiman_hs1sa_e_plus_temperatur" in text


def test_graph_sensors_template_exists():
    text = (HA / "templates" / "graph_sensors.yaml").read_text(encoding="utf-8")
    assert "driveway_env_co2_graph" in text
    assert "driveway_env_aqi_graph" in text
    assert "driveway_env_data_age" in text


def test_insights_rest_includes_bicycle_counter():
    text = (HA / "mqtt_sensors" / "insights_counters.yaml").read_text(encoding="utf-8")
    assert "insights_bicycles_24h" in text
    assert "danielsson/insights/bicycles_24h" in text
    bridge = (REPO / "scripts" / "insights_counters_bridge.py").read_text(encoding="utf-8")
    assert "bicycles" in bridge
    assert "danielsson/insights/" in bridge
    assert "counters_bridge_ok" in bridge


def test_insights_mqtt_bridge_heartbeat_sensor():
    text = (HA / "mqtt_sensors" / "insights_counters.yaml").read_text(encoding="utf-8")
    assert "insights_counters_bridge_ok" in text
    assert "counters_bridge_ok" in text


def test_insights_counters_offline_automation():
    text = (HA / "automations/security/insights_counters_offline.yaml").read_text(encoding="utf-8")
    assert "insights_counters_offline_alert" in text
    assert "sensor.insights_counters_bridge_ok" in text


def test_house_context_zones_label_covers_all_zones():
    text = (HA / "templates" / "house_context.yaml").read_text(encoding="utf-8")
    for label in ("Bakgård", "Förråd ut", "Förråd in", "backyard_scene_object_present", "loiter"):
        assert label in text


def test_statistics_graph_sources_have_state_class():
    """Outdoor MQTT + graph templates must declare state_class for statistics engine."""
    air = (HA / "mqtt_sensors" / "air_quality.yaml").read_text(encoding="utf-8")
    assert air.count("state_class: measurement") >= 5
    graph = (HA / "templates" / "graph_sensors.yaml").read_text(encoding="utf-8")
    assert "state_class: measurement" in graph
    audio = (HA / "mqtt_sensors" / "audio_analytics.yaml").read_text(encoding="utf-8")
    assert audio.count("state_class: measurement") == 3


def test_insights_display_coalesce_templates():
    text = (HA / "templates" / "insights_display.yaml").read_text(encoding="utf-8")
    for key in (
        "insights_events_24h_display",
        "insights_persons_24h_display",
        "insights_bicycles_24h_display",
    ):
        assert key in text
    assert "insights_events_24h_2" in text


def test_no_stale_rest_insights_yaml():
    assert not (HA / "rest" / "insights.yaml").exists()


def test_home_events_embeds_clickable_list():
    text = (DASHBOARDS / "home-events.yaml").read_text(encoding="utf-8")
    assert "sensor.insights_persons_24h_display" in text
    assert "insights_bicycles_24h_display" in text
    assert "panel: true" in text
    assert "type: iframe" in text
    assert "min-width: 1025px" in text
    assert "house-timeline" not in text


def test_home_cameras_no_admin_perimeter_link():
    text = (DASHBOARDS / "home-cameras.yaml").read_text(encoding="utf-8")
    assert "home-tech" not in text
    assert "F✓" not in text


def test_home_security_no_analytics_chip():
    text = (DASHBOARDS / "home-security.yaml").read_text(encoding="utf-8")
    assert "house-timeline" not in text
    assert "backyard_person_occupancy" in text


def test_home_rooms_yaml_no_duplicate_service():
    text = (DASHBOARDS / "home-rooms.yaml").read_text(encoding="utf-8")
    assert text.count("service: script.light_turn_off_bedroom") == 1
    assert "confirmation:" in text
