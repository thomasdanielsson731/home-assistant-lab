# Contributing

Guidelines for working in this repository. Applies to solo development and any future collaborators.

---

## Branch Strategy

| Branch | Purpose | Protected |
|---|---|---|
| `main` | Production configuration — what runs on the HAOS host | Yes |
| `dev` | Development and staging — test changes before merging to main | No |
| `feature/<name>` | New feature or integration | No |
| `fix/<name>` | Bug fix | No |
| `docs/<name>` | Documentation-only changes | No |

**Rules:**
- Never commit directly to `main`
- All changes to `main` go through a PR from `dev` or a feature branch
- PR must be self-reviewed: read your own diff before merging

---

## Commit Message Format

```
<type>: <short summary>

Types: feat, fix, docs, config, refactor, chore
```

Examples:
```
feat: add driveway_id camera to Frigate config
fix: correct RTSP URL for storage_ext camera
docs: add D6210 integration options to cameras.md
config: update Frigate retention to 14 days for events
chore: update .gitignore for Double Take storage paths
```

---

## Pull Request Process

1. Create a branch from `dev`
2. Make changes
3. Run Python tests: `python -m pytest` (requires `pip install -r requirements-dev.txt`)
4. Test by syncing to HAOS with `--dry-run` first: `./scripts/sync-config.sh --dry-run`
5. Open a PR against `dev` (or `main` for urgent fixes)
6. Fill in the PR template
7. Merge when self-reviewed and CI passes

### Python Tests

Event platform scripts (`event_store`, `event_normalizer`, `timeline_server`) have pytest coverage with an 85% minimum threshold enforced in CI.

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

CI workflow: `.github/workflows/test-python.yml` (runs on push/PR when `scripts/` or `tests/` change).

---

## What Gets Committed

**Yes:**
- All YAML config files (no secrets)
- All documentation
- All scripts
- `secrets.yaml.example` (template only)

**No:**
- `secrets.yaml` (gitignored)
- `.env` (gitignored)
- Frigate recordings or clips
- HA database files
- Any credentials or tokens

---

## Config Sync

After merging to `main`, sync to the HAOS host:

```bash
./scripts/sync-config.sh
```

Then restart affected add-ons in HA if config changed.

---

## Documentation Standards

- Use `docs/decisions/NNN-title.md` for architectural decisions (ADRs)
- Use `docs/runbooks/` for operational procedures
- Update `docs/roadmap.md` when a phase is complete
- Update `docs/backlog.md` when items are finished or reprioritized
- File names: kebab-case (e.g. `camera-onboarding.md`)
