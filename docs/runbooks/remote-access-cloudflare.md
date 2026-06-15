# Remote Access — danielsson.cloud via Cloudflare Tunnel

Secure external access to Home Assistant **without port forwarding**.
Target URL: **`https://ha.danielsson.cloud`**.

This runbook follows the standard HA + Cloudflare setup (Loopia registrar, Cloudflare DNS, Cloudflared add-on).

---

## Progress checklist (danielsson.cloud)

| Step | Status | Notes |
|---|---|---|
| 1. Cloudflare-konto + domän | ✅ | `danielsson.cloud` aktiv hos Cloudflare |
| 2. Namnservrar Loopia → Cloudflare | ✅ | `carlos.ns.cloudflare.com`, `love.ns.cloudflare.com` |
| 3. Cloudflared add-on installerat | ❌ | **Nästa steg** |
| 4. Add-on konfigurerat + OAuth | ❌ | `external_hostname: ha.danielsson.cloud` |
| 5. `trusted_proxies` i HA | ✅ | Synkat till HAOS (`172.30.33.0/24`) |
| 6. Extern URL i HA + test mobildata | ❌ | Efter add-on kör |

Verify DNS anytime:

```powershell
nslookup -type=NS danielsson.cloud 1.1.1.1
nslookup ha.danielsson.cloud 1.1.1.1
# Cloudflare NS + Cloudflare anycast IPs (104.21.x / 172.67.x) = OK
```

---

## Steg 1–2 — Cloudflare + Loopia (klart)

1. Domän registrerad hos **Loopia** (behålls där — du byter bara namnservrar).
2. **cloudflare.com** → Add site → `danielsson.cloud` → **Free** plan.
3. Kontrollera importerade DNS-poster (MX för e-post etc.).
4. Loopia → byt namnservrar till Cloudflares två (t.ex. `carlos.ns.cloudflare.com` + `love.ns.cloudflare.com`).
5. Vänta tills Cloudflare mejlar “Active” (ofta 1–24 h).

**WebSockets** (krävs för HA live-uppdateringar):

Cloudflare → danielsson.cloud → **Network** → **WebSockets** → **On**

---

## Steg 3 — Installera Cloudflared add-on

**Inställningar → Tillägg → Tilläggsbutik** → ⋮ → **Repositories**

Lägg till **repository-index** (inte app-cloudflared-projektet):

```
https://github.com/homeassistant-apps/repository
```

One-click (om du är inloggad i HA-appen):  
[my.home-assistant.io — lägg till repo](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fhomeassistant-apps%2Frepository)

Uppdatera tilläggsbutiken → installera **Cloudflared**. **Starta inte än.**

> **Fel URL** (ger "not a valid app repository"):  
> `https://github.com/homeassistant-apps/app-cloudflared`  
> Legacy (fungerar också): `https://github.com/brenner-tobias/ha-addons`

---

## Steg 4 — Konfigurera add-on (local tunnel)

**Configuration**-fliken:

```yaml
external_hostname: ha.danielsson.cloud
tunnel_name: haos-danielsson
log_level: info
```

Spara → **Info** → **Start**.

**Log**-fliken:

1. En URL visas för **engångs-OAuth** mot Cloudflare.
2. Öppna länken, logga in, välj `danielsson.cloud`, godkänn.
3. Add-on skapar tunnel + CNAME `ha` automatiskt hos Cloudflare.
4. Loggen ska visa att tunneln är ansluten.

**Alternativ (remote tunnel):** skapa tunnel manuellt i [Zero Trust](https://one.dash.cloudflare.com/) och sätt bara `tunnel_token:` i add-on — använd det om local tunnel krånglar.

Service-URL i Zero Trust (remote): `http://homeassistant:8123` — **inte** LAN-IP.

---

## Steg 5 — Tillåt proxyn i Home Assistant (klart i repot)

`/config/configuration.yaml`:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.30.33.0/24
```

`172.30.33.0/24` = HAOS add-on-nätverk som Cloudflared kommer från.

Redan synkat. Efter add-on-start: **Inställningar → System → Starta om** om du får 400 Bad Request.

Om 400 kvarstår: **Inställningar → System → Loggar** — lägg till blockerad IP under `trusted_proxies`.

---

## Steg 6 — Extern URL + test

Because `homeassistant:` is in `configuration.yaml`, URLs **cannot** be changed in the UI — set in YAML:

```yaml
homeassistant:
  internal_url: http://192.168.68.175:8123
  external_url: https://ha.danielsson.cloud
```

Sync + **HA core restart** required.

| Fält | Värde |
|---|---|
| Lokal | `http://192.168.68.175:8123` |
| Extern | `https://ha.danielsson.cloud` |

Testa från **mobildata** (inte hemma-WiFi): `https://ha.danielsson.cloud` → HA inloggning + hänglås.

**Companion app (Thomas iPhone):**

Inställningar → Server → Extern URL: `https://ha.danielsson.cloud`

---

## Säkerhet

| Gör | Undvik |
|---|---|
| HA-lösenord + **2FA** | Exponera MQTT `:1883`, Frigate `:5000`, SSH `:22222` |
| Cloudflare SSL: **Full** | Exponera Insights `:8765` utan auth |
| **Cloudflare Access** (valfritt, gratis ≤50 användare) — OTP innan HA-login | Stora kameraströmmar via tunnel (långsamt på free plan) |

### Cloudflare Access (rekommenderat om publikt)

Zero Trust → **Access → Applications → Add** → Self-hosted → `ha.danielsson.cloud` → Policy: din e-post + engångskod.

---

## Insights / Analytics utifrån

Lovelace-iframes pekar på LAN `:8765` i `secrets.yaml` — fungerar **inte** remote förrän du exponerar t.ex. `insights.danielsson.cloud` **med Access** och uppdaterar secrets. HA-gränssnitt + notiser fungerar utan det.

---

## Felsökning

| Symptom | Åtgärd |
|---|---|
| 502 / SSL-fel | Cloudflared add-on inte startat eller OAuth ej klar |
| 400 Bad Request | `trusted_proxies` + HA-omstart |
| Ingen live-uppdatering | WebSockets på i Cloudflare |
| Fungerar hemma, inte ute | Testa mobildata; vänta på DNS |
| Login-loop | Sätt extern URL under Nätverk |

---

## Referenser

- [Cloudflared HA add-on](https://github.com/homeassistant-apps/app-cloudflared/blob/main/cloudflared/DOCS.md)
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- Nätverk: [docs/architecture/network.md](../architecture/network.md)
