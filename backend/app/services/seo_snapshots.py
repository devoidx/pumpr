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


def _render_blog_post_snapshot(post: dict) -> str:
    title = f"{post['title']} | Pumpr Insights"
    description = post.get('summary', '')[:300]
    canonical = f"https://pumpr.co.uk/blog/{post['slug']}"
    published = post.get('published_at', '')[:10]
    content_html = post.get('content', '').replace('\n\n', '</p><p>').replace('\n', '<br>')
    source_name = post.get('source_name', '')
    source_url = post.get('source_url', '')
    source_line = f'<p class="source">Source: <a href="{source_url}">{source_name}</a></p>' if source_url else ''
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
    body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0f0f0f; color: #e8e8e8; line-height: 1.6; }}
    h1 {{ color: #f5a623; font-size: 1.5rem; }}
    p {{ margin: 1rem 0; }}
    a {{ color: #f5a623; }}
    .meta {{ font-size: 0.85rem; color: #a0a0a8; margin-bottom: 1.5rem; }}
    .source {{ font-size: 0.8rem; color: #a0a0a8; margin-top: 2rem; border-top: 1px solid #2a2a2a; padding-top: 1rem; }}
  </style>
</head>
<body>
  <p><a href="https://pumpr.co.uk">⛽ Pumpr</a> · <a href="https://pumpr.co.uk/blog">Insights</a></p>
  <h1>{post['title']}</h1>
  <p class="meta">Published {published}</p>
  <p>{content_html}</p>
  {source_line}
</body>
</html>"""


def _render_blog_list_snapshot(posts: list[dict]) -> str:
    title = "Fuel Market Insights & News | Pumpr"
    description = "UK fuel market news, price trends, and insights — updated regularly with the latest developments affecting petrol and diesel prices."
    canonical = "https://pumpr.co.uk/blog"
    rows = ""
    for p in posts:
        rows += f"""
  <article>
    <h2><a href="https://pumpr.co.uk/blog/{p['slug']}">{p['title']}</a></h2>
    <p class="meta">{p.get('published_at', '')[:10]}</p>
    <p>{p.get('summary', '')}</p>
  </article>"""
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
    h1 {{ color: #f5a623; }}
    article {{ border-bottom: 1px solid #2a2a2a; padding: 1rem 0; }}
    h2 {{ font-size: 1.05rem; margin: 0 0 4px; }}
    a {{ color: #f5a623; text-decoration: none; }}
    .meta {{ font-size: 0.75rem; color: #a0a0a8; margin: 0 0 8px; }}
  </style>
</head>
<body>
  <p><a href="https://pumpr.co.uk">⛽ Pumpr</a></p>
  <h1>Fuel Market Insights & News</h1>
  <p>UK fuel market news, price trends, and analysis — updated regularly.</p>
  {rows}
</body>
</html>"""


def _render_intelligence_snapshot(data: dict) -> str:
    title = "UK Fuel Market Intelligence — Live Price Trends & Analysis | Pumpr"
    national = data.get('national', {})
    e10 = national.get('E10', {})
    b7 = national.get('B7', {})
    narrative = data.get('narrative', '')
    description = (
        f"UK average petrol (E10) is {e10.get('avg', '—')}p/litre, diesel (B7) is {b7.get('avg', '—')}p/litre. "
        f"Live market intelligence covering regional trends, brand comparisons and price analysis."
    )[:300]
    canonical = "https://pumpr.co.uk/intelligence"
    updated = data.get('date', '')
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
    body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0f0f0f; color: #e8e8e8; line-height: 1.6; }}
    h1 {{ color: #f5a623; font-size: 1.5rem; }}
    .stat {{ display: inline-block; background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px 20px; margin: 8px 8px 8px 0; }}
    .stat-val {{ font-size: 1.5rem; font-weight: 700; color: #f5a623; }}
    .stat-label {{ font-size: 0.75rem; color: #a0a0a8; margin-top: 2px; }}
    p {{ margin: 1rem 0; }}
    .updated {{ font-size: 0.75rem; color: #5a5a68; margin-top: 2rem; }}
  </style>
</head>
<body>
  <p><a href="https://pumpr.co.uk">⛽ Pumpr</a></p>
  <h1>UK Fuel Market Intelligence</h1>
  <div>
    <div class="stat"><div class="stat-val">{e10.get('avg', '—')}p</div><div class="stat-label">UK avg Petrol (E10)</div></div>
    <div class="stat"><div class="stat-val">{b7.get('avg', '—')}p</div><div class="stat-label">UK avg Diesel (B7)</div></div>
    <div class="stat"><div class="stat-val">{e10.get('min', '—')}p</div><div class="stat-label">Cheapest E10 nationally</div></div>
    <div class="stat"><div class="stat-val">{b7.get('min', '—')}p</div><div class="stat-label">Cheapest B7 nationally</div></div>
  </div>
  <p>{narrative}</p>
  <p>See full regional breakdowns, brand comparisons and price trend charts at <a href="{canonical}">pumpr.co.uk/intelligence</a></p>
  <p class="updated">Data as of: {updated}</p>
</body>
</html>"""


async def generate_blog_snapshots() -> int:
    """Generate static HTML snapshots for the blog list and all individual posts."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    blog_dir = os.path.join(SNAPSHOT_DIR, "blog")
    os.makedirs(blog_dir, exist_ok=True)
    generated = 0
    async with httpx.AsyncClient(timeout=30, base_url="http://localhost:8000") as client:
        try:
            r = await client.get("/api/v1/blog?limit=50")
            if r.status_code == 200:
                posts = r.json().get("posts", [])
                # List page
                list_html = _render_blog_list_snapshot(posts[:30])
                with open(os.path.join(SNAPSHOT_DIR, "blog.html"), "w", encoding="utf-8") as f:
                    f.write(list_html)
                generated += 1
                # Individual posts
                for post in posts:
                    try:
                        post_html = _render_blog_post_snapshot(post)
                        path = os.path.join(blog_dir, f"{post['slug']}.html")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(post_html)
                        generated += 1
                    except Exception as e:
                        logger.warning(f"Blog post snapshot failed for {post.get('slug')}: {e}")
            else:
                logger.warning(f"Blog snapshot: list fetch returned {r.status_code}")
        except Exception as e:
            logger.warning(f"Blog snapshot generation failed: {e}")
    logger.info(f"Generated {generated} blog snapshots")
    return generated


async def generate_intelligence_snapshot() -> int:
    """Generate static HTML snapshot for the intelligence page."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    async with httpx.AsyncClient(timeout=30, base_url="http://localhost:8000") as client:
        try:
            r = await client.get("/api/v1/intelligence/latest")
            if r.status_code == 200:
                data = r.json()
                html = _render_intelligence_snapshot(data)
                path = os.path.join(SNAPSHOT_DIR, "intelligence.html")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info("Generated intelligence snapshot")
                return 1
            else:
                logger.warning(f"Intelligence snapshot: returned {r.status_code}")
                return 0
        except Exception as e:
            logger.warning(f"Intelligence snapshot generation failed: {e}")
            return 0


EU_SNAPSHOT_CITIES = {
    "ES": [
        "madrid", "barcelona", "malaga", "alicante", "valencia",
        "seville", "palma", "las-palmas", "bilbao", "murcia", "girona", "marbella",
    ],
    "IT": [
        "rome", "milan", "turin", "naples", "palermo", "genoa",
        "florence", "bologna", "catania", "verona", "venice", "bari",
    ],
    "FR": [
        "calais", "boulogne-sur-mer", "dunkirk", "lille", "rouen",
        "paris", "reims", "le-havre", "caen", "rennes",
        "saint-malo", "bordeaux", "toulouse", "lyon", "nice", "marseille",
    ],
    "DE": [
        "aachen", "cologne", "mainz", "frankfurt", "heidelberg", "karlsruhe",
        "freiburg", "stuttgart", "munich", "hamburg", "hanover", "kassel",
    ],
}


def _render_eu_snapshot(country: str, city: str, data: dict) -> str:
    city_name = data.get("city", city.title())
    country_name = {"FR": "France", "DE": "Germany", "ES": "Spain", "IT": "Italy"}.get(country, country)
    eur_to_gbp = data.get("eur_to_gbp")
    stats = data.get("stats", {})
    cheapest = data.get("cheapest", {})

    diesel_stats = stats.get("Diesel", {})
    e5_stats = stats.get("E5", {})
    diesel_min = diesel_stats.get("min", "—")
    e5_min = e5_stats.get("min", "—")

    rate_line = f"£1 = €{(1 / eur_to_gbp):.4f}" if eur_to_gbp else ""

    title = f"Cheap Fuel in {city_name}, {country_name} — Prices for UK Travellers | Pumpr"
    description = (
        f"Petrol and diesel prices near {city_name}, {country_name} for UK drivers. "
        f"Diesel from €{diesel_min}/litre, Petrol (E5) from €{e5_min}/litre. "
        f"Prices updated daily from official government data."
    )
    canonical = f"https://pumpr.co.uk/cheap-fuel/europe/{country.lower()}/{city}"
    updated = datetime.utcnow().strftime("%d %B %Y %H:%M UTC")

    def station_rows(fuel: str) -> str:
        rows = ""
        for s in cheapest.get(fuel, [])[:5]:
            gbp_col = f"≈ {s['price_gbp'] * 100:.1f}p" if s.get("price_gbp") else ""
            rows += f"""
        <tr>
          <td>{s.get('name') or s.get('address', '')}</td>
          <td>{s.get('city', '')} {s.get('postcode', '')}</td>
          <td><strong>€{s['price_eur']:.3f}</strong></td>
          <td>{gbp_col}</td>
          <td>{s['distance_km']}km</td>
        </tr>"""
        return rows

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
    .rate {{ font-size: 0.85rem; color: #a0a0a8; margin-bottom: 1rem; }}
    a {{ color: #f5a623; }}
    .updated {{ font-size: 0.75rem; color: #5a5a68; margin-top: 2rem; }}
  </style>
</head>
<body>
  <p><a href="https://pumpr.co.uk">⛽ Pumpr</a></p>
  <h1>Cheap Fuel in {city_name}, {country_name}</h1>
  <p>Petrol and diesel prices for UK travellers near {city_name}. Updated daily from official government data.</p>
  {f'<p class="rate">Exchange rate: {rate_line} (ECB daily reference rate)</p>' if rate_line else ''}

  <div>
    <div class="stat"><div class="stat-val">€{diesel_min}</div><div class="stat-label">Cheapest Diesel</div></div>
    <div class="stat"><div class="stat-val">€{e5_min}</div><div class="stat-label">Cheapest Petrol (E5)</div></div>
  </div>

  <h2>Cheapest Diesel near {city_name}</h2>
  <table>
    <thead><tr><th>Station</th><th>Location</th><th>Price (EUR)</th><th>Price (GBP)</th><th>Distance</th></tr></thead>
    <tbody>{station_rows("Diesel")}</tbody>
  </table>

  <h2>Cheapest Petrol (E5) near {city_name}</h2>
  <table>
    <thead><tr><th>Station</th><th>Location</th><th>Price (EUR)</th><th>Price (GBP)</th><th>Distance</th></tr></thead>
    <tbody>{station_rows("E5")}</tbody>
  </table>

  <p>See full results and map view at <a href="{canonical}">pumpr.co.uk/cheap-fuel/europe/{country.lower()}/{city}</a></p>
  <p class="updated">Last updated: {updated}</p>
</body>
</html>"""


async def generate_eu_city_snapshots() -> int:
    """Generate static HTML snapshots for EU city landing pages."""
    generated = 0
    async with httpx.AsyncClient(timeout=30, base_url="http://localhost:8000") as client:
        for country, cities in EU_SNAPSHOT_CITIES.items():
            country_dir = os.path.join(SNAPSHOT_DIR, "europe", country.lower())
            os.makedirs(country_dir, exist_ok=True)
            for city in cities:
                try:
                    r = await client.get(f"/api/v1/eu/cheap-fuel/{country}/{city}")
                    if r.status_code == 200:
                        data = r.json()
                        html = _render_eu_snapshot(country, city, data)
                        path = os.path.join(country_dir, f"{city}.html")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(html)
                        generated += 1
                    else:
                        logger.warning("EU snapshot: %s/%s returned %s", country, city, r.status_code)
                except Exception as e:
                    logger.warning("EU snapshot: %s/%s failed: %s", country, city, e)
    logger.info("Generated %d EU city snapshots", generated)
    return generated


async def generate_europe_landing_snapshot() -> int:
    """Generate static HTML snapshot for the /europe landing page."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    title = "European Fuel Prices for UK Travellers — Pumpr"
    description = "Find cheap petrol and diesel prices in France for UK drivers. Compare station prices in EUR and GBP, updated daily from official government data."
    canonical = "https://pumpr.co.uk/europe"
    updated = datetime.utcnow().strftime("%d %B %Y %H:%M UTC")

    cities = [
        ("calais", "Calais"), ("boulogne-sur-mer", "Boulogne-sur-Mer"),
        ("dunkirk", "Dunkirk"), ("lille", "Lille"), ("rouen", "Rouen"),
        ("paris", "Paris"), ("reims", "Reims"), ("le-havre", "Le Havre"),
        ("caen", "Caen"), ("rennes", "Rennes"), ("saint-malo", "Saint-Malo"),
        ("bordeaux", "Bordeaux"), ("toulouse", "Toulouse"), ("lyon", "Lyon"),
        ("nice", "Nice"), ("marseille", "Marseille"),
    ]
    city_links = "".join(
        f'<a href="https://pumpr.co.uk/cheap-fuel/europe/fr/{slug}" style="display:inline-block;padding:10px 16px;margin:4px;background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;color:#e8e8e8;text-decoration:none;">{name}</a>'
        for slug, name in cities
    )

    html = f"""<!DOCTYPE html>
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
    body {{ font-family: sans-serif; max-width: 860px; margin: 0 auto; padding: 20px; background: #0f0f0f; color: #e8e8e8; }}
    h1 {{ color: #f5a623; }} h2 {{ color: #e8e8e8; font-size: 1.1rem; margin-top: 2rem; }}
    a {{ color: #f5a623; }}
    .updated {{ font-size: 0.75rem; color: #5a5a68; margin-top: 2rem; }}
  </style>
</head>
<body>
  <p><a href="https://pumpr.co.uk">⛽ Pumpr</a></p>
  <h1>European Fuel Prices for UK Travellers</h1>
  <p>Planning a driving holiday? Compare petrol and diesel prices at stations across France, shown in both EUR and GBP. Updated daily from official government data.</p>
  <h2>🇫🇷 France</h2>
  <div>{city_links}</div>
  <p class="updated">Last updated: {updated}</p>
</body>
</html>"""

    path = os.path.join(SNAPSHOT_DIR, "europe.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("Generated Europe landing snapshot")
    return 1
