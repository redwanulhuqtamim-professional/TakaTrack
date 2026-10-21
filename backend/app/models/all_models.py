import enum
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Numeric, Boolean, Date, Time, DateTime,
    ForeignKey, Text, UniqueConstraint, CheckConstraint, Index, func, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class TransactionType(str, enum.Enum):
    INCOME = "INCOME"
    ORDINARY_EXPENSE = "ORDINARY_EXPENSE"
    FIXED_BILL_PAYMENT = "FIXED_BILL_PAYMENT"
    LOAN_PROCEEDS = "LOAN_PROCEEDS"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    LENDING_DISBURSEMENT = "LENDING_DISBURSEMENT"
    LENDING_RETURN = "LENDING_RETURN"


class BillStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class DebtStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SETTLED = "SETTLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    monthly_budgets: Mapped[List["MonthlyBudget"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), default="BDT", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Dhaka", nullable=False)
    preferred_dashboard_month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # YYYY-MM
    daily_spending_target: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    notification_preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="settings")


class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_user_year_month"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_valid_month"),
        CheckConstraint("year >= 2000 AND year <= 2100", name="ck_valid_year"),
        CheckConstraint("budget_amount >= 0", name="ck_non_negative_budget"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    opening_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="monthly_budgets")
    expenses: Mapped[List["Expense"]] = relationship(
        back_populates="monthly_budget", cascade="all, delete-orphan"
    )
    incomes: Mapped[List["Income"]] = relationship(
        back_populates="monthly_budget", cascade="all, delete-orphan"
    )
    fixed_bills: Mapped[List["FixedBill"]] = relationship(
        back_populates="monthly_budget", cascade="all, delete-orphan"
    )


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_category_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category_type: Mapped[str] = mapped_column(String(30), default="EXPENSE", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinancialTransaction(Base):
    """Single authoritative ledger for cash inflows/outflows to prevent double counting."""
    __tablename__ = "financial_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_ledger_positive_amount"),
        Index("ix_ledger_user_date", "user_id", "transaction_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    monthly_budget_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("monthly_budgets.id", ondelete="SET NULL"), index=True, nullable=True
    )
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expense_positive_amount"),
        Index("ix_expense_user_date", "user_id", "expense_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    monthly_budget_id: Mapped[int] = mapped_column(
        ForeignKey("monthly_budgets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    expense_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    monthly_budget: Mapped["MonthlyBudget"] = relationship(back_populates="expenses")
    category: Mapped["ExpenseCategory"] = relationship()


class Income(Base):
    __tablename__ = "incomes"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_income_positive_amount"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    monthly_budget_id: Mapped[int] = mapped_column(
        ForeignKey("monthly_budgets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    income_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    monthly_budget: Mapped["MonthlyBudget"] = relationship(back_populates="incomes")


class FixedBill(Base):
    __tablename__ = "fixed_bills"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_bill_non_negative_amount"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    monthly_budget_id: Mapped[int] = mapped_column(
        ForeignKey("monthly_budgets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), default=BillStatus.UNPAID.value, nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    monthly_budget: Mapped["MonthlyBudget"] = relationship(back_populates="fixed_bills")


class Loan(Base):
    """Money borrowed from another person."""
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("principal_amount > 0", name="ck_loan_positive_principal"),
        CheckConstraint(
            "outstanding_amount >= 0 AND outstanding_amount <= principal_amount",
            name="ck_loan_valid_outstanding",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    person_name: Mapped[str] = mapped_column(String(120), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    borrowing_date: Mapped[date] = mapped_column(Date, nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DebtStatus.ACTIVE.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    repayments: Mapped[List["LoanRepayment"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan"
    )


class LoanRepayment(Base):
    __tablename__ = "loan_repayments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_loan_repayment_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(
        ForeignKey("loans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    repayment_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    loan: Mapped["Loan"] = relationship(back_populates="repayments")


class Lending(Base):
    """Money lent to another person."""
    __tablename__ = "lendings"
    __table_args__ = (
        CheckConstraint("principal_amount > 0", name="ck_lending_positive_principal"),
        CheckConstraint(
            "outstanding_amount >= 0 AND outstanding_amount <= principal_amount",
            name="ck_lending_valid_outstanding",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    person_name: Mapped[str] = mapped_column(String(120), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lending_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DebtStatus.ACTIVE.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    repayments: Mapped[List["LendingRepayment"]] = relationship(
        back_populates="lending", cascade="all, delete-orphan"
    )


class LendingRepayment(Base):
    __tablename__ = "lending_repayments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_lending_repayment_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lending_id: Mapped[int] = mapped_column(
        ForeignKey("lendings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("financial_transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    repayment_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lending: Mapped["Lending"] = relationship(back_populates="repayments")
