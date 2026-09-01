import asyncio
from app.services.eu.germany_client import fetch_corridor_stations
from app.services.eu.ingest import upsert_eu_rows
from app.db.session import AsyncSessionLocal

async def main():
    rows = await fetch_corridor_stations()
    print(f'fetch_corridor_stations returned {len(rows)} price rows')
    unique_stations = len({(r["country"], r["external_id"]) for r in rows})
    print(f'{unique_stations} unique stations found')
    async with AsyncSessionLocal() as db:
        stations, prices = await upsert_eu_rows(rows, db)
    print(f'upserted: {stations} stations, {prices} prices')

asyncio.run(main())
