#!/usr/bin/env python3
"""Generate sitemap.xml and write to frontend public folder."""
import asyncio
import os
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]
OUTPUT_PATH = os.environ.get("SITEMAP_OUTPUT", "/app/dist/sitemap.xml")
BASE_URL = "https://pumpr.co.uk"

STATIC_PAGES = [
    ("/", "daily", "1.0"),
    ("/blog", "weekly", "0.8"),
    ("/stats", "daily", "0.7"),
    ("/about", "monthly", "0.5"),
    ("/pro", "monthly", "0.6"),
]

CITIES = [
    "london", "manchester", "birmingham", "leeds", "glasgow", "liverpool",
    "edinburgh", "bristol", "sheffield", "newcastle", "nottingham", "cardiff",
    "leicester", "coventry", "bradford", "belfast", "wolverhampton", "plymouth",
    "derby", "reading", "southampton", "portsmouth", "exeter", "cambridge",
    "oxford", "york", "norwich", "swansea", "aberdeen", "dundee",
]

async def main():
    engine = create_async_engine(DATABASE_URL)
    now = datetime.utcnow().strftime("%Y-%m-%d")
    urls = []

    for path, changefreq, priority in STATIC_PAGES:
        urls.append(f"  <url><loc>{BASE_URL}{path}</loc><lastmod>{now}</lastmod><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>")

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT slug, published_at FROM blog_posts ORDER BY published_at DESC"))
        for row in result.fetchall():
            date = row.published_at.strftime("%Y-%m-%d")
            urls.append(f"  <url><loc>{BASE_URL}/blog/{row.slug}</loc><lastmod>{date}</lastmod><changefreq>never</changefreq><priority>0.6</priority></url>")

        result = await conn.execute(text("SELECT DISTINCT LOWER(REPLACE(county, ' ', '-')) as slug FROM stations WHERE county IS NOT NULL ORDER BY slug"))
        for row in result.fetchall():
            urls.append(f"  <url><loc>{BASE_URL}/cheap-fuel/{row.slug}</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>")

    for city in CITIES:
        urls.append(f"  <url><loc>{BASE_URL}/cheap-fuel/{city}</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>")

    await engine.dispose()

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>"

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(xml)
    print(f"Sitemap written to {OUTPUT_PATH} ({len(urls)} URLs)")

asyncio.run(main())
