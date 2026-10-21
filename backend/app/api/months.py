from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.all_models import Expense, FixedBill, Income, MonthlyBudget, User
from app.schemas.finance import (
    MonthCreateRequest,
    MonthSummaryResponse,
    MonthUpdateRequest,
)
from app.services.finance import compute_monthly_summary

router = APIRouter(prefix="/api/months", tags=["Monthly Budgets"])


def _prev_year_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _next_year_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


@router.post("", response_model=MonthSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_month(
    payload: MonthCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == current_user.id,
            MonthlyBudget.year == payload.year,
            MonthlyBudget.month == payload.month,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Financial month {payload.year}-{payload.month:02d} already exists.",
        )

    opening_cash = payload.opening_cash
    if payload.carry_forward_previous_cash:
        prev_y, prev_m = _prev_year_month(payload.year, payload.month)
        prev_mb = db.scalar(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == current_user.id,
                MonthlyBudget.year == prev_y,
                MonthlyBudget.month == prev_m,
            )
        )
        if prev_mb:
            prev_summary = compute_monthly_summary(db, current_user.id, prev_mb)
            opening_cash = prev_summary["available_cash"]

    mb = MonthlyBudget(
        user_id=current_user.id,
        year=payload.year,
        month=payload.month,
        budget_amount=payload.budget_amount,
        opening_cash=opening_cash,
        notes=payload.notes,
    )
    db.add(mb)
    db.commit()
    db.refresh(mb)
    return compute_monthly_summary(db, current_user.id, mb)


@router.get("", response_model=List[MonthSummaryResponse])
def list_months(
    year: Optional[int] = Query(None),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(MonthlyBudget).where(MonthlyBudget.user_id == current_user.id)
    if year is not None:
        stmt = stmt.where(MonthlyBudget.year == year)
    if not include_archived:
        stmt = stmt.where(MonthlyBudget.is_archived.is_(False))
    stmt = stmt.order_by(MonthlyBudget.year.desc(), MonthlyBudget.month.desc())

    months = db.scalars(stmt).all()
    return [compute_monthly_summary(db, current_user.id, m) for m in months]


@router.get("/by-period/{year}/{month}", response_model=MonthSummaryResponse)
def get_month_by_period(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == current_user.id,
            MonthlyBudget.year == year,
            MonthlyBudget.month == month,
        )
    )
    if not mb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Month {year}-{month:02d} has not been set up yet.",
        )
    return compute_monthly_summary(db, current_user.id, mb)


@router.patch("/{month_id}", response_model=MonthSummaryResponse)
def update_month(
    month_id: int,
    payload: MonthUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.id == month_id,
            MonthlyBudget.user_id == current_user.id,
        )
    )
    if not mb:
        raise HTTPException(status_code=404, detail="Monthly budget not found.")

    if payload.budget_amount is not None:
        mb.budget_amount = payload.budget_amount
    if payload.opening_cash is not None:
        mb.opening_cash = payload.opening_cash
    if payload.notes is not None:
        mb.notes = payload.notes
    if payload.is_archived is not None:
        mb.is_archived = payload.is_archived

    db.commit()
    db.refresh(mb)
    summary = compute_monthly_summary(db, current_user.id, mb)

    next_y, next_m = _next_year_month(mb.year, mb.month)
    next_mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == current_user.id,
            MonthlyBudget.year == next_y,
            MonthlyBudget.month == next_m,
        )
    )
    if next_mb:
        summary["reconciliation_warning"] = (
            f"Note: {next_y}-{next_m:02d} already exists. Its opening cash may need reconciliation."
        )
    return summary


@router.delete("/{month_id}")
def delete_month(
    month_id: int,
    confirm: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.id == month_id,
            MonthlyBudget.user_id == current_user.id,
        )
    )
    if not mb:
        raise HTTPException(status_code=404, detail="Monthly budget not found.")

    has_records = (
        db.scalar(select(Expense.id).where(Expense.monthly_budget_id == mb.id).limit(1))
        or db.scalar(select(FixedBill.id).where(FixedBill.monthly_budget_id == mb.id).limit(1))
        or db.scalar(select(Income.id).where(Income.monthly_budget_id == mb.id).limit(1))
    )
    if has_records and not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This month contains financial records. Pass confirm=true to delete or archive it instead.",
        )

    db.delete(mb)
    db.commit()
    return {"message": "Month deleted successfully."}
