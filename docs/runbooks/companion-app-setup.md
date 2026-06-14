# Companion App Setup — Family Presence

Nils, Hugo, and Anna show **Unknown** on the Who's home row until their phones report to Home Assistant.

## Per person (iPhone)

1. Install **Home Assistant Companion** from App Store
2. Add server: `http://192.168.68.175:8123` (or Nabu Casa URL)
3. Log in as that person's HA user (or shared account with person entity linked)
4. Settings → Companion App → **Location** → allow Always + Precise
5. Settings → **Notifications** → enable as needed

## Link device to person entity

1. HA → **Settings → People** → select person (e.g. Nils)
2. **Trackers** → add `device_tracker.<phone>` from Companion
3. Verify **Developer Tools → States** → `person.nils_2` (or `person.hugo`, `person.anna`) updates when phone leaves/arrives

## Fusion with Double Take

Presence fusion templates (`sensor.house_occupancy_summary`, `sensor.*_presence_fused`) combine:

- Companion GPS / Wi‑Fi zone
- Double Take face match at entrance cameras
- Outdoor AOA context

No extra config once person entities update correctly.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Still Unknown | Companion location permission not "Always" |
| Jumpy home/away | Add home zone radius in HA **Settings → Areas** |
| Thomas works, others don't | Each person needs own HA user or linked device tracker |

## Related

- [projects/family-context.md](../projects/family-context.md)
- `config/home-assistant/templates/presence_fusion.yaml`
