from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["sitemap"])

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
    "derby", "reading", "Southampton", "portsmouth", "exeter", "cambridge",
    "oxford", "york", "norwich", "swansea", "aberdeen", "dundee",
]


@router.get("/sitemap.xml")
async def sitemap(db: AsyncSession = Depends(get_db)) -> Response:
    base = "https://pumpr.co.uk"
    now = datetime.utcnow().strftime("%Y-%m-%d")

    urls = []

    # Static pages
    for path, changefreq, priority in STATIC_PAGES:
        urls.append(f"""  <url>
    <loc>{base}{path}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    # Blog posts
    result = await db.execute(
        text("SELECT slug, published_at FROM blog_posts ORDER BY published_at DESC")
    )
    for row in result.fetchall():
        date = row.published_at.strftime("%Y-%m-%d")
        urls.append(f"""  <url>
    <loc>{base}/blog/{row.slug}</loc>
    <lastmod>{date}</lastmod>
    <changefreq>never</changefreq>
    <priority>0.6</priority>
  </url>""")

    # County pages
    result = await db.execute(
        text("SELECT DISTINCT LOWER(REPLACE(county, ' ', '-')) as slug FROM stations WHERE county IS NOT NULL ORDER BY slug")
    )
    for row in result.fetchall():
        urls.append(f"""  <url>
    <loc>{base}/cheap-fuel/{row.slug}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>""")

    # City pages
    for city in CITIES:
        urls.append(f"""  <url>
    <loc>{base}/cheap-fuel/{city}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>""")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>"

    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt")
async def robots() -> Response:
    content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /my-alerts
Disallow: /my-places
Disallow: /my-vehicles
Disallow: /profile
Disallow: /setup-password
Disallow: /verify-email
Disallow: /reset-password
Disallow: /pro/success

Sitemap: https://pumpr.co.uk/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")
