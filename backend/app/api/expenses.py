from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.all_models import (
    BillStatus,
    Expense,
    ExpenseCategory,
    FinancialTransaction,
    FixedBill,
    Income,
    MonthlyBudget,
    TransactionType,
    User,
)
from app.schemas.finance import (
    CategoryCreateRequest,
    CategoryResponse,
    DailyExpenseSummaryResponse,
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)

router = APIRouter(prefix="/api", tags=["Categories & Daily Expenses"])
ZERO = Decimal("0.00")


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(ExpenseCategory)
        .where(
            or_(
                ExpenseCategory.is_default.is_(True),
                ExpenseCategory.user_id == current_user.id,
            )
        )
        .order_by(ExpenseCategory.is_default.desc(), ExpenseCategory.name.asc())
    )
    return db.scalars(stmt).all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clean_name = payload.name.strip()
    existing = db.scalar(
        select(ExpenseCategory).where(
            or_(
                ExpenseCategory.is_default.is_(True),
                ExpenseCategory.user_id == current_user.id,
            ),
            func.lower(ExpenseCategory.name) == clean_name.lower(),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Category with this name already exists.")

    cat = ExpenseCategory(
        user_id=current_user.id,
        name=clean_name,
        category_type="EXPENSE",
        is_default=False,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _to_expense_response(exp: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=exp.id,
        monthly_budget_id=exp.monthly_budget_id,
        category_id=exp.category_id,
        category_name=exp.category.name if exp.category else "Uncategorized",
        amount=exp.amount,
        description=exp.description,
        expense_date=exp.expense_date,
        expense_time=exp.expense_time,
        notes=exp.notes,
        created_at=exp.created_at,
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == current_user.id,
            MonthlyBudget.year == payload.expense_date.year,
            MonthlyBudget.month == payload.expense_date.month,
        )
    )
    if not mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Month {payload.expense_date.year}-{payload.expense_date.month:02d} has not been created yet. Please set up the month first.",
        )

    cat = db.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.id == payload.category_id,
            or_(
                ExpenseCategory.is_default.is_(True),
                ExpenseCategory.user_id == current_user.id,
            ),
        )
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Valid expense category not found.")

    ledger = FinancialTransaction(
        user_id=current_user.id,
        monthly_budget_id=mb.id,
        transaction_type=TransactionType.ORDINARY_EXPENSE.value,
        amount=payload.amount,
        transaction_date=payload.expense_date,
        description=payload.description.strip(),
    )
    db.add(ledger)
    db.flush()

    exp = Expense(
        user_id=current_user.id,
        monthly_budget_id=mb.id,
        category_id=cat.id,
        linked_transaction_id=ledger.id,
        amount=payload.amount,
        description=payload.description.strip(),
        expense_date=payload.expense_date,
        expense_time=payload.expense_time,
        notes=payload.notes,
    )
    db.add(exp)
    db.commit()

    exp = db.scalar(
        select(Expense).options(joinedload(Expense.category)).where(Expense.id == exp.id)
    )
    return _to_expense_response(exp)


