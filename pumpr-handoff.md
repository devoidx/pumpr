# Pumpr — Project Handoff Document

UK fuel price tracker. Live at [pumpr.co.uk](https://pumpr.co.uk). Solo-developed by Tony McMahon (GitHub: devoidx).

Last updated: 1 July 2026 (reflects state as of v1.9.0)

---

## 1. Overview

Pumpr helps UK drivers find the cheapest petrol and diesel near them, using live data from the GOV.UK Fuel Finder scheme (8,000+ stations). It also includes EV charging point data (Open Charge Map), price alerts, personal fuel spending tracking, market intelligence, and a blog of fuel-market news.

As of v1.9.0, Pumpr also shows **European fuel prices for UK travellers** — France first, with Germany/Spain/Italy planned. French station prices (9,600+ stations) update daily from official government data, shown in EUR and GBP. A Pro-gated interactive map is available at `/europe/map/fr`.

There's also an Android app on Google Play (first production release v1.9.0 submitted 1 July 2026), built as a Capacitor WebView wrapper around the same live website — no separate native codebase.

**Stack:** FastAPI backend, React 18/Vite/Chakra UI frontend, PostgreSQL 16, Docker Compose, deployed across two servers.

---

## 2. Servers & Infrastructure

| Server | Role | Address | Notes |
|---|---|---|---|
| zeolite | Dev / homelab | `192.168.0.246` (Tailscale: `100.106.38.49`) | Ubuntu Server, Docker, no `sudo` needed for docker commands |
| VPS (Hetzner) | Production | `178.104.239.190` | Shared Hetzner VPS, also hosts other devoidx projects |

- Repo: `github.com/devoidx/pumpr`, path `/opt/pumpr/` on both servers.
- Cloudflare sits in front of the VPS. DNS, caching, and SSL termination happen there — **remember to purge Cloudflare cache after frontend deploys** if changes don't appear live (Dashboard → Caching → Configuration → Purge Everything).
- Tailscale is installed on **both** zeolite and the VPS for cross-server access (e.g. DB sync). On the VPS, Tailscale's DNS override previously broke outbound DNS resolution for Docker containers — fixed by running `tailscale set --accept-dns=false` on the VPS. If outbound API calls (e.g. price polling) start failing with `Temporary failure in name resolution`, check `tailscale dns status` first.
- zeolite dev mode has `ENABLE_PRICE_POLLING=false` — it does not poll live prices itself; it syncs from the VPS instead.

### DB sync (VPS → zeolite)
```bash
bash /opt/pumpr/scripts/sync-db-from-vps.sh
```
**Run this at the start of every session involving EU feature work.** The sync script does a full `pg_dump` so it includes `eu_stations`, `eu_latest_prices`, and `exchange_rates` automatically. Skipping this leaves zeolite with no EU data and means all EU testing runs against the production VPS DB instead.

### Useful one-liners
```bash
# Restart API after a power cut (asyncpg silently loses its PG connection)
docker compose restart api

# Check VPS logs
ssh root@178.104.239.190 "docker logs pumpr_api --tail 50"

# Run tests
docker exec pumpr_api pytest --tb=short -q

# Lint
docker exec pumpr_api ruff check app/
docker exec pumpr_api mypy app/ --ignore-missing-imports

# Manual EU ingest (France)
docker exec pumpr_api python3 -c "import asyncio; from app.services.eu.ingest import ingest_france; asyncio.run(ingest_france())"

# Manual ECB rate fetch
docker exec pumpr_api python3 -c "import asyncio; from app.services.eu.ecb_client import upsert_ecb_rate; asyncio.run(upsert_ecb_rate())"

# Check EU data is current
docker exec pumpr_db psql -U pumpr -d pumpr -c "SELECT country, count(*) FROM eu_stations GROUP BY country;"
docker exec pumpr_db psql -U pumpr -d pumpr -c "SELECT fuel_type, count(*), round(avg(price_eur),3) FROM eu_latest_prices GROUP BY fuel_type;"
docker exec pumpr_db psql -U pumpr -d pumpr -c "SELECT * FROM exchange_rates ORDER BY rate_date DESC LIMIT 1;"
```

**Never run `docker compose down` on the VPS** — Postgres loses its password on restart and needs manual recovery. Use `docker compose restart <service>` instead.

**Always run mypy manually before committing new Python files** — the pre-commit hook runs mypy but hangs silently on type errors rather than failing loudly. A hanging hook looks identical to a passing one until you notice no commit hash appears. Run `docker exec pumpr_api mypy app/ --ignore-missing-imports` before every commit when new `.py` files are involved.

---

## 3. Deploy Workflow (web)

1. Bump the version in `frontend/src/version.js` (format: `export const VERSION = 'X.Y.Z'`)
2. On zeolite: `git add -A && git commit -m "..." && git push`
3. Deploy to VPS:
   ```bash
   ssh root@178.104.239.190 "cd /opt/pumpr && git pull && bash build.sh"
   ```
4. `build.sh` reads the version, rebuilds the `frontend` container with `BUILD_HASH` set to the current git short SHA, and restarts it.
5. **Frontend-only changes deploy without any Android rebuild** — the Capacitor app loads `https://pumpr.co.uk` live via `server.url` in its config, so web deploys reach Android users immediately.
6. A pre-commit hook runs **Ruff + mypy + pytest** on every commit. Common Ruff failure: unsorted/ungrouped imports (stdlib → third-party → blank line → local `app.*` imports) and long import lines (split with parens across multiple lines).

**Important:** `build.sh` only rebuilds the `frontend` container. API/backend changes require a separate API rebuild:
```bash
ssh root@178.104.239.190 "cd /opt/pumpr && docker compose build --no-cache api && docker compose up -d api"
```
The `--no-cache` flag is critical — Docker's layer cache will serve stale `COPY . .` layers otherwise, even after a `git pull`.

**SQL migrations** must be applied to the VPS DB *before* deploying code that depends on them. The numbered SQL files in `/opt/pumpr/postgres/` are applied manually. Since the file won't exist on the VPS until after `git pull`, pipe from local:
```bash
ssh root@178.104.239.190 "docker exec -i pumpr_db psql -U pumpr -d pumpr" < /opt/pumpr/postgres/015-eu-tables.sql
```

To rebuild only the frontend container (e.g. after a CSS/JS-only change tested locally):
```bash
docker compose up --build -d frontend
```

---

## 4. Versioning

- **Web app version**: `frontend/src/version.js` — bump on every deploy-worthy change. Shown in the About page footer along with `BUILD_HASH` (git short SHA, injected at build time via `--build-arg BUILD_HASH`).
- **Android version**: tracked separately in `frontend/android/app/build.gradle` (`versionCode` integer, `versionName` string) and mirrored in `ANDROID_VERSION.txt` at the repo root for quick reference. `versionCode` must strictly increase on every Play Store upload; `versionName` is cosmetic and usually matches the current web version.

---

## 5. Android Build & Release Process

### Architecture
The Android app is a **Capacitor WebView wrapper**, not a separate native app. `capacitor.config.json` sets `server.url: https://pumpr.co.uk`, so the app always loads the live website. This means:
- Web/UI/backend changes need **no new APK/AAB** — they're live the moment you deploy to the VPS.
- A new AAB build is only needed for: native config changes (permissions, icons, Capacitor plugin updates), or when a meaningful feature warrants a Play Store release with updated description/notes.

### Critical rule: zeolite is the only place that bumps Android version and pushes to git
Windows is **build-only** — it must never commit or push.

### Step 1 — Bump version (on zeolite)
```bash
cd /opt/pumpr
bash scripts/bump-android-version.sh
```

### Step 2 — Build (on Windows, `C:\Users\admcm\pumpr`)
```powershell
git pull
.\build-android.ps1
```

### Step 3 — Sign the bundle (Android Studio, manual)
1. **Build → Generate Signed Bundle / APK → Android App Bundle**
2. Keystore: `C:\Users\admcm\pumpr-keystore.jks` (**do not lose this — no recovery possible**)
3. Output: `frontend\android\app\release\app-release.aab`

### Step 4 — Upload to Play Console
**Release → Production → Create New Release** → Upload AAB → release notes → Submit.

### Google Play Console reference
- Developer account: DevoidX (Account ID: `4708071328485362899`)
- App: Pumpr, package `co.uk.pumpr`
- Privacy policy: `https://pumpr.co.uk/privacy`
- First production release: v1.9.0, versionCode 7, submitted 1 July 2026.
- Countries/regions must be explicitly set on the Production track (United Kingdom) — separate step from the release itself, will block submission if skipped.

---

## 6. Code Structure

```
/opt/pumpr/
├── backend/
│   └── app/
│       ├── api/
│       │   ├── endpoints/
│       │   │   ├── eu_locations.py   # NEW — /api/v1/eu/cheap-fuel/{country}/{city}
│       │   │   │                     #        /api/v1/eu/nearby (lat/lng radius search)
│       │   │   └── ... (auth, stations, prices, alerts, stats, intelligence,
│       │   │           blog, feedback, fillups, vehicles, locations, locations_seo,
│       │   │           ev, sitemap, stripe_routes)
│       │   └── router.py
│       ├── models/
│       │   ├── eu.py             # NEW — EUStation, EULatestPrice, ExchangeRate
│       │   └── ...
│       ├── services/
│       │   ├── eu/               # NEW — EU ingestion pipeline
│       │   │   ├── __init__.py
│       │   │   ├── ecb_client.py      # ECB EUR→GBP daily rate fetch + upsert
│       │   │   ├── france_client.py   # France feed (ZIP/ISO-8859-1 XML) parser
│       │   │   ├── fuel_type_map.py   # per-country fuel label → enum mapping
│       │   │   └── ingest.py          # upsert into eu_stations/eu_latest_prices
│       │   ├── seo_snapshots.py  # now includes generate_eu_city_snapshots()
│       │   │                     # and generate_europe_landing_snapshot()
│       │   ├── scheduler.py      # now includes ingest_eu_job (05:00),
│       │   │                     # fetch_ecb_rate_job (04:00),
│       │   │                     # post_france_promo_job (Mon+Thu, Jun/Jul/Aug)
│       │   └── ...
│       └── ...
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── EuropePage.jsx         # NEW — /europe landing page
│       │   ├── EuropeMapPage.jsx      # NEW — /europe/map/:country (Pro-gated)
│       │   └── EUCheapFuelPage.jsx    # NEW — /cheap-fuel/europe/:country/:city
│       ├── components/
│       │   └── EUMap.jsx              # NEW — EU Leaflet map (separate from Map.jsx)
│       └── api/client.js             # now includes getEUNearby(), getEUCheapFuel()
└── postgres/
    └── 015-eu-tables.sql             # NEW — creates eu_stations, eu_latest_prices,
                                      #        exchange_rates + indexes
```

### Database — EU tables
- `eu_stations` — id, external_id, country (ISO 2-char), name, address, postcode, city, latitude, longitude. UNIQUE on (country, external_id). Deliberately isolated from UK `stations` table — EU ingestion failures cannot affect the GB pipeline.
- `eu_latest_prices` — eu_station_id, fuel_type, price_eur (NUMERIC 6,3), recorded_at. One row per station+fuel. UNIQUE on (eu_station_id, fuel_type).
- `exchange_rates` — rate_date (PK), eur_to_gbp (NUMERIC 8,6), fetched_at. ECB daily reference rate. Prices stored natively in EUR; GBP conversion happens at query/display time — never store converted prices.

---

## 7. Scheduler Jobs (APScheduler, in `scheduler.py`)

All times Europe/London. Full list as of July 2026:

| Schedule | Job | Notes |
|---|---|---|
| Every 30 min | `poll_prices` | Incremental fetch from Fuel Finder API |
| ~60s after poll | `warm_city_cache_job` | Warms UK city cache + regenerates UK SEO snapshots |
| Daily 02:00 | sitemap generation | |
| Daily 03:00 | retention policy | Trims `price_history` to 7 days full / 90 days daily |
| Daily 04:00 | `fetch_ecb_rate_job` | ECB EUR→GBP rate → `exchange_rates` |
| Daily 04:30 | market intelligence + station sync | |
| Daily 05:00 | `ingest_eu_job` | France feed → eu_tables; then EU city snapshots + /europe snapshot |
| 08:00–08:25 + 16:00–16:25 | 5 social posts | daily averages, cheapest E10/diesel/by-country |
| 08:30 + 16:30 daily | `post_play_store_launch_job` | **Still running indefinitely — remove when no longer wanted** |
| Mon + Thu, Jun/Jul/Aug annually | `post_france_promo_job` | France feature promo — recurs automatically each summer |
| Weekly Tue 09:30 | weekly blog post | |
| Weekly Wed 10:00 | check blog sources (RSS) | |
| Monthly 1st 08:00 | spending digest emails | |
| Every 30 min | check price alerts | |

**Known gotcha:** APScheduler logs `executed successfully` even when job side effects failed silently. Never trust that log line alone — check actual data. See `latest_prices` incident in §9.

---

## 8. SEO Architecture

### EU pages (added v1.9.0)

Snapshot generation runs daily inside `ingest_eu_job` after ingestion completes. Snapshot locations:
- `/opt/pumpr/snapshots/europe.html` — `/europe` landing page
- `/opt/pumpr/snapshots/europe/fr/{city}.html` — 16 France city pages

nginx location blocks in `/etc/nginx/sites-enabled/pumpr.co.uk`:
```nginx
location = /europe { ... rewrite to /snapshots/europe.html if $is_crawler ... }
location ~ ^/cheap-fuel/europe/([a-z]+)/([a-z-]+)$ { ... rewrite to /snapshots/europe/$country/$city.html if $is_crawler ... }
```

**Critical:** the EU multi-segment block must appear **before** the UK single-segment block (`^/cheap-fuel/([a-z-]+)$`) in the nginx config — the UK block would otherwise match `europe` as a city slug.

France city list (16 cities, curated for UK traveller routes): calais, boulogne-sur-mer, dunkirk, lille, rouen, paris, reims, le-havre, caen, rennes, saint-malo, bordeaux, toulouse, lyon, nice, marseille.

URLs submitted to Search Console 1 July 2026 — expect organic traffic to build over 4–8 weeks.

### France data source quirks
- Feed: `https://donnees.roulez-eco.fr/opendata/instantane` — ZIP-compressed (not gzip), ISO-8859-1 XML
- Coordinates: scaled ×1e5 integers — divide by 100,000 to get decimal degrees
- Bounding box validation: lat 41–51.5°N, lon -6–10°E (catches sign/scale errors before DB write)
- Per-fuel `maj` timestamp in each `<prix>` element — stations can have different update times per fuel type

### UK pages (unchanged from original)
Two bugs fixed that made the site invisible to Google: hardcoded canonical in `index.html` (removed) and `google-inspectiontool` not in the `$is_crawler` nginx map (added). Both resolved. Full debugging checklist:
1. `curl -s -A "Googlebot UA" https://pumpr.co.uk/PATH | grep "canonical\|title"` — check snapshot is served
2. Also test with Google-InspectionTool UA (different code path, burned us once)
3. Check snapshot exists on disk at `/opt/pumpr/snapshots/...`
4. Check nginx `location` block exists and matches
5. Check page component calls `useSEO` with correct `path` derived from URL param (not async-fetched state)

### `useSEO` hook contract
```js
useSEO({ title, description, path, noindex })
```
- `path` is route-relative; prefixed with `https://pumpr.co.uk` internally
- `noindex: true` for all account/private/admin/tool pages (including `/europe/map/:country`)
- Every public-facing page **must** call this hook

---

## 9. Common Debug Issues & Known Gotchas

### EU data not updating
Check directly — don't rely on scheduler logs:
```sql
SELECT MAX(recorded_at) FROM eu_latest_prices;
SELECT * FROM exchange_rates ORDER BY rate_date DESC LIMIT 1;
```
ECB rate always shows previous working day's date (ECB publishes ~16:00 CET; job runs 04:00 BST) — this is expected. If `eu_latest_prices` is stale by more than 24 hours, run the manual ingest one-liner from §2.

### API container not picking up new code after `git pull`
`build.sh` only rebuilds frontend. Always use `--no-cache` for API rebuilds:
```bash
ssh root@178.104.239.190 "cd /opt/pumpr && docker compose build --no-cache api && docker compose up -d api"
```

### mypy hangs silently in pre-commit hook
Returns to prompt without commit hash or error. Always run mypy manually before committing new `.py` files.

### "No data on the map" / feed shows "could not reach server"
- **Power cut recovery (zeolite)**: `docker compose restart api`
- **DNS resolution failure on VPS**: `tailscale set --accept-dns=false`
- **VPS-wide outage**: check status.hetzner.com

### `latest_prices` silently going stale (real incident, 3 weeks undetected)
APScheduler logged `executed successfully` throughout while the upsert failed every cycle. Root cause: `asyncpg` doesn't support inline `:param::type[]` cast syntax; fixed by switching to `CAST(:param AS type[])`. Check `MAX(recorded_at)` in `latest_prices` vs `price_history` if stats pages look wrong.

### Birmingham (and similar) stations geocoded into the sea
`_fix_coords()` validates by bounding box, not postcode-region cross-check. A sign flip that still lands "somewhere in the UK" won't be caught unless explicitly handled per postcode prefix. Check `longitude` sign first.

### Ruff import-sorting
Enforces: stdlib → (blank) → third-party → (blank) → local `app.*`. Fails on new files too.

### Cloudflare cache masking deploys
Purge before assuming a deploy failed: Dashboard → Caching → Configuration → Purge Everything.

### Vite `manualChunks` / chunk-splitting
`vite.config.js` is intentionally plain. Chunk-splitting was measured to make mobile PageSpeed worse. Don't reintroduce it.

### asyncpg / SQLAlchemy version drift after rebuild
Fresh builds can pull newer versions with different behaviour. If something breaks only after a rebuild, suspect transitive dependency version change first.

---

## 10. Pro / Billing
- Stripe-based subscriptions, price IDs in `ProPage.jsx` and `stripe_routes.py`.
- **EU map (`/europe/map/fr`) is Pro-gated** — non-Pro users see a teaser with upgrade prompt on `/europe`.
- EU map uses Nominatim (OpenStreetMap) for location search — no API key required.
- Pro test/seed accounts on VPS:
  - `hello@pumpr.co.uk` (testpro) — **also admin role**
  - `andrewj720@fastmail.com` (pumpr1) — pro, opted into `blog_newsletter`
  - `mcmahonmegan66@gmail.com` (Megan) — pro, opted into `blog_newsletter`

---

## 11. Distribution / Marketing State (as of 1 July 2026)
- Google Play **first production release v1.9.0 submitted 1 July 2026** (pending Google review).
- `PlayStoreBanner` shows on web (not in Android WebView), dismissible via `localStorage`.
- Play Store launch promo posts (`post_play_store_launch`) **still running indefinitely at 08:30/16:30 daily — remove when no longer wanted**.
- France promo post runs Mon + Thu in June/July/August annually — recurs automatically, no maintenance needed.
- Threads posting **blocked** — `_threads_post()` fails silently. Bluesky and Mastodon unaffected.
- EU pages submitted to Search Console 1 July 2026. No strong incumbents in EU fuel prices for UK travellers — this is the realistic SEO opportunity.

---

## 12. EU Feature — Next Steps

**Germany**: register free Tankerkönig API key at `https://creativecommons.tankerkoenig.de/`. Once registered, add key to `.env`, write `services/eu/germany_client.py`, add `DE` to `FUEL_TYPE_MAP`, add German cities to `EU_SNAPSHOT_CITIES` in `seo_snapshots.py`, wire into `ingest_eu_job`.

**Spain**: `curl https://geoportalgasolineras.es/resources/files/preciosEESS_es.xml` to inspect live format, then write parser. Updates a few times daily.

**Italy**: `curl https://www.mise.gov.it/images/exportCSV/prezzi_alle_8.csv` to inspect format, then write parser.

**New country onboarding pattern**: curl live feed → inspect format → write parser → test standalone (`asyncio.run(fetch_and_parse_X())`) → integrate ingest → add to `FUEL_TYPE_MAP` + `EU_SNAPSHOT_CITIES` → deploy.

**OCM EV chargers on EU map**: `getChargers()` already hits Open Charge Map globally — just add EV mode toggle to `EuropeMapPage` and pass chargers to `EUMap`. No backend work needed.

**Key architectural decisions (don't revisit without good reason)**:
- Separate `eu_` tables, not a `country` column on shared tables — isolates EU failures from GB pipeline
- EUR stored natively, GBP at query time — never store converted prices
- Daily ingestion for all EU countries — 30-min live cadence not needed
- ECB daily reference rate for FX — not a live tick feed
- 16 curated France cities for SEO — weighted toward Channel-crossing routes, not domestic French volume
- `EUMap.jsx` separate from `Map.jsx` — UK map is untouched by EU work

---

## 13. Open / Parked Ideas
- Google/social OAuth sign-in — deferred, tester feedback requested it, not yet implemented
- `GET /api/v1/blog?limit=N` returns `total: 1` regardless of actual row count — not investigated
- Lazy-loading Recharts on Intelligence page — works, doesn't move PageSpeed scores meaningfully

---

## 14. Sibling Projects (separate repos, mentioned for context only)
- **Spade** (`devoidx/spade`, private) — UK planning application lead-gen SaaS, FastAPI/React/PostgreSQL, ports 8004/3005/5435
- **TerraWatch** — seismic/volcanic monitoring dashboard
- **Barograph** (`devoidx/barograph`) — weather dashboard, FastAPI (8003) + Vite/React (3004) + PostgreSQL (5434)
- **OceanLens** — newly scoped, not yet built
