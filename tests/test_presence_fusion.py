"""Tests for scripts/presence_fusion.py."""

from __future__ import annotations

import pytest

from presence_fusion import (
    FUSED_AWAY,
    FUSED_FACE,
    FUSED_HOME,
    enrich_person_event,
    face_match_at_entrance,
    fuse_all,
    fuse_member,
    summary_dict,
)


def _states(mapping: dict[str, str]) -> dict:
    return {eid: {"entity_id": eid, "state": st} for eid, st in mapping.items()}


class TestFuseMember:
    def test_companion_home(self):
        states = _states({"person.thomasx": "home"})
        m = fuse_member({"name": "Thomas", "person": "person.thomasx", "dt_key": "thomas"}, states)
        assert m.state == FUSED_HOME
        assert m.counts_as_home

    def test_face_when_away(self):
        states = _states({
            "person.thomasx": "not_home",
            "binary_sensor.dt_thomas_present": "on",
            "sensor.dt_thomas_confidence": "92",
        })
        m = fuse_member({"name": "Thomas", "person": "person.thomasx", "dt_key": "thomas"}, states)
        assert m.state == FUSED_FACE
        assert m.confidence == pytest.approx(0.92)

    def test_away_without_signals(self):
        states = _states({"person.nils_2": "not_home"})
        m = fuse_member({"name": "Nils", "person": "person.nils_2", "dt_key": "nils"}, states)
        assert m.state == FUSED_AWAY


class TestEnrichPersonEvent:
    def test_attaches_face_identity_at_front(self):
        members = fuse_all(_states({
            "person.thomasx": "not_home",
            "binary_sensor.dt_thomas_present": "on",
            "sensor.dt_thomas_confidence": "0.91",
        }))
        event = {
            "type": "person",
            "location": {"zone": "front", "camera": "front"},
            "identity": {},
            "metadata": {},
        }
        out = enrich_person_event(event, members)
        assert out["identity"]["name"] == "Thomas"
        assert out["identity"]["source"] == "presence_fusion"

    def test_skips_non_entrance_zone(self):
        members = fuse_all(_states({
            "binary_sensor.dt_thomas_present": "on",
            "sensor.dt_thomas_confidence": "95",
        }))
        event = {"type": "person", "location": {"zone": "backyard"}, "identity": {}, "metadata": {}}
        assert enrich_person_event(event, members)["identity"] == {}


class TestSummary:
    def test_counts_home_and_face(self):
        members = fuse_all(_states({
            "person.thomasx": "home",
            "person.nils_2": "not_home",
            "binary_sensor.dt_nils_present": "on",
            "sensor.dt_nils_confidence": "88",
            "person.hugo": "not_home",
            "person.anna": "not_home",
        }))
        s = summary_dict(members)
        assert s["count"] == 2
        assert "Thomas" in s["who_home"]
        assert "Nils" in s["who_home"]


class TestFaceMatch:
    def test_picks_highest_confidence(self):
        members = fuse_all(_states({
            "binary_sensor.dt_thomas_present": "on",
            "sensor.dt_thomas_confidence": "80",
            "binary_sensor.dt_nils_present": "on",
            "sensor.dt_nils_confidence": "95",
            "person.thomasx": "not_home",
            "person.nils_2": "not_home",
        }))
        match = face_match_at_entrance(members)
        assert match is not None
        assert match.name == "Nils"
