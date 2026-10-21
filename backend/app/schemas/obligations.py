from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class FixedBillCreateRequest(BaseModel):
    monthly_budget_id: int
    name: str = Field(..., min_length=1, max_length=120)
    amount: Decimal = Field(..., ge=Decimal("0.00"))
    due_date: Optional[date] = None
    payment_status: str = Field(default="UNPAID", pattern="^(UNPAID|PAID)$")
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class FixedBillUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    due_date: Optional[date] = None
    payment_status: Optional[str] = Field(None, pattern="^(UNPAID|PAID)$")
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class FixedBillResponse(BaseModel):
    id: int
    monthly_budget_id: int
    name: str
    amount: Decimal
    due_date: Optional[date] = None
    payment_status: str
    payment_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IncomeCreateRequest(BaseModel):
    monthly_budget_id: int
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    category: str = Field(..., min_length=1, max_length=80)
    income_date: date
    description: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None


class IncomeResponse(BaseModel):
    id: int
    monthly_budget_id: int
    amount: Decimal
    category: str
    income_date: date
    description: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    repayment_date: date
    notes: Optional[str] = None


class RepaymentResponse(BaseModel):
    id: int
    amount: Decimal
    repayment_date: date
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoanCreateRequest(BaseModel):
    person_name: str = Field(..., min_length=1, max_length=120)
    principal_amount: Decimal = Field(..., gt=Decimal("0.00"))
    borrowing_date: date
    purpose: Optional[str] = None
    notes: Optional[str] = None


class LoanResponse(BaseModel):
    id: int
    person_name: str
    principal_amount: Decimal
    outstanding_amount: Decimal
    borrowing_date: date
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: str
    repayments: List[RepaymentResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class LendingCreateRequest(BaseModel):
    person_name: str = Field(..., min_length=1, max_length=120)
    principal_amount: Decimal = Field(..., gt=Decimal("0.00"))
    lending_date: date
    expected_return_date: Optional[date] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None


class LendingResponse(BaseModel):
    id: int
    person_name: str
    principal_amount: Decimal
    outstanding_amount: Decimal
    lending_date: date
    expected_return_date: Optional[date] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: str
    repayments: List[RepaymentResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    preferred_dashboard_month: Optional[str] = None
    daily_spending_target: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
