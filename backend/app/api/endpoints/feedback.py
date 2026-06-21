import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.feedback import Feedback
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackIn(BaseModel):
    name: str | None = Field(None, max_length=120)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=5000)
    page_url: str | None = Field(None, max_length=500)


@router.post("")
@limiter.limit("5/minute")
async def submit_feedback(
    request: Request,
    payload: FeedbackIn,
    db: AsyncSession = Depends(get_db),
) -> dict:
    feedback = Feedback(
        name=payload.name,
        email=payload.email,
        message=payload.message,
        page_url=payload.page_url,
    )
    db.add(feedback)
    await db.commit()
    logger.info(f"Feedback received from {payload.email}")
    return {"status": "ok", "message": "Thank you for your feedback!"}


@router.get("/admin/list")
async def list_feedback(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Feedback).order_by(Feedback.created_at.desc()))
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": f.id,
                "name": f.name,
                "email": f.email,
                "message": f.message,
                "page_url": f.page_url,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in items
        ]
    }


@router.delete("/admin/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    await db.execute(delete(Feedback).where(Feedback.id == feedback_id))
    await db.commit()
    return {"status": "ok"}
