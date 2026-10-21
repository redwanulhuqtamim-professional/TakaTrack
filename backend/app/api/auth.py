import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import (
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    hash_password,
    set_auth_cookie,
    verify_password,
)
from app.db.session import get_db
from app.models.all_models import MonthlyBudget, User, UserSettings
from app.schemas.auth import (
    LoginRequest,
    OnboardingRequest,
    PasswordChangeRequest,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_ATTEMPTS = 10
WINDOW_SECONDS = 60.0


def _check_rate_limit(client_ip: str) -> None:
    now = time.time()
    _login_attempts[client_ip] = [t for t in _login_attempts[client_ip] if now - t < WINDOW_SECONDS]
    if len(_login_attempts[client_ip]) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a minute and try again.",
        )
    _login_attempts[client_ip].append(now)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        is_onboarded=False,
    )
    db.add(user)
    db.flush()

    user_settings = UserSettings(
        user_id=user.id,
        currency="BDT",
        timezone="Asia/Dhaka",
        notification_preferences={"budget_alerts": True, "bill_reminders": True},
    )
    db.add(user_settings)
    db.commit()

    user = db.scalar(select(User).options(joinedload(User.settings)).where(User.id == user.id))
    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return user


@router.post("/login", response_model=UserResponse)
def login_user(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "local"
    _check_rate_limit(client_ip)

    normalized_email = payload.email.lower().strip()
    user = db.scalar(
        select(User).options(joinedload(User.settings)).where(User.email == normalized_email)
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return user


@router.post("/logout")
def logout_user(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully."}


@router.post("/onboarding", response_model=UserResponse)
def complete_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name:
        current_user.full_name = payload.full_name.strip()

    now_dhaka = datetime.now(ZoneInfo(settings.TIMEZONE))
    year, month = now_dhaka.year, now_dhaka.month

    if payload.initial_monthly_budget is not None:
        existing_month = db.scalar(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == current_user.id,
                MonthlyBudget.year == year,
                MonthlyBudget.month == month,
            )
        )
        if not existing_month:
            db.add(
                MonthlyBudget(
                    user_id=current_user.id,
                    year=year,
                    month=month,
                    budget_amount=payload.initial_monthly_budget,
                    opening_cash=payload.opening_cash or Decimal("0.00"),
                    notes="Created during initial onboarding",
                )
            )

    current_user.is_onboarded = True
    db.commit()
    db.refresh(current_user)
    return current_user
