# Secrets Backup Runbook

`secrets.yaml` lives only on the HAOS host at `/config/secrets.yaml` — never committed to git.

## Why

A host crash or SD/SSD failure without a secrets backup means lost camera passwords, MQTT credentials, and API tokens. Re-pairing six Axis cameras and all integrations is a full-day recovery.

## Backup procedure

1. SSH to HA: `ssh root@192.168.68.175 -p 22222`
2. Copy secrets to a password manager (Bitwarden recommended):
   ```bash
   cat /config/secrets.yaml
   ```
3. Store as secure note **Danielsson Home — HA secrets.yaml** with date in title.
4. Also export `.env` from dev PC (HA_TOKEN, camera passwords) to the same vault entry or sibling note.

## Restore procedure

1. Fresh HA install or new host — restore Supervisor backup if available.
2. Copy repo config via `.\scripts\sync-config.ps1`
3. Recreate `/config/secrets.yaml` from Bitwarden (use `secrets.yaml.example` as shape checklist).
4. Restart HA core: `ha core restart`
5. Verify: `python scripts/health-check.py`

## Rotation

When changing a camera or MQTT password:

1. Update on device / Mosquitto
2. Update `secrets.yaml` on host
3. Update matching key in dev `.env` if scripts use it
4. Update Bitwarden entry same day

## Related

- [initial-setup.md](initial-setup.md)
- [architecture-review.md](../architecture-review.md) — risk #3
