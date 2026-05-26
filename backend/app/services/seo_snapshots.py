from __future__ import annotations

import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = "/app/snapshots"
CITIES = [
    "london", "manchester", "birmingham", "leeds", "glasgow", "liverpool",
    "edinburgh", "bristol", "sheffield", "newcastle", "nottingham", "cardiff",
    "leicester", "coventry", "bradford", "belfast", "wolverhampton", "plymouth",
    "derby", "reading", "southampton", "portsmouth", "exeter", "cambridge",
    "oxford", "york", "norwich", "swansea", "aberdeen", "dundee",
]


def _render_snapshot(city: str, data: dict) -> str:
    location = data.get("location", {})
    city_name = location.get("name", city.title())
    region = location.get("region", "")
    stats = data.get("stats", {})
    cheapest = data.get("cheapest", {})
    national = data.get("national", {})

    e10_stats = stats.get("E10", {})
    b7_stats = stats.get("B7", {})
    e10_min = e10_stats.get("min", "—")
    b7_min = b7_stats.get("min", "—")
    e10_nat = national.get("E10", "—")
    b7_nat = national.get("B7", "—")

    title = f"Cheapest Petrol & Diesel in {city_name} — Live Prices | Pumpr"
    description = (
        f"Find the cheapest fuel in {city_name} today. "
        f"Petrol (E10) from {e10_min}p/litre, Diesel (B7) from {b7_min}p/litre. "
        f"Live prices from 8,000+ UK stations updated every 30 minutes."
    )
    canonical = f"https://pumpr.co.uk/cheap-fuel/{city}"

    # Build station rows for E10
    station_rows = ""
    for s in cheapest.get("E10", [])[:5]:
        station_rows += f"""
        <tr>
          <td>{s['name']}</td>
          <td>{s.get('address','')}</td>
          <td><strong>{s['price_pence']}p</strong></td>
          <td>{s['distance_km']}km</td>
        </tr>"""

    b7_rows = ""
    for s in cheapest.get("B7", [])[:5]:
        b7_rows += f"""
        <tr>
          <td>{s['name']}</td>
          <td>{s.get('address','')}</td>
          <td><strong>{s['price_pence']}p</strong></td>
          <td>{s['distance_km']}km</td>
        </tr>"""

    updated = datetime.utcnow().strftime("%d %B %Y %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <style>
    body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0f0f0f; color: #e8e8e8; }}
    h1 {{ color: #f5a623; }} h2 {{ color: #e8e8e8; font-size: 1.1rem; margin-top: 2rem; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }}
    th {{ text-align: left; color: #a0a0a8; padding: 6px 8px; border-bottom: 1px solid #2a2a2a; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #1a1a1a; }}
    .stat {{ display: inline-block; background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px 20px; margin: 8px 8px 8px 0; }}
    .stat-val {{ font-size: 1.5rem; font-weight: 700; color: #f5a623; }}
    .stat-label {{ font-size: 0.75rem; color: #a0a0a8; margin-top: 2px; }}
    a {{ color: #f5a623; }}
    .updated {{ font-size: 0.75rem; color: #5a5a68; margin-top: 2rem; }}
  </style>
</head>
<body>
  <p><a href="https://pumpr.co.uk">⛽ Pumpr</a></p>
  <h1>Cheapest Fuel in {city_name}{', ' + region if region else ''}</h1>
  <p>Live petrol and diesel prices near {city_name}, updated every 30 minutes from 8,000+ UK stations.</p>

  <div>
    <div class="stat"><div class="stat-val">{e10_min}p</div><div class="stat-label">Cheapest E10 locally</div></div>
    <div class="stat"><div class="stat-val">{b7_min}p</div><div class="stat-label">Cheapest B7 locally</div></div>
    <div class="stat"><div class="stat-val">{e10_nat}p</div><div class="stat-label">UK avg E10</div></div>
    <div class="stat"><div class="stat-val">{b7_nat}p</div><div class="stat-label">UK avg B7</div></div>
  </div>

  <h2>Cheapest Petrol (E10) near {city_name}</h2>
  <table>
    <thead><tr><th>Station</th><th>Address</th><th>Price</th><th>Distance</th></tr></thead>
    <tbody>{station_rows}</tbody>
  </table>

  <h2>Cheapest Diesel (B7) near {city_name}</h2>
  <table>
    <thead><tr><th>Station</th><th>Address</th><th>Price</th><th>Distance</th></tr></thead>
    <tbody>{b7_rows}</tbody>
  </table>

  <p>See full results, map view and filter by brand at <a href="{canonical}">pumpr.co.uk/cheap-fuel/{city}</a></p>
  <p class="updated">Last updated: {updated}</p>
</body>
</html>"""


async def generate_city_snapshots() -> int:
    """Generate static HTML snapshots for all city landing pages."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    generated = 0
    async with httpx.AsyncClient(timeout=30, base_url="http://localhost:8000") as client:
        for city in CITIES:
            try:
                r = await client.get(f"/api/v1/locations/cheap-fuel/{city}")
                if r.status_code == 200:
                    data = r.json()
                    html = _render_snapshot(city, data)
                    path = os.path.join(SNAPSHOT_DIR, f"{city}.html")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(html)
                    generated += 1
                else:
                    logger.warning(f"Snapshot: {city} returned {r.status_code}")
            except Exception as e:
                logger.warning(f"Snapshot: {city} failed: {e}")
    logger.info(f"Generated {generated}/{len(CITIES)} city snapshots")
    return generated
