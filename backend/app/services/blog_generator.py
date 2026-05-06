from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.blog import BlogPost

logger = logging.getLogger(__name__)

GOV_STATS_PAGE = "https://www.gov.uk/government/statistics/weekly-road-fuel-prices"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

STYLES = [
    "analytical and data-driven, using specific numbers and comparisons",
    "conversational and accessible, written for everyday drivers",
    "focused on historical context, comparing current prices to past peaks and troughs",
    "consumer-focused, emphasising practical tips for saving money on fuel",
    "investigative in tone, questioning why prices are moving the way they are",
]

async def _fetch_gov_csv() -> list[dict]:
    """Fetch and parse the GOV.UK weekly fuel prices CSV — discovers URL dynamically."""
    import re as _re
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # Fetch the stats page to find the current CSV URL
        page = await client.get(GOV_STATS_PAGE)
        page.raise_for_status()
        match = _re.search(r'https://assets\.publishing\.service\.gov\.uk/[^"]+weekly_road_fuel_prices_\d+\.csv', page.text)
        if not match:
            raise ValueError("Could not find CSV URL on GOV.UK stats page")
        csv_url = match.group(0)
        logger.info(f"Found CSV URL: {csv_url}")
        resp = await client.get(csv_url)
        resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text.lstrip('\ufeff')))
    rows = list(reader)
    return rows


async def _get_pumpr_stats() -> dict:
    """Get current stats from our own DB."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence, price_flagged
                FROM price_history
                WHERE recorded_at > NOW() - INTERVAL '2 hours'
                ORDER BY station_id, fuel_type, recorded_at DESC
            )
            SELECT fuel_type,
                   ROUND(AVG(price_pence)::numeric, 1) as avg_price,
                   MIN(price_pence) as min_price,
                   MAX(price_pence) as max_price,
                   COUNT(*) as station_count
            FROM latest
            WHERE price_flagged = FALSE OR price_flagged IS NULL
            GROUP BY fuel_type
            ORDER BY fuel_type
        """))
        return {r.fuel_type: {
            "avg": float(r.avg_price),
            "min": float(r.min_price),
            "max": float(r.max_price),
            "count": int(r.station_count),
        } for r in result.fetchall()}


def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:80]


async def generate_weekly_post(style_index: int | None = None) -> BlogPost | None:
    """Fetch GOV.UK CSV, get Pumpr stats, generate blog post via Claude API."""
    try:
        rows = await _fetch_gov_csv()
        if not rows:
            logger.error("No rows from GOV.UK CSV")
            return None

        # Get last two weeks
        latest = rows[-1]
        prev = rows[-2] if len(rows) >= 2 else None
        year_ago = rows[-53] if len(rows) >= 53 else None

        petrol_now = float(latest['ULSP (Ultra low sulphur unleaded petrol) Pump price in pence/litre'])
        diesel_now = float(latest['ULSD (Ultra low sulphur diesel) Pump price in pence/litre'])
        week_date = latest['Date']

        petrol_prev = float(prev['ULSP (Ultra low sulphur unleaded petrol) Pump price in pence/litre']) if prev else None
        diesel_prev = float(prev['ULSD (Ultra low sulphur diesel) Pump price in pence/litre']) if prev else None
        petrol_yoy = float(year_ago['ULSP (Ultra low sulphur unleaded petrol) Pump price in pence/litre']) if year_ago else None
        diesel_yoy = float(year_ago['ULSD (Ultra low sulphur diesel) Pump price in pence/litre']) if year_ago else None

        pumpr_stats = await _get_pumpr_stats()

        # Pick style
        import random
        style = STYLES[style_index % len(STYLES)] if style_index is not None else random.choice(STYLES)

        # Build prompt
        prompt = f"""You are writing a blog post for Pumpr (pumpr.co.uk), a UK fuel price tracker.

Write a blog post about this week's UK fuel prices. Be {style}.

Data:
- Week commencing: {week_date}
- Petrol (ULSP): {petrol_now}p/litre
- Diesel (ULSD): {diesel_now}p/litre
- Previous week petrol: {petrol_prev}p, diesel: {diesel_prev}p
- Year ago petrol: {petrol_yoy}p, diesel: {diesel_yoy}p
- All-time peak: petrol 191.6p (July 2022), diesel 199.2p (July 2022)
- Fuel duty: 52.95p/litre (frozen since March 2022)
- Pumpr live data (from 7,600+ stations): {pumpr_stats}

Requirements:
- 300-400 words
- Include a compelling headline as the first line starting with #
- Include a one-sentence summary as the second line starting with SUMMARY:
- Write in British English
- Do not mention that this was AI generated
- Reference pumpr.co.uk naturally where relevant
- Data source: Department for Energy Security and Net Zero weekly road fuel prices
- Do not reproduce large chunks of data verbatim
"""

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                headers={"Content-Type": "application/json", "x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text_content = data["content"][0]["text"]

        lines = text_content.strip().split('\n')
        title = lines[0].lstrip('#').strip()
        summary = ""
        content_lines = []
        for line in lines[1:]:
            if line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            else:
                content_lines.append(line)
        content = '\n'.join(content_lines).strip()

        slug = _slugify(f"uk-fuel-prices-{week_date.replace('/', '-')}")

        post = BlogPost(
            title=title,
            slug=slug,
            content=content,
            summary=summary or title,
            source_url="https://www.gov.uk/government/statistics/weekly-road-fuel-prices",
            source_name="Department for Energy Security and Net Zero",
            post_type="weekly_prices",
            published_at=datetime.now(timezone.utc),
        )

        async with AsyncSessionLocal() as session:
            session.add(post)
            await session.commit()
            await session.refresh(post)
            logger.info(f"Generated blog post: {post.title}")

            # Post to social media
            try:
                import os

                from app.services.social import _bsky_client, _mastodon_post, _threads_post
                enable_social = os.getenv("ENABLE_SOCIAL_POSTS", "false").lower() == "true"
                if enable_social:
                    post_url = f"https://pumpr.co.uk/blog/{post.slug}"
                    social_text = f"📊 {post.title}\n\n{post.summary}\n\n{post_url}\n\n#UKFuel #FuelPrices #Pumpr"
                    try:
                        client = _bsky_client()
                        client.send_post(text=social_text)
                        logger.info("Blog post shared to Bluesky")
                    except Exception as e:
                        logger.error(f"Blog Bluesky post failed: {e}")
                    _mastodon_post(social_text)
                    _threads_post(social_text)
            except Exception as e:
                logger.error(f"Blog social posting failed: {e}")

            return post

    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        return None
