import calendar
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.all_models import (
    BillStatus,
    DebtStatus,
    Expense,
    ExpenseCategory,
    FixedBill,
    Income,
    Lending,
    LendingRepayment,
    Loan,
    LoanRepayment,
    MonthlyBudget,
)

ZERO = Decimal("0.00")


def get_month_date_range(year: int, month: int) -> tuple[date, date, int]:
    """Returns (start_date, end_date, days_in_month) using real Gregorian calendar."""
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day), last_day


def compute_monthly_summary(db: Session, user_id: int, mb: MonthlyBudget) -> dict:
    """
    Authoritative financial formulas:
    - Total Ordinary Expenses = Daily Expenses + Paid Fixed Bills (never double-counted)
    - Remaining Budget = Monthly Budget - Total Ordinary Expenses (can be negative)
    - Available Cash = Opening Cash + Inflows (Income + Loans Borrowed + Lending Returned)
                       - Outflows (Daily Expenses + Paid Fixed Bills + Loans Repaid + Money Lent)
    """
    start_date, end_date, days_in_month = get_month_date_range(mb.year, mb.month)

    daily_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), ZERO)).where(
            Expense.user_id == user_id,
            Expense.monthly_budget_id == mb.id,
        )
    ) or ZERO

    paid_bills_total = db.scalar(
        select(func.coalesce(func.sum(FixedBill.amount), ZERO)).where(
            FixedBill.user_id == user_id,
            FixedBill.monthly_budget_id == mb.id,
            FixedBill.payment_status == BillStatus.PAID.value,
        )
    ) or ZERO

    unpaid_bills_total = db.scalar(
        select(func.coalesce(func.sum(FixedBill.amount), ZERO)).where(
            FixedBill.user_id == user_id,
            FixedBill.monthly_budget_id == mb.id,
            FixedBill.payment_status == BillStatus.UNPAID.value,
        )
    ) or ZERO

    total_fixed_bills = paid_bills_total + unpaid_bills_total

    income_total = db.scalar(
        select(func.coalesce(func.sum(Income.amount), ZERO)).where(
            Income.user_id == user_id,
            Income.monthly_budget_id == mb.id,
        )
    ) or ZERO

    # Loans & Lending cash flows occurring within this Gregorian month
    borrowed_in_month = db.scalar(
        select(func.coalesce(func.sum(Loan.principal_amount), ZERO)).where(
            Loan.user_id == user_id,
            Loan.borrowing_date >= start_date,
            Loan.borrowing_date <= end_date,
        )
    ) or ZERO

    loan_repayments_in_month = db.scalar(
        select(func.coalesce(func.sum(LoanRepayment.amount), ZERO))
        .join(Loan, Loan.id == LoanRepayment.loan_id)
        .where(
            Loan.user_id == user_id,
            LoanRepayment.repayment_date >= start_date,
            LoanRepayment.repayment_date <= end_date,
        )
    ) or ZERO

    lent_in_month = db.scalar(
        select(func.coalesce(func.sum(Lending.principal_amount), ZERO)).where(
            Lending.user_id == user_id,
            Lending.lending_date >= start_date,
            Lending.lending_date <= end_date,
        )
    ) or ZERO

    lending_returns_in_month = db.scalar(
        select(func.coalesce(func.sum(LendingRepayment.amount), ZERO))
        .join(Lending, Lending.id == LendingRepayment.lending_id)
        .where(
            Lending.user_id == user_id,
            LendingRepayment.repayment_date >= start_date,
            LendingRepayment.repayment_date <= end_date,
        )
    ) or ZERO

    # Overall active debt/receivable balances for the user
    outstanding_loans = db.scalar(
        select(func.coalesce(func.sum(Loan.outstanding_amount), ZERO)).where(
            Loan.user_id == user_id,
            Loan.status == DebtStatus.ACTIVE.value,
        )
    ) or ZERO

    outstanding_lending = db.scalar(
        select(func.coalesce(func.sum(Lending.outstanding_amount), ZERO)).where(
            Lending.user_id == user_id,
            Lending.status == DebtStatus.ACTIVE.value,
        )
    ) or ZERO

    total_ordinary_expenses = daily_expenses_total + paid_bills_total
    remaining_budget = mb.budget_amount - total_ordinary_expenses

    cash_inflows = income_total + borrowed_in_month + lending_returns_in_month
    cash_outflows = total_ordinary_expenses + loan_repayments_in_month + lent_in_month
    available_cash = mb.opening_cash + cash_inflows - cash_outflows

    budget_utilization = (
        ((total_ordinary_expenses / mb.budget_amount) * Decimal("100.00")).quantize(Decimal("0.01"))
        if mb.budget_amount > ZERO
        else ZERO
    )

    # Category breakdown for the month
    cat_rows = db.execute(
        select(ExpenseCategory.name, func.coalesce(func.sum(Expense.amount), ZERO))
        .join(Expense, Expense.category_id == ExpenseCategory.id)
        .where(Expense.user_id == user_id, Expense.monthly_budget_id == mb.id)
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(Expense.amount).desc())
    ).all()

    category_breakdown = {name: amt for name, amt in cat_rows}

    return {
        "id": mb.id,
        "year": mb.year,
        "month": mb.month,
        "month_name": calendar.month_name[mb.month],
        "days_in_month": days_in_month,
        "budget_amount": mb.budget_amount,
        "opening_cash": mb.opening_cash,
        "notes": mb.notes,
        "is_archived": mb.is_archived,
        "daily_expenses_total": daily_expenses_total,
        "paid_bills_total": paid_bills_total,
        "unpaid_bills_total": unpaid_bills_total,
        "total_fixed_bills": total_fixed_bills,
        "total_ordinary_expenses": total_ordinary_expenses,
        "remaining_budget": remaining_budget,
        "income_total": income_total,
        "borrowed_in_month": borrowed_in_month,
        "loan_repayments_in_month": loan_repayments_in_month,
        "lent_in_month": lent_in_month,
        "lending_returns_in_month": lending_returns_in_month,
        "available_cash": available_cash,
        "outstanding_loans": outstanding_loans,
        "outstanding_lending": outstanding_lending,
        "budget_utilization_pct": budget_utilization,
        "is_over_budget": remaining_budget < ZERO,
        "category_breakdown": category_breakdown,
    }