@router.get("/expenses/daily/{target_date}", response_model=DailyExpenseSummaryResponse)
def get_daily_expenses(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == current_user.id,
            MonthlyBudget.year == target_date.year,
            MonthlyBudget.month == target_date.month,
        )
    )
    daily_target = current_user.settings.daily_spending_target if current_user.settings else None

    if not mb:
        return DailyExpenseSummaryResponse(
            selected_date=target_date,
            day_of_week=target_date.strftime("%A"),
            year=target_date.year,
            month=target_date.month,
            month_exists=False,
            monthly_budget_id=None,
            daily_total=ZERO,
            food_expenses=ZERO,
            transportation_expenses=ZERO,
            education_expenses=ZERO,
            other_expenses=ZERO,
            transaction_count=0,
            remaining_monthly_budget_as_of_date=ZERO,
            available_cash_as_of_date=ZERO,
            daily_spending_target=daily_target,
            remaining_daily_allowance=daily_target,
            expenses=[],
        )

    day_expenses = db.scalars(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(
            Expense.user_id == current_user.id,
            Expense.monthly_budget_id == mb.id,
            Expense.expense_date == target_date,
        )
        .order_by(Expense.expense_time.asc().nulls_last(), Expense.id.asc())
    ).all()

    daily_total = sum((e.amount for e in day_expenses), ZERO)
    food = sum((e.amount for e in day_expenses if e.category and "food" in e.category.name.lower()), ZERO)
    transport = sum((e.amount for e in day_expenses if e.category and "transport" in e.category.name.lower()), ZERO)
    education = sum((e.amount for e in day_expenses if e.category and "education" in e.category.name.lower()), ZERO)
    other = daily_total - (food + transport + education)

    # Historical calculation strictly up to and including target_date
    cum_daily_exp = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), ZERO)).where(
            Expense.user_id == current_user.id,
            Expense.monthly_budget_id == mb.id,
            Expense.expense_date <= target_date,
        )
    ) or ZERO

    cum_paid_bills = db.scalar(
        select(func.coalesce(func.sum(FixedBill.amount), ZERO)).where(
            FixedBill.user_id == current_user.id,
            FixedBill.monthly_budget_id == mb.id,
            FixedBill.payment_status == BillStatus.PAID.value,
            or_(FixedBill.payment_date.is_(None), FixedBill.payment_date <= target_date),
        )
    ) or ZERO

    cum_income = db.scalar(
        select(func.coalesce(func.sum(Income.amount), ZERO)).where(
            Income.user_id == current_user.id,
            Income.monthly_budget_id == mb.id,
            Income.income_date <= target_date,
        )
    ) or ZERO

    rem_budget_as_of_date = mb.budget_amount - (cum_daily_exp + cum_paid_bills)
    avail_cash_as_of_date = mb.opening_cash + cum_income - (cum_daily_exp + cum_paid_bills)

    return DailyExpenseSummaryResponse(
        selected_date=target_date,
        day_of_week=target_date.strftime("%A"),
        year=target_date.year,
        month=target_date.month,
        month_exists=True,
        monthly_budget_id=mb.id,
        daily_total=daily_total,
        food_expenses=food,
        transportation_expenses=transport,
        education_expenses=education,
        other_expenses=other,
        transaction_count=len(day_expenses),
        remaining_monthly_budget_as_of_date=rem_budget_as_of_date,
        available_cash_as_of_date=avail_cash_as_of_date,
        daily_spending_target=daily_target,
        remaining_daily_allowance=(daily_target - daily_total) if daily_target is not None else None,
        expenses=[_to_expense_response(e) for e in day_expenses],
    )


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = db.scalar(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.id == expense_id, Expense.user_id == current_user.id)
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found.")

    if payload.expense_date is not None and payload.expense_date != exp.expense_date:
        target_mb = db.scalar(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == current_user.id,
                MonthlyBudget.year == payload.expense_date.year,
                MonthlyBudget.month == payload.expense_date.month,
            )
        )
        if not target_mb:
            raise HTTPException(status_code=400, detail="Target month does not exist.")
        exp.monthly_budget_id = target_mb.id
        exp.expense_date = payload.expense_date

    if payload.category_id is not None:
        exp.category_id = payload.category_id
    if payload.amount is not None:
        exp.amount = payload.amount
    if payload.description is not None:
        exp.description = payload.description.strip()
    if payload.expense_time is not None:
        exp.expense_time = payload.expense_time
    if payload.notes is not None:
        exp.notes = payload.notes

    if exp.linked_transaction_id:
        ledger = db.get(FinancialTransaction, exp.linked_transaction_id)
        if ledger:
            ledger.amount = exp.amount
            ledger.transaction_date = exp.expense_date
            ledger.description = exp.description
            ledger.monthly_budget_id = exp.monthly_budget_id

    db.commit()
    exp = db.scalar(
        select(Expense).options(joinedload(Expense.category)).where(Expense.id == exp.id)
    )
    return _to_expense_response(exp)


@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = db.scalar(
        select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id)
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found.")

    linked_id = exp.linked_transaction_id
    db.delete(exp)
    if linked_id:
        ledger = db.get(FinancialTransaction, linked_id)
        if ledger:
            db.delete(ledger)
    db.commit()
    return {"message": "Expense deleted and totals updated."}
