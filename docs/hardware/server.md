# Production Server

## Dell Latitude 3120

| Attribute | Value |
|---|---|
| Model | Dell Latitude 3120 |
| Architecture | x86-64 |
| OS | Home Assistant OS (HAOS) |
| Install method | Generic x86-64 image |

### CPU (verify before Frigate install)

Run `cat /proc/cpuinfo | grep "model name"` via SSH on the HAOS host and update this table:

| Attribute | Value |
|---|---|
| CPU model | TBD — check SSH |
| Core count | TBD |
| Intel generation | TBD |
| OpenVINO support | TBD — check [OpenVINO CPU list](https://docs.openvino.ai/latest/openvino_docs_OV_UG_supported_plugins_CPU.html) |

**Why this matters:** OpenVINO support determines whether Frigate can run hardware-accelerated object detection at no cost. If supported, the Frigate detector changes from `type: cpu` to `type: openvino` — roughly 4× throughput improvement.

### Storage

| Drive | Role | Size | Mount |
|---|---|---|---|
| Internal SSD/eMMC | HAOS system + add-ons | TBD | `/` (managed by HAOS) |
| External 1 TB SSD | Frigate recordings | 1 TB | `/media/frigate` |

**External SSD:** Connect via USB 3.0. Verify visibility in **Settings → System → Storage** after HAOS boots. Format as ext4 via HAOS UI before mounting for Frigate.

### Network

| Interface | Role | Recommended |
|---|---|---|
| Ethernet (wired) | Primary — HA host NIC | Required |
| WiFi | Not recommended for HA host | Disable if possible |

### Verified IP and SSH Access

| Detail | Value |
|---|---|
| HAOS host IP | TBD — set static DHCP lease on router |
| SSH port | 22222 (SSH add-on default) |
| SSH user | `root` |

Update `.env` with the confirmed IP before running `sync-config.sh`.

---

## Development Machine

| Attribute | Value |
|---|---|
| OS | Windows (PC) |
| Editor | VS Code + Cursor |
| AI assistant | Claude Code |
| Local LLM | Ollama + Qwen |
| Role | Config authoring, AI experimentation |

The dev machine does **not** run any production services. It connects to the HAOS host via SSH for config sync. Ollama runs here for Phase 6 AI experiments before any decision is made to run LLMs on the HAOS host.
