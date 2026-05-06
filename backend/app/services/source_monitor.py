from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.blog import BlogPost
from app.models.blog_source import BlogSource

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

RELEVANT_KEYWORDS = [
    'petrol', 'diesel', 'pump price', 'forecourt',
    'fuel duty', 'fuel finder', 'wholesale fuel', 'road fuel',
    'fuel prices', 'fuel costs', 'filling station',
    'unleaded', 'electric vehicle charging', 'ev charging',
]

# Keywords that disqualify an article even if relevant keywords match
EXCLUDE_KEYWORDS = [
    'aviation', 'jet fuel', 'airline', 'aircraft', 'airport',
    'veterinary', 'agricultural', 'marine fuel', 'shipping fuel',
    'heating oil', 'kerosene',
]


def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:80]


def _hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


def _is_relevant(title: str, summary: str) -> bool:
    text = (title + ' ' + summary).lower()
    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return False
    return any(kw in text for kw in RELEVANT_KEYWORDS)


async def _fetch_rss(url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={'User-Agent': 'Pumpr/1.0 fuel price tracker'})
        resp.raise_for_status()

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        logger.error(f"RSS parse error for {url}: {e}")
        return []

    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    items = []

    for entry in root.findall('.//atom:entry', ns):
        title = entry.findtext('atom:title', namespaces=ns) or ''
        link_el = entry.find('atom:link', ns)
        link = link_el.get('href', '') if link_el is not None else ''
        summary = entry.findtext('atom:summary', namespaces=ns) or ''
        updated = entry.findtext('atom:updated', namespaces=ns) or ''
        items.append({'title': title, 'link': link, 'summary': summary, 'updated': updated})

    if not items:
        for item in root.findall('.//item'):
            title = item.findtext('title') or ''
            link = item.findtext('link') or ''
            description = item.findtext('description') or ''
            pub_date = item.findtext('pubDate') or ''
            items.append({'title': title, 'link': link, 'summary': description, 'updated': pub_date})

    return items


async def _summarise_article(title: str, url: str, summary: str, source_name: str, category: str) -> BlogPost | None:
    try:
        category_context = {
            'fuel': 'UK fuel prices and the petrol/diesel market',
            'ev': 'electric vehicles and EV charging in the UK',
            'oil': 'global oil markets and their impact on UK fuel prices',
        }.get(category, 'motoring and fuel')

        prompt = f"""You are writing a blog post for Pumpr (pumpr.co.uk), a UK fuel price tracker.

Summarise this article about {category_context} for UK drivers. Write in British English.

Article title: {title}
Source: {source_name}
URL: {url}
Summary/excerpt: {summary}

Requirements:
- 200-250 words
- First line: compelling headline starting with #
- Second line: SUMMARY: one sentence
- Explain why this matters to UK drivers
- Reference the source naturally and encourage readers to read the full article
- Do not reproduce large chunks of the original text
- Do not mention this was AI generated
"""

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': settings.anthropic_api_key,
                    'anthropic-version': '2023-06-01',
                },
                json={
                    'model': 'claude-sonnet-4-5',
                    'max_tokens': 500,
                    'messages': [{'role': 'user', 'content': prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text_content = data['content'][0]['text']

        lines = text_content.strip().split('\n')
        post_title = lines[0].lstrip('#').strip()
        post_summary = ''
        content_lines = []
        for line in lines[1:]:
            if line.startswith('SUMMARY:'):
                post_summary = line.replace('SUMMARY:', '').strip()
            else:
                content_lines.append(line)
        content = '\n'.join(content_lines).strip()
        slug = _slugify(post_title)

        async with AsyncSessionLocal() as session:
            existing_slug = await session.execute(
                select(BlogPost).where(BlogPost.slug == slug)
            )
            if existing_slug.scalar_one_or_none():
                slug = slug[:74] + '-' + datetime.now(timezone.utc).strftime('%d%m%y')

            existing_url = await session.execute(
                select(BlogPost).where(BlogPost.source_url == url)
            )
            if existing_url.scalar_one_or_none():
                logger.info(f"Already have a post for {url} — skipping")
                return None

        post = BlogPost(
            title=post_title,
            slug=slug,
            content=content,
            summary=post_summary or post_title,
            source_url=url,
            source_name=source_name,
            post_type='external',
            published_at=datetime.now(timezone.utc),
        )

        async with AsyncSessionLocal() as session:
            session.add(post)
            await session.commit()
            await session.refresh(post)
            logger.info(f"Created blog post from {source_name}: {post.title}")
            return post

    except Exception as e:
        logger.error(f"Failed to summarise article '{title}': {e}")
        return None


async def check_sources() -> list[BlogPost]:
    """Check RSS sources for new relevant content. Max 1 post per source."""
    new_posts = []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BlogSource).where(
                BlogSource.active.is_(True),
                BlogSource.source_type == 'rss',
            )
        )
        sources = result.scalars().all()

    for source in sources:
        try:
            logger.info(f"Checking RSS source: {source.name}")
            items = await _fetch_rss(source.url)
            content_hash = _hash(''.join(i['title'] for i in items[:10]))

            if content_hash == source.last_content_hash:
                logger.info(f"No new content from {source.name}")
                async with AsyncSessionLocal() as session:
                    src = await session.get(BlogSource, source.id)
                    if src:
                        src.last_checked_at = datetime.now(timezone.utc)
                        await session.commit()
                continue

            # Find single most relevant new unposted item
            best_item = None
            for item in items:
                if not _is_relevant(item['title'], item['summary']):
                    continue
                async with AsyncSessionLocal() as session:
                    existing = await session.execute(
                        select(BlogPost).where(BlogPost.source_url == item['link'])
                    )
                    if existing.scalar_one_or_none():
                        continue
                best_item = item
                break

            if best_item:
                logger.info(f"Found relevant item from {source.name}: {best_item['title']}")
                post = await _summarise_article(
                    best_item['title'],
                    best_item['link'],
                    best_item['summary'],
                    source.name,
                    source.category,
                )
                if post:
                    new_posts.append(post)
            else:
                logger.info(f"No relevant new items from {source.name}")

            async with AsyncSessionLocal() as session:
                src = await session.get(BlogSource, source.id)
                if src:
                    src.last_checked_at = datetime.now(timezone.utc)
                    src.last_content_hash = content_hash
                    await session.commit()

        except Exception as e:
            logger.error(f"Error checking source {source.name}: {e}")

    logger.info(f"Source check complete — {len(new_posts)} new posts generated")
    return new_posts


async def summarise_url(url: str, source_name: str = "External", category: str = "fuel") -> BlogPost | None:
    """Manually summarise a specific URL — for editorial use."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={'User-Agent': 'Pumpr/1.0'})
        resp.raise_for_status()
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', resp.text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else url
    desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', resp.text, re.IGNORECASE)
    summary = desc_match.group(1) if desc_match else ''
    return await _summarise_article(title, url, summary, source_name, category)
