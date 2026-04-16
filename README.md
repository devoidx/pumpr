# Pumpr 🔴

UK fuel price tracker using the GOV.UK Fuel Finder API. Tracks prices at service stations over time and displays trends, maps, and cheapest fuel near you.

## Stack

- **Backend**: FastAPI + SQLAlchemy (async) + APScheduler
- **Database**: PostgreSQL 16
- **Frontend**: React 18 + Vite + Chakra UI _(coming soon)_
- **Data**: GOV.UK Fuel Finder API (OAuth 2.0)

## Setup

### 1. Get API credentials

Register at: https://www.developer.fuel-finder.service.gov.uk/access-latest-fuelprices

You'll need a GOV.UK One Login. You'll receive a `client_id` and `client_secret`.

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your credentials
```

Key variables:
```
FUEL_FINDER_CLIENT_ID=your_client_id
FUEL_FINDER_CLIENT_SECRET=your_client_secret
POSTGRES_PASSWORD=choose_a_password
SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Run

```bash
docker compose up -d
```

API will be available at `http://localhost:8002`  
Docs at `http://localhost:8002/docs`

### 4. Zeolite / NPM setup

Ports:
- `8002` → FastAPI backend
- `3003` → React frontend (once built)

Add proxy hosts in Nginx Proxy Manager pointing to `192.168.0.246`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/stations/` | List stations with latest prices |
| GET | `/api/v1/stations/{id}` | Station detail |
| GET | `/api/v1/stations/{id}/history` | Price history for a station |
| GET | `/api/v1/prices/cheapest` | Cheapest stations for a fuel type |
| GET | `/api/v1/prices/stats` | UK-wide averages by fuel type |
| GET | `/health` | Health check |

## Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Linting
ruff check .
mypy .
```

## Data

Prices are polled every 30 minutes from the GOV.UK Fuel Finder API. All historical readings are retained in the `price_history` table.

Fuel types: `E10` (Unleaded), `E5` (Super Unleaded), `B7` (Diesel), `SDV` (Super Diesel)
