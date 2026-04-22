#!/usr/bin/env python3
"""
Pumpr auth install script
Run once on zeolite from /opt/pumpr:

    cd /opt/pumpr
    python3 pumpr_auth_install.py

What it does:
  1.  Creates  postgres/002_add_users.sql
  2.  Creates  backend/app/auth/__init__.py
  3.  Creates  backend/app/auth/password.py
  4.  Creates  backend/app/auth/jwt.py
  5.  Creates  backend/app/auth/dependencies.py
  6.  Creates  backend/app/models/user.py
  7.  Creates  backend/app/schemas/user.py
  8.  Creates  backend/app/services/email.py
  9.  Creates  backend/app/api/endpoints/auth.py
  10. Patches   backend/app/core/config.py        (add SMTP + APP_BASE_URL fields)
  11. Patches   backend/app/models/__init__.py     (import new models)
  12. Patches   backend/app/api/router.py          (register auth router)
  13. Patches   backend/requirements.txt           (add python-jose, passlib, pydantic[email])
  14. Creates   frontend/src/contexts/AuthContext.jsx
  15. Creates   frontend/src/hooks/useAuth.js
  16. Creates   frontend/src/components/auth/AuthModal.css
  17. Creates   frontend/src/components/auth/LoginModal.jsx
  18. Creates   frontend/src/components/auth/RegisterModal.jsx
  19. Creates   frontend/src/components/auth/UserMenu.jsx
  20. Creates   frontend/src/components/auth/VerifyEmailPage.jsx
  21. Creates   frontend/src/components/auth/ResetPasswordPage.jsx
  22. Patches   frontend/src/main.jsx              (wrap in AuthProvider)
  23. Patches   frontend/src/App.jsx               (add verify/reset routes)
  24. Patches   frontend/src/components/Navbar.jsx (add NavAuthSection)
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend" / "app"
FRONTEND = ROOT / "frontend" / "src"

errors = []

# ── helpers ───────────────────────────────────────────────────────────────────

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  WRITE  {path.relative_to(ROOT)}")


def patch(path: Path, find: str, replace: str, description: str) -> None:
    if not path.exists():
        errors.append(f"PATCH FAILED ({description}): {path} not found")
        return
    text = path.read_text()
    if replace in text:
        print(f"  SKIP   {path.relative_to(ROOT)} — already patched ({description})")
        return
    if find not in text:
        errors.append(f"PATCH FAILED ({description}): marker not found in {path}")
        return
    path.write_text(text.replace(find, replace, 1))
    print(f"  PATCH  {path.relative_to(ROOT)} ({description})")


def append_if_missing(path: Path, marker: str, content: str, description: str) -> None:
    if not path.exists():
        errors.append(f"APPEND FAILED ({description}): {path} not found")
        return
    text = path.read_text()
    if marker in text:
        print(f"  SKIP   {path.relative_to(ROOT)} — already present ({description})")
        return
    path.write_text(text.rstrip() + "\n" + content + "\n")
    print(f"  APPEND {path.relative_to(ROOT)} ({description})")


# ═════════════════════════════════════════════════════════════════════════════
# 1. DB migration
# ═════════════════════════════════════════════════════════════════════════════
print("\n[1/24] DB migration SQL")
write(ROOT / "postgres" / "002_add_users.sql", """\
-- Migration: 002_add_users
-- Run: docker exec -i pumpr_db psql -U pumpr pumpr < postgres/002_add_users.sql

CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT        NOT NULL UNIQUE,
    username        TEXT        NOT NULL UNIQUE,
    password_hash   TEXT        NOT NULL,
    is_verified     BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    role            TEXT        NOT NULL DEFAULT 'free'
                                CHECK (role IN ('free', 'pro', 'admin')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email    ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash  TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked     BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id    ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens (expires_at);

CREATE TABLE IF NOT EXISTS user_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash  TEXT        NOT NULL UNIQUE,
    purpose     TEXT        NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_tokens_user_id    ON user_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_user_tokens_token_hash ON user_tokens (token_hash);
""")

# ═════════════════════════════════════════════════════════════════════════════
# 2-5. backend/app/auth/
# ═════════════════════════════════════════════════════════════════════════════
print("\n[2/24] auth/__init__.py")
write(BACKEND / "auth" / "__init__.py", "# app/auth\n")

print("\n[3/24] auth/password.py")
write(BACKEND / "auth" / "password.py", """\
from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _ctx.verify(plain, hashed)
""")

print("\n[4/24] auth/jwt.py")
write(BACKEND / "auth" / "jwt.py", """\
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    \"\"\"Return (encoded_jwt, expires_in_seconds).\"\"\"
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + delta
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, int(delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


def generate_link_token() -> str:
    return secrets.token_urlsafe(48)
""")

print("\n[5/24] auth/dependencies.py")
write(BACKEND / "auth" / "dependencies.py", """\
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.jwt import decode_access_token
from app.db.session import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise exc
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user: User | None = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise exc
    return user


async def require_verified(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email address not verified")
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
""")

# ═════════════════════════════════════════════════════════════════════════════
# 6. models/user.py
# ═════════════════════════════════════════════════════════════════════════════
print("\n[6/24] models/user.py")
write(BACKEND / "models" / "user.py", """\
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_tokens: Mapped[list[UserToken]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class UserToken(Base):
    __tablename__ = "user_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="user_tokens")
""")

# ═════════════════════════════════════════════════════════════════════════════
# 7. schemas/user.py
# ═════════════════════════════════════════════════════════════════════════════
print("\n[7/24] schemas/user.py")
write(BACKEND / "schemas" / "user.py", """\
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_\\-]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    is_verified: bool
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
""")

# ═════════════════════════════════════════════════════════════════════════════
# 8. services/email.py
# ═════════════════════════════════════════════════════════════════════════════
print("\n[8/24] services/email.py")
write(BACKEND / "services" / "email.py", """\
\"\"\"
Transactional email for auth flows.
Set SMTP_HOST in .env to send real mail.
If SMTP_HOST is blank, tokens are logged to stdout (dev mode).
\"\"\"
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str, text: str) -> None:
    if not settings.smtp_host:
        logger.info("=== [DEV EMAIL] To: %s | Subject: %s ===", to, subject)
        logger.info(text)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, to, msg.as_string())

    logger.info("Email sent to %s: %s", to, subject)


async def send_verification_email(email: str, token: str) -> None:
    link = f"{settings.app_base_url}/verify-email?token={token}"
    html = f\"\"\"
    <h2>Welcome to Pumpr ⛽</h2>
    <p>Please verify your email address:</p>
    <p><a href="{link}">Verify email address</a></p>
    <p>This link expires in 24 hours.</p>
    \"\"\"
    text = f"Welcome to Pumpr!\\n\\nVerify your email:\\n{link}\\n\\nExpires in 24 hours."
    _send(email, "Verify your Pumpr email address", html, text)


async def send_password_reset_email(email: str, token: str) -> None:
    link = f"{settings.app_base_url}/reset-password?token={token}"
    html = f\"\"\"
    <h2>Pumpr password reset</h2>
    <p>Reset your password:</p>
    <p><a href="{link}">Reset password</a></p>
    <p>This link expires in 1 hour.</p>
    \"\"\"
    text = f"Pumpr password reset\\n\\nReset your password:\\n{link}\\n\\nExpires in 1 hour."
    _send(email, "Reset your Pumpr password", html, text)
""")

# ═════════════════════════════════════════════════════════════════════════════
# 9. api/endpoints/auth.py
# ═════════════════════════════════════════════════════════════════════════════
print("\n[9/24] api/endpoints/auth.py")
write(BACKEND / "api" / "endpoints" / "auth.py", """\
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
from app.db.session import get_db
from app.models.user import RefreshToken, User, UserToken
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
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
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/api/v1/auth/refresh",
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    from fastapi import Request
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
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/api/v1/auth/refresh",
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in)


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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, response: Response, db: AsyncSession = Depends(get_db)) -> None:
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored: RefreshToken | None = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
        await db.commit()
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")


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
""")

# ═════════════════════════════════════════════════════════════════════════════
# 10. Patch core/config.py — add SMTP + APP_BASE_URL fields
# ═════════════════════════════════════════════════════════════════════════════
print("\n[10/24] Patching core/config.py")
patch(
    BACKEND / "core" / "config.py",
    find='    bsky_app_password: str = ""\n\n    class Config:',
    replace='''\
    bsky_app_password: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@pumpr.co.uk"
    app_base_url: str = "https://pumpr.co.uk"

    class Config:''',
    description="add SMTP + app_base_url settings",
)

# ═════════════════════════════════════════════════════════════════════════════
# 11. Patch models/__init__.py — import new models so SQLAlchemy sees them
# ═════════════════════════════════════════════════════════════════════════════
print("\n[11/24] Patching models/__init__.py")
append_if_missing(
    BACKEND / "models" / "__init__.py",
    marker="from app.models.user import",
    content="from app.models.user import RefreshToken, User, UserToken  # noqa: F401\n",
    description="import auth models",
)

# ═════════════════════════════════════════════════════════════════════════════
# 12. Patch api/router.py — register auth router
# ═════════════════════════════════════════════════════════════════════════════
print("\n[12/24] Patching api/router.py")
patch(
    BACKEND / "api" / "router.py",
    find="from app.api.endpoints import ev, prices, stations, stats",
    replace="from app.api.endpoints import auth, ev, prices, stations, stats",
    description="import auth endpoint",
)
patch(
    BACKEND / "api" / "router.py",
    find="api_router.include_router(stations.router)",
    replace="api_router.include_router(auth.router)\napi_router.include_router(stations.router)",
    description="register auth router",
)

# ═════════════════════════════════════════════════════════════════════════════
# 13. Patch requirements.txt — add new deps
# ═════════════════════════════════════════════════════════════════════════════
print("\n[13/24] Patching requirements.txt")
append_if_missing(
    ROOT / "backend" / "requirements.txt",
    marker="python-jose",
    content="python-jose[cryptography]>=3.3.0\npasslib[bcrypt]>=1.7.4\nemail-validator>=2.0.0\n",
    description="auth dependencies",
)

# ═════════════════════════════════════════════════════════════════════════════
# 14. frontend/src/contexts/AuthContext.jsx
# ═════════════════════════════════════════════════════════════════════════════
print("\n[14/24] AuthContext.jsx")
write(FRONTEND / "contexts" / "AuthContext.jsx", """\
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'

