import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.all_models import (
    Expense,
    FinancialTransaction,
    MonthlyBudget,
    User,
    UserSettings,
)
from app.schemas.auth import UserResponse
from app.schemas.obligations import ProfileUpdateRequest
from app.services.finance import compute_monthly_summary, get_month_date_range

router = APIRouter(prefix="/api", tags=["Reports, Dashboard & Profile"])
ZERO = Decimal("0.00")


@router.get("/reports/monthly-details/{year}/{month}")
def get_monthly_report_details(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == current_user.id,
            MonthlyBudget.year == year,
            MonthlyBudget.month == month,
        )
    )
    if not mb:
        raise HTTPException(status_code=404, detail="Month not found.")

    summary = compute_monthly_summary(db, current_user.id, mb)
    start_date, end_date, days_in_month = get_month_date_range(year, month)

    # Daily spending trend for every day of the Gregorian month
    daily_rows = db.execute(
        select(Expense.expense_date, func.coalesce(func.sum(Expense.amount), ZERO))
        .where(
            Expense.user_id == current_user.id,
            Expense.monthly_budget_id == mb.id,
        )
        .group_by(Expense.expense_date)
        .order_by(Expense.expense_date.asc())
    ).all()
    by_date = {d: amt for d, amt in daily_rows}

    daily_trend = [
        {
            "day": day_num,
            "date": date(year, month, day_num).isoformat(),
            "amount": str(by_date.get(date(year, month, day_num), ZERO)),
        }
        for day_num in range(1, days_in_month + 1)
    ]

    # Recent transactions across ledger within this month
    recent_ledger = db.scalars(
        select(FinancialTransaction)
        .where(
            FinancialTransaction.user_id == current_user.id,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date,
        )
        .order_by(FinancialTransaction.transaction_date.desc(), FinancialTransaction.id.desc())
        .limit(15)
    ).all()

    return {
        "summary": summary,
        "daily_trend": daily_trend,
        "recent_transactions": [
            {
                "id": t.id,
                "date": t.transaction_date.isoformat(),
                "description": t.description,
                "transaction_type": t.transaction_type,
                "amount": str(t.amount),
            }
            for t in recent_ledger
        ],
    }


@router.get("/reports/export-csv")
def export_transactions_csv(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.user_id == current_user.id)
    )
    if year and month:
        start_d, end_d, _ = get_month_date_range(year, month)
        stmt = stmt.where(Expense.expense_date >= start_d, Expense.expense_date <= end_d)

    expenses = db.scalars(stmt.order_by(Expense.expense_date.desc(), Expense.id.desc())).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "Category", "Description", "Amount (BDT)", "Notes"])
    for e in expenses:
        writer.writerow([
            e.expense_date.isoformat(),
            e.expense_time.strftime("%H:%M") if e.expense_time else "",
            e.category.name if e.category else "Other",
            e.description,
            f"{e.amount:.2f}",
            e.notes or "",
        ])

    output.seek(0)
    filename = f"takatrack_expenses_{year or 'all'}_{month or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/profile", response_model=UserResponse)
def update_profile_and_settings(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()

    if not current_user.settings:
        current_user.settings = UserSettings(user_id=current_user.id, currency="BDT", timezone="Asia/Dhaka")

    if payload.preferred_dashboard_month is not None:
        current_user.settings.preferred_dashboard_month = payload.preferred_dashboard_month
    if payload.daily_spending_target is not None:
        current_user.settings.daily_spending_target = payload.daily_spending_target

    db.commit()
    db.refresh(current_user)
    return current_user
