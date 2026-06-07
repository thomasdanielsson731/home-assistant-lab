# Project: Face Recognition

**Phase:** 4 · **Status:** In progress

## Goal

Identify household members (Thomas, Nils, Hugo, Anna) at `front` and `driveway_id`. Alert on unknown persons.

## Decision

CodeProject.AI on Windows dev PC — [ADR-003](../docs/decisions/003-face-recognizer.md).

## Done Criteria

- [ ] CodeProject.AI running on `192.168.68.136:32168`
- [ ] Double Take connected to CodeProject.AI
- [ ] All 4 household members recognized at `front` (>85% confidence)
- [ ] Unknown person triggers push notification with snapshot
- [ ] Face match status visible in Security dashboard

## Tasks

| # | Task | Status |
|---|---|---|
| 1 | Install CodeProject.AI on dev PC | ⬜ |
| 2 | Enable Face Recognition module | ⬜ |
| 3 | Restart Double Take, verify detector connection | ⬜ |
| 4 | Collect 10+ training photos per person | ⬜ |
| 5 | Upload via Double Take UI (`:3000`) | ⬜ |
| 6 | Test recognition accuracy at `front` | ⬜ |
| 7 | Create unknown person alert automation | ⬜ |
| 8 | Add face match cards to Security view | ⬜ |

## Key Files

- `config/double-take/config.yml` — already points to CodeProject.AI
- `config/home-assistant/automations/security/` — alert automations (to create)

## References

- [integrations/face-recognition/README.md](../integrations/face-recognition/README.md)
- [docs/runbooks/double-take-setup.md](../docs/runbooks/double-take-setup.md)
