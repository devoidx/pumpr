import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.db.session import get_db
from app.models.feedback import Feedback

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