const BASE = '/api/v1/auth'
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]               = useState(null)
  const [accessToken, setAccessToken] = useState(null)
  const [loading, setLoading]         = useState(true)
  const refreshTimer                  = useRef(null)

  const storeTokens = useCallback((token, expiresIn, userObj) => {
    setAccessToken(token)
    setUser(userObj)
    if (refreshTimer.current) clearTimeout(refreshTimer.current)
    const delay = Math.max((expiresIn - 60) * 1000, 10_000)
    refreshTimer.current = setTimeout(() => silentRefresh(), delay)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function clearAuth() {
    setAccessToken(null)
    setUser(null)
    if (refreshTimer.current) clearTimeout(refreshTimer.current)
  }

  const silentRefresh = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/refresh`, { method: 'POST', credentials: 'include' })
      if (!res.ok) { clearAuth(); return }
      const { access_token, expires_in } = await res.json()
      const meRes = await fetch(`${BASE}/me`, { headers: { Authorization: `Bearer ${access_token}` } })
      if (!meRes.ok) { clearAuth(); return }
      storeTokens(access_token, expires_in, await meRes.json())
    } catch {
      clearAuth()
    }
  }, [storeTokens])

  useEffect(() => {
    silentRefresh().finally(() => setLoading(false))
    return () => { if (refreshTimer.current) clearTimeout(refreshTimer.current) }
  }, [silentRefresh])

  async function login(email, password) {
    const res = await fetch(`${BASE}/login`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Login failed') }
    const { access_token, expires_in } = await res.json()
    const meRes = await fetch(`${BASE}/me`, { headers: { Authorization: `Bearer ${access_token}` } })
    storeTokens(access_token, expires_in, await meRes.json())
  }

  async function register(email, username, password) {
    const res = await fetch(`${BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Registration failed') }
    return res.json()
  }

  async function logout() {
    if (accessToken) {
      await fetch(`${BASE}/logout`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ refresh_token: '' }),
      }).catch(() => {})
    }
    clearAuth()
  }

  async function requestPasswordReset(email) {
    const res = await fetch(`${BASE}/password-reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    return res.json()
  }

  const authFetch = useCallback(async (url, options = {}) => {
    const headers = { ...(options.headers || {}), ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) }
    return fetch(url, { ...options, headers })
  }, [accessToken])

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, isAuthenticated: !!accessToken, login, register, logout, requestPasswordReset, authFetch }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
""")

# ═════════════════════════════════════════════════════════════════════════════
# 15. hooks/useAuth.js
# ═════════════════════════════════════════════════════════════════════════════
print("\n[15/24] hooks/useAuth.js")
write(FRONTEND / "hooks" / "useAuth.js", """\
export { useAuth } from '../contexts/AuthContext'
""")

# ═════════════════════════════════════════════════════════════════════════════
# 16. components/auth/AuthModal.css
# ═════════════════════════════════════════════════════════════════════════════
print("\n[16/24] components/auth/AuthModal.css")
write(FRONTEND / "components" / "auth" / "AuthModal.css", """\
.auth-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.65);
  backdrop-filter: blur(3px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 1rem;
}
.auth-modal {
  position: relative;
  background: var(--surface, #1a1a1a);
  border: 1px solid var(--border, #2d2d2d);
  border-radius: 12px; padding: 2rem;
  width: 100%; max-width: 420px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.5);
  animation: auth-slide-in 0.18s ease-out;
}
@keyframes auth-slide-in {
  from { opacity: 0; transform: translateY(-12px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.auth-close {
  position: absolute; top: 1rem; right: 1rem;
  background: none; border: none; color: #888;
  font-size: 1.1rem; cursor: pointer;
  padding: 0.25rem 0.5rem; border-radius: 4px;
  transition: color 0.15s, background 0.15s;
}
.auth-close:hover { color: #fff; background: rgba(255,255,255,0.08); }
.auth-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.5rem; }
.auth-logo { font-size: 1.6rem; line-height: 1; }
.auth-header h2 { margin: 0; font-size: 1.25rem; font-weight: 600; color: var(--text, #e8e8e8); }
.auth-form { display: flex; flex-direction: column; gap: 0.4rem; }
.auth-form label { font-size: 0.8rem; font-weight: 500; color: #a0a0a8; margin-top: 0.5rem; }
.auth-form input {
  background: var(--bg, #111); border: 1px solid var(--border, #2d2d2d);
  border-radius: 6px; color: var(--text, #e8e8e8);
  font-size: 0.95rem; padding: 0.6rem 0.75rem; width: 100%; box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.auth-form input::placeholder { color: #4a4a4a; }
.auth-form input:focus { outline: none; border-color: var(--amber, #f59e0b); box-shadow: 0 0 0 3px rgba(245,158,11,0.2); }
.auth-hint { font-size: 0.72rem; color: #5a5a5a; margin-top: 0.1rem; }
.auth-btn-primary {
  margin-top: 1rem; background: var(--amber, #f59e0b); border: none;
  border-radius: 6px; color: #000; cursor: pointer;
  font-size: 0.95rem; font-weight: 700; padding: 0.7rem 1rem;
  transition: opacity 0.15s; width: 100%;
}
.auth-btn-primary:hover:not(:disabled) { opacity: 0.88; }
.auth-btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
.auth-btn-secondary {
  margin-top: 0.5rem; background: transparent;
  border: 1px solid var(--border, #2d2d2d); border-radius: 6px;
  color: #a0a0a8; cursor: pointer; font-size: 0.88rem;
  padding: 0.55rem 1rem; transition: border-color 0.15s, color 0.15s; width: 100%;
}
.auth-btn-secondary:hover { border-color: var(--amber, #f59e0b); color: var(--text, #e8e8e8); }
.auth-error {
  background: rgba(220,50,50,0.12); border: 1px solid rgba(220,50,50,0.35);
  border-radius: 6px; color: #f08080; font-size: 0.85rem;
  margin: 0.25rem 0 0.5rem; padding: 0.55rem 0.75rem;
}
.auth-success { color: #6dbf7e; font-size: 0.88rem; margin: 0.5rem 0; }
.auth-success-block { text-align: center; padding: 0.5rem 0 0.25rem; }
.auth-switch { font-size: 0.83rem; color: #6a6a6a; margin-top: 1.1rem; text-align: center; }
.auth-link {
  background: none; border: none; color: var(--amber, #f59e0b);
  cursor: pointer; font-size: inherit; padding: 0;
  text-decoration: underline; text-underline-offset: 2px;
}
.auth-link:hover { opacity: 0.8; }
.auth-reset-inline { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border, #2d2d2d); }

/* UserMenu */
.user-menu { position: relative; display: inline-flex; }
.user-menu-trigger {
  align-items: center; background: rgba(245,158,11,0.1);
  border: 1px solid rgba(245,158,11,0.3); border-radius: 20px;
  color: var(--text, #e8e8e8); cursor: pointer; display: flex;
  font-size: 0.85rem; font-weight: 500; gap: 0.4rem;
  padding: 0.35rem 0.75rem 0.35rem 0.5rem; transition: background 0.15s;
}
.user-menu-trigger:hover { background: rgba(245,158,11,0.18); }
.user-menu-trigger .avatar {
  align-items: center; background: var(--amber, #f59e0b);
  border-radius: 50%; color: #000; display: flex;
  font-size: 0.75rem; font-weight: 700;
  height: 22px; justify-content: center; width: 22px;
}
.user-menu-dropdown {
  background: var(--surface, #1a1a1a); border: 1px solid var(--border, #2d2d2d);
  border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,0.45);
  min-width: 180px; padding: 0.4rem 0;
  position: absolute; right: 0; top: calc(100% + 6px); z-index: 500;
}
.user-menu-info { padding: 0.5rem 0.85rem 0.4rem; border-bottom: 1px solid var(--border, #2d2d2d); margin-bottom: 0.3rem; }
.user-menu-info .um-username { font-size: 0.88rem; font-weight: 600; color: var(--text, #e8e8e8); }
.user-menu-info .um-email { font-size: 0.75rem; color: #5a5a5a; margin-top: 0.1rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }
.user-menu-info .um-badge {
  display: inline-block; background: rgba(245,158,11,0.15);
  border: 1px solid rgba(245,158,11,0.35); border-radius: 3px;
  color: var(--amber, #f59e0b); font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.05em; margin-top: 0.3rem; padding: 0.1rem 0.35rem; text-transform: uppercase;
}
.user-menu-item {
  background: none; border: none; color: #a0a0a8; cursor: pointer;
  display: block; font-size: 0.87rem; padding: 0.45rem 0.85rem;
  text-align: left; transition: background 0.12s, color 0.12s; width: 100%;
}
.user-menu-item:hover { background: rgba(255,255,255,0.05); color: var(--text, #e8e8e8); }
.user-menu-item.danger { color: #c07070; }
.user-menu-item.danger:hover { background: rgba(220,50,50,0.1); color: #f08080; }
.nav-auth-buttons { display: flex; align-items: center; gap: 0.5rem; }
.nav-btn-ghost {
  background: none; border: 1px solid var(--border, #2d2d2d); border-radius: 6px;
  color: #a0a0a8; cursor: pointer; font-size: 0.85rem; padding: 0.35rem 0.75rem;
  transition: border-color 0.15s, color 0.15s;
}
.nav-btn-ghost:hover { border-color: var(--amber, #f59e0b); color: var(--text, #e8e8e8); }
.nav-btn-filled {
  background: var(--amber, #f59e0b); border: none; border-radius: 6px;
  color: #000; cursor: pointer; font-size: 0.85rem; font-weight: 700;
  padding: 0.35rem 0.85rem; transition: opacity 0.15s;
}
.nav-btn-filled:hover { opacity: 0.88; }
""")

# ═════════════════════════════════════════════════════════════════════════════
# 17. LoginModal.jsx
# ═════════════════════════════════════════════════════════════════════════════
print("\n[17/24] LoginModal.jsx")
write(FRONTEND / "components" / "auth" / "LoginModal.jsx", """\
import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import './AuthModal.css'

export default function LoginModal({ onClose, onSwitchToRegister }) {
  const { login, requestPasswordReset } = useAuth()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [showReset, setShowReset] = useState(false)
  const [resetEmail, setResetEmail] = useState('')
  const [resetSent, setResetSent]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try { await login(email, password); onClose() }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function handleReset(e) {
    e.preventDefault()
    await requestPasswordReset(resetEmail)
    setResetSent(true)
  }

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="auth-close" onClick={onClose}>✕</button>
        <div className="auth-header"><span className="auth-logo">⛽</span><h2>Sign in to Pumpr</h2></div>
        <form onSubmit={handleSubmit} className="auth-form">
          {error && <p className="auth-error">{error}</p>}
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" />
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required autoComplete="current-password" />
          <button type="submit" className="auth-btn-primary" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <button className="auth-link" style={{marginTop:'0.75rem',display:'block',textAlign:'center'}} onClick={() => setShowReset(v => !v)}>Forgot your password?</button>
        {showReset && !resetSent && (
          <form onSubmit={handleReset} className="auth-form auth-reset-inline">
            <label>Enter your email to reset</label>
            <input type="email" value={resetEmail} onChange={e => setResetEmail(e.target.value)} placeholder="you@example.com" required />
            <button type="submit" className="auth-btn-secondary">Send reset link</button>
          </form>
        )}
        {resetSent && <p className="auth-success" style={{textAlign:'center'}}>Reset link sent — check your inbox.</p>}
        <p className="auth-switch">Don't have an account? <button className="auth-link" onClick={onSwitchToRegister}>Create one</button></p>
      </div>
    </div>
  )
}
""")

# ═════════════════════════════════════════════════════════════════════════════
# 18. RegisterModal.jsx
# ═════════════════════════════════════════════════════════════════════════════
print("\n[18/24] RegisterModal.jsx")
write(FRONTEND / "components" / "auth" / "RegisterModal.jsx", """\
import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import './AuthModal.css'

export default function RegisterModal({ onClose, onSwitchToLogin }) {
  const { register } = useAuth()
  const [email, setEmail]       = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault(); setError('')
    if (password !== confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    try { const r = await register(email, username, password); setSuccess(r.message || 'Account created! Check your email.') }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="auth-close" onClick={onClose}>✕</button>
        <div className="auth-header"><span className="auth-logo">⛽</span><h2>Create your account</h2></div>
        {success ? (
          <div className="auth-success-block">
            <p className="auth-success">{success}</p>
            <p className="auth-switch"><button className="auth-link" onClick={onSwitchToLogin}>Back to sign in</button></p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {error && <p className="auth-error">{error}</p>}
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" />
            <label>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="pumpr_user" pattern="[a-zA-Z0-9_\\-]+" minLength={3} maxLength={30} required autoComplete="username" />
            <small className="auth-hint">Letters, numbers, _ and - only</small>
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" minLength={8} required autoComplete="new-password" />
            <small className="auth-hint">Min 8 chars, one uppercase, one number</small>
            <label>Confirm password</label>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="••••••••" required autoComplete="new-password" />
            <button type="submit" className="auth-btn-primary" disabled={loading}>{loading ? 'Creating account…' : 'Create account'}</button>
          </form>
        )}
        {!success && <p className="auth-switch">Already have an account? <button className="auth-link" onClick={onSwitchToLogin}>Sign in</button></p>}
      </div>
    </div>
  )
}
""")

# ═════════════════════════════════════════════════════════════════════════════
# 19. UserMenu.jsx
# ═════════════════════════════════════════════════════════════════════════════
print("\n[19/24] UserMenu.jsx")
write(FRONTEND / "components" / "auth" / "UserMenu.jsx", """\
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import LoginModal from './LoginModal'
import RegisterModal from './RegisterModal'
import './AuthModal.css'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen]  = useState(false)
  const ref              = useRef(null)

  useEffect(() => {
    function handler(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (!user) return null
  const initial = (user.username?.[0] ?? user.email[0]).toUpperCase()

  return (
    <div className="user-menu" ref={ref}>
      <button className="user-menu-trigger" onClick={() => setOpen(o => !o)}>
        <span className="avatar">{initial}</span>{user.username}
      </button>
      {open && (
        <div className="user-menu-dropdown">
          <div className="user-menu-info">
            <div className="um-username">{user.username}</div>
            <div className="um-email">{user.email}</div>
            <span className="um-badge">{user.role}</span>
          </div>
          <button className="user-menu-item" onClick={() => setOpen(false)}>★ Favourite stations</button>
          <button className="user-menu-item" onClick={() => setOpen(false)}>🔔 Price alerts</button>
          <button className="user-menu-item danger" onClick={() => { setOpen(false); logout() }}>Sign out</button>
        </div>
      )}
    </div>
  )
}

export default function NavAuthSection() {
  const { isAuthenticated, loading } = useAuth()
  const [modal, setModal] = useState(null)

  if (loading) return <div style={{ width: 120 }} />
  if (isAuthenticated) return <UserMenu />

  return (
    <>
      <div className="nav-auth-buttons">
        <button className="nav-btn-ghost"  onClick={() => setModal('login')}>Sign in</button>
        <button className="nav-btn-filled" onClick={() => setModal('register')}>Join free</button>
      </div>
      {modal === 'login'    && <LoginModal    onClose={() => setModal(null)} onSwitchToRegister={() => setModal('register')} />}
      {modal === 'register' && <RegisterModal onClose={() => setModal(null)} onSwitchToLogin={() => setModal('login')} />}
    </>
  )
}
""")

# ═════════════════════════════════════════════════════════════════════════════
# 20. VerifyEmailPage.jsx
# ═════════════════════════════════════════════════════════════════════════════
print("\n[20/24] VerifyEmailPage.jsx")
write(FRONTEND / "components" / "auth" / "VerifyEmailPage.jsx", """\
import { useEffect, useState } from 'react'

export default function VerifyEmailPage() {
  const [status, setStatus]   = useState('verifying')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token')
    if (!token) { setStatus('error'); setMessage('No verification token found.'); return }
    fetch(`/api/v1/auth/verify/${token}`)
      .then(r => r.json())
      .then(d => { if (d.message) { setStatus('success'); setMessage(d.message) } else { setStatus('error'); setMessage(d.detail || 'Verification failed.') } })
      .catch(() => { setStatus('error'); setMessage('An error occurred. Please try again.') })
  }, [])

  const card = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, maxWidth: 420, padding: '2.5rem 2rem', textAlign: 'center', width: '100%' }
  return (
    <div style={{ alignItems: 'center', background: 'var(--bg)', display: 'flex', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
      <div style={card}>
        <div style={{ fontSize: '2.5rem' }}>⛽</div>
        {status === 'verifying' && <><h2 style={{ color: 'var(--text)' }}>Verifying your email…</h2><p style={{ color: '#888' }}>Just a moment.</p></>}
        {status === 'success'   && <><h2 style={{ color: '#6dbf7e' }}>Email verified ✓</h2><p style={{ color: '#888' }}>{message}</p><a href="/" style={{ color: 'var(--amber)' }}>Go to Pumpr →</a></>}
        {status === 'error'     && <><h2 style={{ color: '#f08080' }}>Verification failed</h2><p style={{ color: '#888' }}>{message}</p><a href="/" style={{ color: 'var(--amber)' }}>Back to Pumpr</a></>}
      </div>
    </div>
  )
}
""")

# ═════════════════════════════════════════════════════════════════════════════
# 21. ResetPasswordPage.jsx
# ═════════════════════════════════════════════════════════════════════════════
print("\n[21/24] ResetPasswordPage.jsx")
write(FRONTEND / "components" / "auth" / "ResetPasswordPage.jsx", """\
import { useState } from 'react'
import './AuthModal.css'

export default function ResetPasswordPage() {
  const token = new URLSearchParams(window.location.search).get('token') ?? ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault(); setError('')
    if (password !== confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/v1/auth/password-reset/confirm', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Reset failed')
      setSuccess(data.message)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div style={{ alignItems: 'center', background: 'var(--bg)', display: 'flex', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
      <div className="auth-modal" style={{ position: 'static', maxWidth: 420, width: '100%' }}>
        <div className="auth-header"><span className="auth-logo">⛽</span><h2>Reset your password</h2></div>
        {success ? (
          <div className="auth-success-block"><p className="auth-success">{success}</p><a href="/" style={{ color: 'var(--amber)' }}>Sign in →</a></div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {error && <p className="auth-error">{error}</p>}
            {!token && <p className="auth-error">Invalid reset link — please request a new one.</p>}
            <label>New password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" minLength={8} required autoComplete="new-password" />
            <small className="auth-hint">Min 8 chars, one uppercase, one number</small>
            <label>Confirm password</label>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="••••••••" required autoComplete="new-password" />
            <button type="submit" className="auth-btn-primary" disabled={loading || !token}>{loading ? 'Updating…' : 'Set new password'}</button>
          </form>
        )}
      </div>
    </div>
  )
}
""")

# ═════════════════════════════════════════════════════════════════════════════
# 22. Patch main.jsx — wrap in AuthProvider
# ═════════════════════════════════════════════════════════════════════════════
print("\n[22/24] Patching main.jsx")
patch(
    FRONTEND / "main.jsx",
    find="import './index.css'",
    replace="import './index.css'\nimport { AuthProvider } from './contexts/AuthContext'",
    description="import AuthProvider",
)
patch(
    FRONTEND / "main.jsx",
    find="    <BrowserRouter>\n      <App />\n    </BrowserRouter>",
    replace="    <BrowserRouter>\n      <AuthProvider>\n        <App />\n      </AuthProvider>\n    </BrowserRouter>",
    description="wrap App in AuthProvider",
)

# ═════════════════════════════════════════════════════════════════════════════
# 23. Patch App.jsx — add verify/reset routes
# ═════════════════════════════════════════════════════════════════════════════
print("\n[23/24] Patching App.jsx")
patch(
    FRONTEND / "App.jsx",
    find="import Privacy from './pages/Privacy'",
    replace="import Privacy from './pages/Privacy'\nimport VerifyEmailPage from './components/auth/VerifyEmailPage'\nimport ResetPasswordPage from './components/auth/ResetPasswordPage'",
    description="import auth pages",
)
patch(
    FRONTEND / "App.jsx",
    find="          <Route path=\"/privacy\" element={<Privacy />} />",
    replace="          <Route path=\"/privacy\" element={<Privacy />} />\n          <Route path=\"/verify-email\" element={<VerifyEmailPage />} />\n          <Route path=\"/reset-password\" element={<ResetPasswordPage />} />",
    description="add auth routes",
)

# ═════════════════════════════════════════════════════════════════════════════
# 24. Patch Navbar.jsx — add NavAuthSection
# ═════════════════════════════════════════════════════════════════════════════
print("\n[24/24] Patching Navbar.jsx")
patch(
    FRONTEND / "components" / "Navbar.jsx",
    find="import './Navbar.css'",
    replace="import NavAuthSection from './auth/UserMenu'\nimport './Navbar.css'",
    description="import NavAuthSection",
)
patch(
    FRONTEND / "components" / "Navbar.jsx",
    find='      <div className="navbar-tag">Live UK fuel prices</div>',
    replace='      <NavAuthSection />\n      <div className="navbar-tag">Live UK fuel prices</div>',
    description="add NavAuthSection to navbar",
)

# ═════════════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
if errors:
    print("COMPLETED WITH ERRORS:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("ALL 24 STEPS COMPLETED SUCCESSFULLY")
    print("""
Next steps:
  1. Run the DB migration:
       docker exec -i pumpr_db psql -U pumpr pumpr < postgres/002_add_users.sql

  2. Rebuild the API container:
       docker compose build api

  3. Restart everything:
       docker compose up -d

  4. Test via Swagger:
       http://localhost:8002/docs  →  POST /api/v1/auth/register

  5. Grab verification token from logs (SMTP_HOST is blank = dev mode):
       docker logs pumpr_api 2>&1 | grep -A2 "DEV EMAIL"

  6. Rebuild frontend:
       docker compose build frontend && docker compose up -d frontend
""")
