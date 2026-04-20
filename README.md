# Pumpr ⛽⚡

Real-time UK fuel price tracker and EV charging finder. Covers 7,600+ petrol stations across the UK with prices updated every 30 minutes from the official GOV.UK Fuel Finder scheme. EV charging data via Open Charge Map.

**Live at:** https://pumpr.co.uk (coming soon)
**Follow:** [@pumpr_app](https://x.com/pumpr_app) · [Bluesky](https://bsky.app/profile/pumpr-app.bsky.social)
**Support:** [Ko-fi](https://ko-fi.com/devoidx)

## Features

- Live fuel prices (E10, E5, B7, SDV, B10, HVO) at 7,600+ UK stations
- EV charging locations via Open Charge Map with connector type and speed filters
- Location-based search (GPS or postcode)
- Cheapest fuel sorted by price then distance
- Price history charts per station
- Price change indicators vs 24h ago
- Open now / closed indicator with full opening hours
- Amenities display (AdBlue, car wash, toilets etc)
- UK-wide stats and regional breakdown by country and county
- Daily social media posts to X and Bluesky
- Dark UI, mobile-friendly

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy (async) + APScheduler |
| Database | PostgreSQL 16 |
| Frontend | React 18 + Vite (no UI framework) |
| Map | Leaflet + CartoDB tiles |
| Fuel data | GOV.UK Fuel Finder API (OAuth 2.0) |
| EV data | Open Charge Map API |
| Geocoding | postcodes.io |
| Social | atproto (Bluesky) + tweepy (X) |
| Hosting | Self-hosted on zeolite (Ubuntu Server) |

## Setup

### 1. Get API credentials

**GOV.UK Fuel Finder** — register at https://www.developer.fuel-finder.service.gov.uk/access-latest-fuelprices

You'll need a GOV.UK One Login. You'll receive a client_id and client_secret.

**Open Charge Map** — register for a free API key at https://openchargemap.org/site/develop/apikey

**Bluesky** (optional) — create an app password at https://bsky.app/settings/app-passwords

**X / Twitter** (optional) — create a developer app at https://developer.twitter.com with Read and Write permissions.

### 2. Configure environment

Copy .env.example to .env and fill in:

    FUEL_FINDER_CLIENT_ID=your_client_id
    FUEL_FINDER_CLIENT_SECRET=your_client_secret
    OCM_API_KEY=your_ocm_key
    POSTGRES_PASSWORD=choose_a_strong_password
    SECRET_KEY=run: openssl rand -hex 32

    # Optional social media
    BSKY_HANDLE=yourhandle.bsky.social
    BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
    X_API_KEY=your_consumer_key
    X_API_SECRET=your_consumer_secret
    X_ACCESS_TOKEN=your_access_token
    X_ACCESS_TOKEN_SECRET=your_access_token_secret

### 3. Run

    docker compose up -d

API at http://localhost:8002 — Swagger docs at /docs
Frontend at http://localhost:3003

### 4. Initial data

On first startup the app syncs all 7,600+ stations, ingests current prices, and starts polling every 30 minutes.

### 5. Clean county data (first run only)

    docker exec pumpr_api python3 /app/scripts/fix_counties.py

Takes ~5 minutes. Geocodes all station postcodes via postcodes.io for clean county data.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/prices/cheapest | Cheapest stations by fuel type and location |
| GET | /api/v1/prices/stats | UK-wide averages by fuel type |
| GET | /api/v1/stations/{id} | Station detail with opening hours |
| GET | /api/v1/stations/{id}/history | Price history |
| GET | /api/v1/stations/{id}/price-changes | Price changes vs 24h ago |
| GET | /api/v1/ev/chargers | EV chargers near location |
| GET | /api/v1/ev/chargers/{id} | Charger detail |
| GET | /api/v1/stats/countries | Average prices by country |
| GET | /api/v1/stats/countries/cheapest | Cheapest station per country |
| GET | /api/v1/stats/counties | Average prices by county |
| GET | /api/v1/stats/counties/cheapest | Cheapest station per county |

## Data

- Fuel prices polled every 30 minutes from GOV.UK Fuel Finder API
- Retention: 7 days full granularity, 7-90 days daily, 90+ days purged
- Price validation: outliers below 50p or above 300p rejected
- County data: geocoded via postcodes.io, re-validated weekly
- Social posts: daily averages, cheapest station, cheapest by country at 8am UTC

## Development

    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    ruff check .
    mypy .

## Licence

MIT

## Disclaimer

Fuel price data is provided as-is from the GOV.UK Fuel Finder scheme under the Motor Fuel Price (Open Data) Regulations 2025. Prices may be up to 30 minutes old. Always verify at the pump. Pumpr is not affiliated with the UK Government, VE3 Global Ltd, or Open Charge Map.
