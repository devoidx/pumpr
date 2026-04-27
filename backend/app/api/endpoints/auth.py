from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import (
    create_access_token,
    generate_link_token,
    generate_refresh_token,
    hash_token,
    refresh_token_expiry,
)
from app.auth.password import hash_password, verify_password
from app.core.config import settings
from app.db.session import get_db
from app.models.user import RefreshToken, User, UserToken
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)
from app.services.email import send_password_reset_email, send_verification_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)) -> dict:
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already registered")

    user = User(email=body.email, username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()

    raw_token = generate_link_token()
    db.add(UserToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        purpose="verify_email",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    ))
    await db.commit()

    await send_verification_email(body.email, raw_token)
    logger.info("Registered user %s", body.email)
    return {"message": "Account created. Please check your email to verify your address."}


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access_token, expires_in = create_access_token(str(user.id), user.role)
    raw_refresh = generate_refresh_token()

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=refresh_token_expiry(),
    ))
    await db.execute(update(User).where(User.id == user.id).values(last_login=datetime.now(timezone.utc)))
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    token_hash = hash_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored: RefreshToken | None = result.scalar_one_or_none()
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    stored.revoked = True
    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user: User = user_result.scalar_one()

    new_raw_refresh = generate_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw_refresh),
        expires_at=refresh_token_expiry(),
    ))
    await db.commit()

    access_token, expires_in = create_access_token(str(user.id), user.role)
    response.set_cookie(
        key="refresh_token",
        value=new_raw_refresh,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/resend-verification")
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.is_verified:
        return {"message": "Email already verified"}

    # Invalidate old tokens
    from sqlalchemy import update as _update
    await db.execute(
        _update(UserToken)
        .where(UserToken.user_id == current_user.id, UserToken.purpose == "verify_email")
        .values(used_at=datetime.now(timezone.utc))
    )

    raw_token = generate_link_token()
    db.add(UserToken(
        user_id=current_user.id,
        token_hash=hash_token(raw_token),
        purpose="verify_email",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    ))
    await db.commit()
    await send_verification_email(current_user.email, raw_token)
    return {"message": "Verification email sent"}


@router.get("/verify/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    token_hash = hash_token(token)
    result = await db.execute(
        select(UserToken).where(
            UserToken.token_hash == token_hash,
            UserToken.purpose == "verify_email",
            UserToken.used_at.is_(None),
            UserToken.expires_at > datetime.now(timezone.utc),
        )
    )
    user_token: UserToken | None = result.scalar_one_or_none()
    if user_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link is invalid or has expired")

    user_token.used_at = datetime.now(timezone.utc)
    await db.execute(update(User).where(User.id == user_token.user_id).values(is_verified=True))
    await db.commit()
    return {"message": "Email verified. You can now log in."}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    raw_token = request.cookies.get("refresh_token")
    if raw_token:
        token_hash = hash_token(raw_token)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        stored: RefreshToken | None = result.scalar_one_or_none()
        if stored:
            stored.revoked = True
            await db.commit()
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(body: PasswordResetRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.email == body.email))
    user: User | None = result.scalar_one_or_none()
    if user and user.is_active:
        raw_token = generate_link_token()
        db.add(UserToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            purpose="reset_password",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        await db.commit()
        await send_password_reset_email(body.email, raw_token)
    return {"message": "If that email is registered you will receive a reset link shortly."}


@router.post("/password-reset/confirm")
async def confirm_password_reset(body: PasswordResetConfirm, db: AsyncSession = Depends(get_db)) -> dict:
    token_hash = hash_token(body.token)
    result = await db.execute(
        select(UserToken).where(
            UserToken.token_hash == token_hash,
            UserToken.purpose == "reset_password",
            UserToken.used_at.is_(None),
            UserToken.expires_at > datetime.now(timezone.utc),
        )
    )
    user_token: UserToken | None = result.scalar_one_or_none()
    if user_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or has expired")

    user_token.used_at = datetime.now(timezone.utc)
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == user_token.user_id).values(revoked=True))
    await db.execute(update(User).where(User.id == user_token.user_id).values(password_hash=hash_password(body.new_password)))
    await db.commit()
    return {"message": "Password updated. Please log in with your new password."}
