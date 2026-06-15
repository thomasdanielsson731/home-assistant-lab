# Network Architecture

Home lab LAN at `192.168.68.0/24`. Static DHCP recommended for all infrastructure.

## Hosts

| Host | IP | Role |
|---|---|---|
| HAOS (Dell Latitude 3120) | `192.168.68.175` | Home Assistant, Frigate, MQTT, Insights add-on |
| Dev PC (Windows) | `192.168.68.136` | Git repo, sync scripts, Ollama (optional) |
| Router (TP-Link Deco M9+) | gateway | WAN, Wi‑Fi, optional device presence |

## Camera network (PoE)

| Zone ID | Model | IP |
|---|---|---|
| `front` | Axis P3288-LVE | `192.168.68.200` |
| `recorder` | Axis S3008 | `192.168.68.201` |
| `backyard` | Axis Q1656-LE | `192.168.68.202` |
| `driveway_wide` | Axis Q3558-LVE | `192.168.68.203` |
| `driveway_id` | Axis M2036-LE (+ D6210 air quality via VAPIX proxy) | `192.168.68.204` |
| `storage_ext` | Axis M1055-L | `192.168.68.205` |
| `storage_int` | Axis Q1656 | `192.168.68.206` |

## Service ports

| Service | Port | Notes |
|---|---|---|
| Home Assistant | `8123` | LAN; external via Cloudflare Tunnel → `https://ha.danielsson.cloud` |
| SSH add-on | `22222` | Config sync |
| Mosquitto | `1883` | Internal; do not forward WAN |
| Frigate UI / API | `5000` | Add-on |
| Frigate RTSP re-stream | `8554` | Add-on |
| Danielsson Insights | `8765` | Add-on + Ingress |
| Grafana | Ingress | HA sidebar |
| InfluxDB | `8086` | Add-on internal |

## VLAN design (future)

Recommended hardening from [architecture-review.md](../architecture-review.md):

1. **Camera VLAN** — Axis devices RTSP-only toward HA/Frigate; block internet egress
2. **IoT VLAN** — Zigbee coordinator stays on HA host USB; no Zigbee over IP
3. **Trusted LAN** — HA, admin workstations, NAS

Not yet implemented — document target state before router changes.

## DNS / external access

- **Domain:** `danielsson.cloud` (Loopia registrar)
- **External HA URL (target):** `https://ha.danielsson.cloud` via [Cloudflare Tunnel](../runbooks/remote-access-cloudflare.md)
- **DNS today:** Loopia nameservers (`ns1.loopia.se`) — use remote tunnel + CNAME, or move NS to Cloudflare
- Frigate MQTT host: `core-mosquitto` (add-on internal name)
- Axis MQTT topic prefix: `axis/<zone_id>/`
- Energy stub: `danielsson/energy/*`
