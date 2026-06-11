#!/usr/bin/env python3
"""
Presence fusion — combine HA Companion, Double Take, and outdoor analytics.

Used by event_normalizer (identity hints) and HA template sensors (dashboard).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import requests

log = logging.getLogger("presence_fusion")

ENTRANCE_ZONES = frozenset({"front", "driveway", "driveway_id"})

HOUSEHOLD: tuple[dict[str, str], ...] = (
    {"name": "Thomas", "person": "person.thomasx", "dt_key": "thomas"},
    {"name": "Nils", "person": "person.nils_2", "dt_key": "nils"},
    {"name": "Hugo", "person": "person.hugo", "dt_key": "hugo"},
    {"name": "Anna", "person": "person.anna", "dt_key": "anna"},
)

FUSED_HOME = "home"
FUSED_FACE = "face"
FUSED_AWAY = "away"


@dataclass
class FusedMember:
    name: str
    person_entity: str
    state: str
    label: str
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def counts_as_home(self) -> bool:
        return self.state in (FUSED_HOME, FUSED_FACE)


def _dt_entities(dt_key: str) -> tuple[str, str]:
    return (
        f"binary_sensor.dt_{dt_key}_present",
        f"sensor.dt_{dt_key}_confidence",
    )


def _entity_state(states: dict[str, dict], entity_id: str) -> str | None:
    row = states.get(entity_id)
    if not row:
        return None
    st = row.get("state")
    if st in (None, "unknown", "unavailable", ""):
        return None
    return st


def _entity_float(states: dict[str, dict], entity_id: str) -> float:
    raw = _entity_state(states, entity_id)
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def fuse_member(member: dict[str, str], states: dict[str, dict]) -> FusedMember:
    name = member["name"]
    person_entity = member["person"]
    present_ent, conf_ent = _dt_entities(member["dt_key"])

    person_st = _entity_state(states, person_entity)
    face_on = _entity_state(states, present_ent) == "on"
    confidence = _entity_float(states, conf_ent)
    if confidence > 1:
        confidence = confidence / 100.0

    sources: list[str] = []
    if person_st == "home":
        sources.append("companion")
        return FusedMember(
            name=name,
            person_entity=person_entity,
            state=FUSED_HOME,
            label="Home",
            sources=sources,
            confidence=1.0,
        )
    if face_on and confidence >= 0.5:
        sources.append("double_take")
        pct = int(confidence * 100) if confidence <= 1 else int(confidence)
        return FusedMember(
            name=name,
            person_entity=person_entity,
            state=FUSED_FACE,
            label=f"Seen at camera ({pct}%)",
            sources=sources,
            confidence=confidence if confidence <= 1 else confidence / 100.0,
        )
    if person_st == "not_home":
        sources.append("companion")
    return FusedMember(
        name=name,
        person_entity=person_entity,
        state=FUSED_AWAY,
        label="Away",
        sources=sources or ["none"],
        confidence=0.0,
    )


def fuse_all(states: dict[str, dict]) -> list[FusedMember]:
    return [fuse_member(m, states) for m in HOUSEHOLD]


def summary_dict(members: list[FusedMember]) -> dict[str, Any]:
    home = [m for m in members if m.counts_as_home]
    return {
        "count": len(home),
        "who_home": ", ".join(m.name for m in home) if home else "Nobody",
        "members": [
            {
                "name": m.name,
                "state": m.state,
                "label": m.label,
                "sources": m.sources,
                "confidence": m.confidence,
                "person_entity": m.person_entity,
            }
            for m in members
        ],
    }


def fetch_ha_states(
    *,
    base_url: str,
    token: str,
    timeout: int = 10,
) -> dict[str, dict]:
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{base_url}/api/states", headers=headers, timeout=timeout)
    r.raise_for_status()
    wanted = {m["person"] for m in HOUSEHOLD}
    for m in HOUSEHOLD:
        wanted.add(_dt_entities(m["dt_key"])[0])
        wanted.add(_dt_entities(m["dt_key"])[1])
    return {row["entity_id"]: row for row in r.json() if row["entity_id"] in wanted}


def face_match_at_entrance(members: list[FusedMember]) -> FusedMember | None:
    """Best Double Take match among household (for person events without identity)."""
    candidates = [
        m for m in members
        if m.state == FUSED_FACE and m.confidence >= 0.85
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda m: m.confidence)


def enrich_person_event(event: dict, members: list[FusedMember]) -> dict:
    """Attach identity from fusion when Frigate person has no name at entrance."""
    if event.get("type") != "person":
        return event
    if (event.get("identity") or {}).get("name"):
        return event
    zone = event.get("location", {}).get("zone", "")
    if zone not in ENTRANCE_ZONES:
        return event
    match = face_match_at_entrance(members)
    if not match:
        return event
    event = dict(event)
    event["identity"] = {
        "type": "person",
        "name": match.name,
        "source": "presence_fusion",
        "confidence": round(match.confidence, 3),
    }
    meta = dict(event.get("metadata") or {})
    meta["fusion_sources"] = match.sources
    event["metadata"] = meta
    return event


class PresenceFusionCache:
    """Thread-safe HA state cache with optional background refresh."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        refresh_seconds: int = 60,
    ) -> None:
        self.base_url = (base_url or os.environ.get("HA_URL") or "").rstrip("/")
        if not self.base_url:
            host = os.environ.get("HA_HOST", "192.168.68.175")
            self.base_url = f"http://{host}:8123"
        self.token = token or os.environ.get("HA_TOKEN", "")
        self.refresh_seconds = refresh_seconds
        self._lock = threading.Lock()
        self._members: list[FusedMember] = []
        self._thread: threading.Thread | None = None

    def enabled(self) -> bool:
        return bool(self.token)

    def refresh(self) -> list[FusedMember]:
        if not self.enabled():
            return []
        try:
            states = fetch_ha_states(base_url=self.base_url, token=self.token)
            members = fuse_all(states)
            with self._lock:
                self._members = members
            return members
        except requests.RequestException as exc:
            log.warning("Presence fusion refresh failed: %s", exc)
            with self._lock:
                return list(self._members)

    def members(self) -> list[FusedMember]:
        with self._lock:
            return list(self._members)

    def start_background(self) -> None:
        if not self.enabled() or self._thread:
            return

        def _loop() -> None:
            while True:
                self.refresh()
                time.sleep(self.refresh_seconds)

        self._thread = threading.Thread(target=_loop, name="presence_fusion", daemon=True)
        self._thread.start()
        log.info("Presence fusion polling HA every %ds", self.refresh_seconds)
