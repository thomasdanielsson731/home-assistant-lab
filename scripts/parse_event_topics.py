#!/usr/bin/env python3
"""Walk GetEventInstances XML and print topic paths."""
import xml.etree.ElementTree as ET
from pathlib import Path

path = Path(__file__).parent.parent / "_event_instances.xml"
root = ET.fromstring(path.read_text(encoding="utf-8"))


def local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def walk(elem, prefix: list[str]) -> None:
    tag = local(elem.tag)
    is_topic = elem.get("{http://docs.oasis-open.org/wsn/t-1}topic") == "true"
    nice = elem.get("{http://www.axis.com/vapix/ws/event1}NiceName", "")
    parts = prefix + ([tag] if is_topic or tag in ("SoundPressureLevel", "Summary") else [])
    if tag == "Summary" or (is_topic and "Sound" in (nice or tag)):
        print(" / ".join(parts), nice)
    for child in elem:
        walk(child, parts if is_topic else prefix)


for child in root.iter():
    if local(child.tag) == "TopicSet":
        for c in child:
            walk(c, [])
