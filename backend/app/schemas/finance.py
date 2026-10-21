from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class MonthCreateRequest(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    budget_amount: Decimal = Field(..., ge=Decimal("0.00"))
    opening_cash: Decimal = Field(default=Decimal("0.00"))
    carry_forward_previous_cash: bool = False
    notes: Optional[str] = None


class MonthUpdateRequest(BaseModel):
    budget_amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    opening_cash: Optional[Decimal] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None


class MonthSummaryResponse(BaseModel):
    id: int
    year: int
    month: int
    month_name: str
    days_in_month: int
    budget_amount: Decimal
    opening_cash: Decimal
    notes: Optional[str] = None
    is_archived: bool
    daily_expenses_total: Decimal
    paid_bills_total: Decimal
    unpaid_bills_total: Decimal
    total_fixed_bills: Decimal
    total_ordinary_expenses: Decimal
    remaining_budget: Decimal
    income_total: Decimal
    borrowed_in_month: Decimal
    loan_repayments_in_month: Decimal
    lent_in_month: Decimal
    lending_returns_in_month: Decimal
    available_cash: Decimal
    outstanding_loans: Decimal
    outstanding_lending: Decimal
    budget_utilization_pct: Decimal
    is_over_budget: bool
    category_breakdown: Dict[str, Decimal]
    reconciliation_warning: Optional[str] = None


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)


class CategoryResponse(BaseModel):
    id: int
    name: str
    category_type: str
    is_default: bool

    model_config = {"from_attributes": True}


class ExpenseCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    category_id: int
    description: str = Field(..., min_length=1, max_length=255)
    expense_date: date
    expense_time: Optional[time] = None
    notes: Optional[str] = None


class ExpenseUpdateRequest(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    category_id: Optional[int] = None
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    expense_date: Optional[date] = None
    expense_time: Optional[time] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    monthly_budget_id: int
    category_id: int
    category_name: str
    amount: Decimal
    description: str
    expense_date: date
    expense_time: Optional[time] = None
    notes: Optional[str] = None
    created_at: datetime


class DailyExpenseSummaryResponse(BaseModel):
    selected_date: date
    day_of_week: str
    year: int
    month: int
    month_exists: bool
    monthly_budget_id: Optional[int] = None
    daily_total: Decimal
    food_expenses: Decimal
    transportation_expenses: Decimal
    education_expenses: Decimal
    other_expenses: Decimal
    transaction_count: int
    remaining_monthly_budget_as_of_date: Decimal
    available_cash_as_of_date: Decimal
    daily_spending_target: Optional[Decimal] = None
    remaining_daily_allowance: Optional[Decimal] = None
    expenses: List[ExpenseResponse]
