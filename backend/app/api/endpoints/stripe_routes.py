from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import generate_link_token, hash_token
from app.auth.password import hash_password
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserToken
from app.services.email import send_welcome_setup_email

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/stripe", tags=["stripe"])


class CheckoutRequest(BaseModel):
    price_id: str


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
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


@router.post("/create-checkout-session-public")
async def create_checkout_session_public(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create checkout session for non-logged-in users. Account created via webhook."""
    allowed = {settings.stripe_price_monthly, settings.stripe_price_annual}
    if body.price_id not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price")

    # Stripe will collect the email — we pass it to the checkout
    # so if an existing customer exists, Stripe will reuse them
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": body.price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.app_base_url}/pro/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.app_base_url}/pro",
        allow_promotion_codes=True,
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
        session_obj = event["data"]["object"]
        # Use attribute access for StripeObject
        metadata = session_obj.metadata or {}
        customer_details = session_obj.customer_details or {}
        user_id = metadata.get("user_id") if hasattr(metadata, "get") else getattr(metadata, "user_id", None)
        customer_email = getattr(customer_details, "email", None) or getattr(session_obj, "customer_email", None)
        subscription_id = getattr(session_obj, "subscription", None)

        user = None

        # Try user_id from metadata first (logged-in user)
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        # Fall back to email lookup
        if not user and customer_email:
            result = await db.execute(select(User).where(User.email == customer_email))
            user = result.scalar_one_or_none()

        if user:
            # Upgrade existing user
            user.role = "pro"
            user.subscription_status = "active"
            user.subscription_id = subscription_id
            user.is_verified = True
            await db.commit()
            logger.info(f"Upgraded user {user.email} to Pro")
        elif customer_email:
            # Create new Pro user
            temp_pw = secrets.token_urlsafe(32)
            new_user = User(
                email=customer_email,
                username=None,
                password_hash=hash_password(temp_pw),
                role="pro",
                is_verified=True,
                subscription_status="active",
                subscription_id=subscription_id,
            )
            db.add(new_user)
            await db.flush()

            raw_token = generate_link_token()
            db.add(UserToken(
                user_id=new_user.id,
                token_hash=hash_token(raw_token),
                purpose="setup_password",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            ))
            await db.commit()
            await send_welcome_setup_email(customer_email, raw_token)
            logger.info(f"Created new Pro user for {customer_email}")

    elif event_type == "customer.subscription.updated":
        sub = event["data"]["object"]
        await _sync_subscription(db, sub)

    elif event_type == "customer.subscription.deleted":
        sub = event["data"]["object"]
        await _cancel_subscription(db, sub)

    return {"received": True}


async def _sync_subscription(db: AsyncSession, sub: dict) -> None:
    customer_id = sub["customer"]
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user: User | None = result.scalar_one_or_none()
    if not user:
        return

    status_map = {"active": "active", "past_due": "past_due", "canceled": "inactive"}
    new_status = status_map.get(sub["status"], "inactive")
    new_role = "pro" if new_status == "active" else "free"
    period_end = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
    price_id = sub["items"]["data"][0]["price"]["id"]

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
    return {
        "status": current_user.subscription_status,
        "role": current_user.role,
        "price_id": current_user.price_id,
        "current_period_end": current_user.current_period_end.isoformat() if current_user.current_period_end else None,
        "is_monthly": current_user.price_id == settings.stripe_price_monthly,
        "is_annual": current_user.price_id == settings.stripe_price_annual,
    }


@router.post("/resume")
async def resume_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not current_user.subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")
    if current_user.subscription_status != "canceling":
        raise HTTPException(status_code=400, detail="Subscription is not set to cancel")

    stripe.Subscription.modify(
        current_user.subscription_id,
        cancel_at_period_end=False,
    )
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(subscription_status="active")
    )
    await db.commit()
    return {"message": "Subscription resumed successfully"}


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
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
