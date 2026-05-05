from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.blog import BlogPost

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/blog", tags=["blog"])


def _post_out(p: BlogPost) -> dict:
    return {
        "id": str(p.id),
        "title": p.title,
        "slug": p.slug,
        "content": p.content,
        "summary": p.summary,
        "source_url": p.source_url,
        "source_name": p.source_name,
        "post_type": p.post_type,
        "published_at": p.published_at.isoformat(),
    }


@router.get("")
async def list_posts(
    limit: int = Query(10, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(BlogPost)
        .order_by(BlogPost.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = result.scalars().all()
    return {
        "posts": [_post_out(p) for p in posts],
        "total": len(posts),
    }


@router.get("/{slug}")
async def get_post(slug: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_out(post)
