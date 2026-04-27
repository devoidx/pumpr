from __future__ import annotations

import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/stripe", tags=["stripe"])


class CheckoutRequest(BaseModel):
    price_id: str  # must be one of the two configured price IDs


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before subscribing"
        )

    # Validate price_id is one we recognise
    allowed = {settings.stripe_price_monthly, settings.stripe_price_annual}
    if body.price_id not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price")

    # Reuse existing Stripe customer or create one
    customer_id = current_user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": str(current_user.id)},
        )
        customer_id = customer.id
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(stripe_customer_id=customer_id)
        )
        await db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": body.price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.app_base_url}/pro/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.app_base_url}/pro",
        metadata={"user_id": str(current_user.id)},
    )

    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    logger.info("Stripe webhook: %s", event_type)

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        subscription_id = session.get("subscription")
        if user_id and subscription_id:
            await _activate_subscription(db, user_id, subscription_id)

    elif event_type == "customer.subscription.updated":
        sub = event["data"]["object"]
        await _sync_subscription(db, sub)

    elif event_type == "customer.subscription.deleted":
        sub = event["data"]["object"]
        await _cancel_subscription(db, sub)

    return {"received": True}


async def _activate_subscription(db: AsyncSession, user_id: str, subscription_id: str) -> None:
    sub = stripe.Subscription.retrieve(subscription_id)
    period_end = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
    price_id = sub["items"]["data"][0]["price"]["id"]

    await db.execute(
        update(User)
        .where(User.id == user_id)  # type: ignore[arg-type]
        .values(
            role="pro",
            subscription_status="active",
            subscription_id=subscription_id,
            price_id=price_id,
            current_period_end=period_end,
        )
    )
    await db.commit()
    logger.info("Activated Pro for user %s", user_id)


async def _sync_subscription(db: AsyncSession, sub: dict) -> None:
    customer_id = sub["customer"]
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user: User | None = result.scalar_one_or_none()
    if not user:
        return

    status_map = {"active": "active", "past_due": "past_due", "canceled": "inactive"}
    new_status = status_map.get(sub["status"], "inactive")
    new_role   = "pro" if new_status == "active" else "free"
    period_end = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
    price_id   = sub["items"]["data"][0]["price"]["id"]

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            role=new_role,
            subscription_status=new_status,
            subscription_id=sub["id"],
            price_id=price_id,
            current_period_end=period_end,
        )
    )
    await db.commit()
    logger.info("Synced subscription for user %s → %s", user.email, new_status)


async def _cancel_subscription(db: AsyncSession, sub: dict) -> None:
    customer_id = sub["customer"]
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user: User | None = result.scalar_one_or_none()
    if not user:
        return

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(role="free", subscription_status="inactive", subscription_id=None, current_period_end=None)
    )
    await db.commit()
    logger.info("Cancelled subscription for user %s", user.email)


@router.get("/subscription")
async def get_subscription(current_user: User = Depends(get_current_user)) -> dict:
    """Return current user's subscription details."""
    return {
        "status": current_user.subscription_status,
        "role": current_user.role,
        "price_id": current_user.price_id,
        "current_period_end": current_user.current_period_end.isoformat() if current_user.current_period_end else None,
        "is_monthly": current_user.price_id == settings.stripe_price_monthly,
        "is_annual": current_user.price_id == settings.stripe_price_annual,
    }


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel at period end — user keeps Pro until current_period_end."""
    if not current_user.subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    stripe.Subscription.modify(
        current_user.subscription_id,
        cancel_at_period_end=True,
    )
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(subscription_status="canceling")
    )
    await db.commit()
    return {"message": "Subscription will cancel at the end of the current period"}
