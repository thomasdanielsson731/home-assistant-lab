# Initial Setup Runbook

## 1. Install Home Assistant OS

1. Download HAOS generic x86-64 image from [home-assistant.io](https://www.home-assistant.io/installation/generic-x86-64)
2. Flash to target drive with Balena Etcher or `dd`
3. Boot Dell Latitude 3120 from the drive
4. Navigate to `http://homeassistant.local:8123` (or host IP) to complete onboarding

## 2. Enable SSH Access

1. In HA: **Settings → Add-ons → Add-on Store → SSH & Web Terminal**
2. Install and start the add-on
3. Set a password or authorized key in add-on config
4. Confirm SSH works: `ssh root@<ha-ip> -p 22222`

## 3. Install HACS (Community Store)

```bash
# SSH into HA host
wget -O - https://get.hacs.xyz | bash -
```

Restart HA, then enable HACS integration.

## 4. Clone This Repo

On your workstation:

```bash
git clone <repo-url> home-assistant-lab
cd home-assistant-lab
cp .env.example .env   # fill in HA_HOST, HA_USER
```

## 5. Sync Config

```bash
./scripts/sync-config.sh
```

## 6. Install Add-ons

From HA → Add-ons → Add-on Store:
- Frigate (via HACS or community repo)
- Danielsson Insights (via repo URL — see [timeline-addon.md](timeline-addon.md))
- MQTT Broker (Mosquitto)

## 7. Configure MQTT

In HA: **Settings → Devices & Services → Add Integration → MQTT**
Point to `localhost:1883` (Mosquitto add-on default).
