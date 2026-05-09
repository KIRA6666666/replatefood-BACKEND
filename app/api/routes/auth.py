import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select

from app.api.deps import DbSession
from app.core.config import settings
from app.core.email import send_reset_email, send_verification_email
from app.core.security import create_access_token, create_reset_token, verify_reset_token
from app.crud import user as user_crud
from app.models.account_verification_otp import AccountVerificationOTP
from app.models.password_reset_otp import PasswordResetOTP
from app.models.user import UserRole
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead


class VerifyEmailOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


STUDENT_EMAIL_DOMAIN = "@uca.ac.ma"

router = APIRouter(prefix="/auth", tags=["auth"])


async def _create_and_send_verification_otp(db: DbSession, user) -> str:
    await db.execute(delete(AccountVerificationOTP).where(AccountVerificationOTP.user_id == user.id))
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = AccountVerificationOTP(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(otp)
    await db.commit()
    return code


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession) -> UserRead:
    if payload.role == UserRole.student and not payload.email.lower().endswith(STUDENT_EMAIL_DOMAIN):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student accounts require a {STUDENT_EMAIL_DOMAIN} email address",
        )
    if payload.role != UserRole.student and payload.email.lower().endswith(STUDENT_EMAIL_DOMAIN):
        payload = payload.model_copy(update={"role": UserRole.student})
    if await user_crud.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    if await user_crud.get_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    user = await user_crud.create(db, payload)
    code = await _create_and_send_verification_otp(db, user)
    if settings.SMTP_HOST:
        try:
            await send_verification_email(user.email, code)
        except Exception:
            pass
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await user_crud.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="email_not_verified",
        )
    return Token(access_token=create_access_token(subject=str(user.id)))


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> dict:
    user = await user_crud.get_by_email(db, payload.email)
    if user is None:
        return {"message": "ok"}

    # Delete any existing OTPs for this user and create a fresh one.
    await db.execute(delete(PasswordResetOTP).where(PasswordResetOTP.user_id == user.id))
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = PasswordResetOTP(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(otp)
    await db.commit()

    if settings.SMTP_HOST:
        try:
            await send_reset_email(user.email, code)
        except Exception:
            pass
        return {"message": "ok"}

    # SMTP not configured — return code directly (development only).
    return {"message": "ok", "debug_code": code}


@router.post("/verify-reset-otp")
async def verify_reset_otp(payload: VerifyOtpRequest, db: DbSession) -> dict:
    user = await user_crud.get_by_email(db, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_code")

    result = await db.execute(
        select(PasswordResetOTP).where(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.code == payload.code,
            PasswordResetOTP.used.is_(False),
            PasswordResetOTP.expires_at > datetime.now(timezone.utc),
        )
    )
    otp = result.scalar_one_or_none()
    if otp is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_code")

    otp.used = True
    await db.commit()

    reset_token = create_reset_token(str(user.id))
    return {"reset_token": reset_token}


@router.post("/verify-otp")
async def verify_email_otp(payload: VerifyEmailOtpRequest, db: DbSession) -> dict:
    user = await user_crud.get_by_email(db, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_otp")
    result = await db.execute(
        select(AccountVerificationOTP).where(
            AccountVerificationOTP.user_id == user.id,
            AccountVerificationOTP.code == payload.code,
            AccountVerificationOTP.used.is_(False),
            AccountVerificationOTP.expires_at > datetime.now(timezone.utc),
        )
    )
    otp = result.scalar_one_or_none()
    if otp is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_otp")
    otp.used = True
    user.is_verified = True
    await db.commit()
    return {"message": "email_verified"}


@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, db: DbSession) -> dict:
    user = await user_crud.get_by_email(db, payload.email)
    if user is None or user.is_verified:
        return {"message": "ok"}
    code = await _create_and_send_verification_otp(db, user)
    if settings.SMTP_HOST:
        try:
            await send_verification_email(user.email, code)
        except Exception:
            pass
        return {"message": "ok"}
    return {"message": "ok", "debug_code": code}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: DbSession) -> dict:
    try:
        user_id = verify_reset_token(payload.token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_or_expired_token",
        )
    user = await user_crud.get_by_id(db, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_crud.change_password(db, user, payload.new_password)
    return {"message": "password_updated"}
