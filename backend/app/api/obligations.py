from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.all_models import (
    BillStatus,
    DebtStatus,
    FinancialTransaction,
    FixedBill,
    Income,
    Lending,
    LendingRepayment,
    Loan,
    LoanRepayment,
    MonthlyBudget,
    TransactionType,
    User,
)
from app.schemas.obligations import (
    FixedBillCreateRequest,
    FixedBillResponse,
    FixedBillUpdateRequest,
    IncomeCreateRequest,
    IncomeResponse,
    LendingCreateRequest,
    LendingResponse,
    LoanCreateRequest,
    LoanResponse,
    RepaymentCreateRequest,
)

router = APIRouter(prefix="/api", tags=["Bills, Income, Loans & Lending"])
ZERO = Decimal("0.00")


@router.post("/bills", response_model=FixedBillResponse, status_code=status.HTTP_201_CREATED)
def create_fixed_bill(
    payload: FixedBillCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.id == payload.monthly_budget_id,
            MonthlyBudget.user_id == current_user.id,
        )
    )
    if not mb:
        raise HTTPException(status_code=404, detail="Monthly budget not found.")

    pay_date = payload.payment_date or (date(mb.year, mb.month, 1) if payload.payment_status == "PAID" else None)
    ledger_id = None
    if payload.payment_status == BillStatus.PAID.value and payload.amount > ZERO:
        ledger = FinancialTransaction(
            user_id=current_user.id,
            monthly_budget_id=mb.id,
            transaction_type=TransactionType.FIXED_BILL_PAYMENT.value,
            amount=payload.amount,
            transaction_date=pay_date or date(mb.year, mb.month, 1),
            description=f"Fixed Bill Paid: {payload.name.strip()}",
        )
        db.add(ledger)
        db.flush()
        ledger_id = ledger.id

    bill = FixedBill(
        user_id=current_user.id,
        monthly_budget_id=mb.id,
        linked_transaction_id=ledger_id,
        name=payload.name.strip(),
        amount=payload.amount,
        due_date=payload.due_date,
        payment_status=payload.payment_status,
        payment_date=pay_date,
        notes=payload.notes,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.get("/bills", response_model=List[FixedBillResponse])
def list_fixed_bills(
    monthly_budget_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(FixedBill)
        .where(
            FixedBill.user_id == current_user.id,
            FixedBill.monthly_budget_id == monthly_budget_id,
        )
        .order_by(FixedBill.id.asc())
    ).all()


@router.patch("/bills/{bill_id}", response_model=FixedBillResponse)
def update_fixed_bill(
    bill_id: int,
    payload: FixedBillUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.scalar(
        select(FixedBill).where(FixedBill.id == bill_id, FixedBill.user_id == current_user.id)
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Fixed bill not found.")

    if payload.name is not None:
        bill.name = payload.name.strip()
    if payload.amount is not None:
        bill.amount = payload.amount
    if payload.due_date is not None:
        bill.due_date = payload.due_date
    if payload.notes is not None:
        bill.notes = payload.notes

    # Idempotent paid/unpaid state transition without double counting
    if payload.payment_status is not None:
        bill.payment_status = payload.payment_status
        if payload.payment_status == BillStatus.PAID.value:
            bill.payment_date = payload.payment_date or bill.payment_date or date.today()
            if not bill.linked_transaction_id and bill.amount > ZERO:
                ledger = FinancialTransaction(
                    user_id=current_user.id,
                    monthly_budget_id=bill.monthly_budget_id,
                    transaction_type=TransactionType.FIXED_BILL_PAYMENT.value,
                    amount=bill.amount,
                    transaction_date=bill.payment_date,
                    description=f"Fixed Bill Paid: {bill.name}",
                )
                db.add(ledger)
                db.flush()
                bill.linked_transaction_id = ledger.id
        else:
            bill.payment_date = None
            if bill.linked_transaction_id:
                old_ledger = db.get(FinancialTransaction, bill.linked_transaction_id)
                if old_ledger:
                    db.delete(old_ledger)
                bill.linked_transaction_id = None

    if bill.linked_transaction_id and bill.amount > ZERO:
        ledger = db.get(FinancialTransaction, bill.linked_transaction_id)
        if ledger:
            ledger.amount = bill.amount
            ledger.description = f"Fixed Bill Paid: {bill.name}"

    db.commit()
    db.refresh(bill)
    return bill


@router.delete("/bills/{bill_id}")
def delete_fixed_bill(
    bill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.scalar(
        select(FixedBill).where(FixedBill.id == bill_id, FixedBill.user_id == current_user.id)
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Fixed bill not found.")
    linked_id = bill.linked_transaction_id
    db.delete(bill)
    if linked_id:
        ledger = db.get(FinancialTransaction, linked_id)
        if ledger:
            db.delete(ledger)
    db.commit()
    return {"message": "Fixed bill deleted."}


@router.post("/incomes", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    payload: IncomeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mb = db.scalar(
        select(MonthlyBudget).where(
            MonthlyBudget.id == payload.monthly_budget_id,
            MonthlyBudget.user_id == current_user.id,
        )
    )
    if not mb:
        raise HTTPException(status_code=404, detail="Monthly budget not found.")

    ledger = FinancialTransaction(
        user_id=current_user.id,
        monthly_budget_id=mb.id,
        transaction_type=TransactionType.INCOME.value,
        amount=payload.amount,
        transaction_date=payload.income_date,
        description=payload.description.strip(),
    )
    db.add(ledger)
    db.flush()

    inc = Income(
        user_id=current_user.id,
        monthly_budget_id=mb.id,
        linked_transaction_id=ledger.id,
        amount=payload.amount,
        category=payload.category.strip(),
        income_date=payload.income_date,
        description=payload.description.strip(),
        notes=payload.notes,
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


@router.get("/incomes", response_model=List[IncomeResponse])
def list_incomes(
    monthly_budget_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Income)
        .where(
            Income.user_id == current_user.id,
            Income.monthly_budget_id == monthly_budget_id,
        )
        .order_by(Income.income_date.desc(), Income.id.desc())
    ).all()


@router.delete("/incomes/{income_id}")
def delete_income(
    income_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inc = db.scalar(
        select(Income).where(Income.id == income_id, Income.user_id == current_user.id)
    )
    if not inc:
        raise HTTPException(status_code=404, detail="Income record not found.")
    linked_id = inc.linked_transaction_id
    db.delete(inc)
    if linked_id:
        ledger = db.get(FinancialTransaction, linked_id)
        if ledger:
            db.delete(ledger)
    db.commit()
    return {"message": "Income deleted."}


@router.post("/loans", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ledger = FinancialTransaction(
        user_id=current_user.id,
        monthly_budget_id=None,
        transaction_type=TransactionType.LOAN_PROCEEDS.value,
        amount=payload.principal_amount,
        transaction_date=payload.borrowing_date,
        description=f"Borrowed from {payload.person_name.strip()}",
    )
    db.add(ledger)
    db.flush()

    loan = Loan(
        user_id=current_user.id,
        linked_transaction_id=ledger.id,
        person_name=payload.person_name.strip(),
        principal_amount=payload.principal_amount,
        outstanding_amount=payload.principal_amount,
        borrowing_date=payload.borrowing_date,
        purpose=payload.purpose,
        notes=payload.notes,
        status=DebtStatus.ACTIVE.value,
    )
    db.add(loan)
    db.commit()
    return db.scalar(
        select(Loan).options(joinedload(Loan.repayments)).where(Loan.id == loan.id)
    )


@router.get("/loans", response_model=List[LoanResponse])
def list_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Loan)
        .options(joinedload(Loan.repayments))
        .where(Loan.user_id == current_user.id)
        .order_by(Loan.borrowing_date.desc(), Loan.id.desc())
    ).unique().all()


@router.post("/loans/{loan_id}/repayments", response_model=LoanResponse)
def repay_loan(
    loan_id: int,
    payload: RepaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    loan = db.scalar(
        select(Loan)
        .options(joinedload(Loan.repayments))
        .where(Loan.id == loan_id, Loan.user_id == current_user.id)
    )
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")
    if payload.amount > loan.outstanding_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Repayment amount (৳{payload.amount}) cannot exceed outstanding debt (৳{loan.outstanding_amount}).",
        )

    ledger = FinancialTransaction(
        user_id=current_user.id,
        monthly_budget_id=None,
        transaction_type=TransactionType.LOAN_REPAYMENT.value,
        amount=payload.amount,
        transaction_date=payload.repayment_date,
        description=f"Loan repayment to {loan.person_name}",
    )
    db.add(ledger)
    db.flush()

    repayment = LoanRepayment(
        loan_id=loan.id,
        linked_transaction_id=ledger.id,
        amount=payload.amount,
        repayment_date=payload.repayment_date,
        notes=payload.notes,
    )
    db.add(repayment)

    loan.outstanding_amount -= payload.amount
    if loan.outstanding_amount == ZERO:
        loan.status = DebtStatus.SETTLED.value

    db.commit()
    db.refresh(loan)
    return db.scalar(
        select(Loan).options(joinedload(Loan.repayments)).where(Loan.id == loan.id)
    )


@router.post("/lendings", response_model=LendingResponse, status_code=status.HTTP_201_CREATED)
def create_lending(
    payload: LendingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ledger = FinancialTransaction(
        user_id=current_user.id,
        monthly_budget_id=None,
        transaction_type=TransactionType.LENDING_DISBURSEMENT.value,
        amount=payload.principal_amount,
        transaction_date=payload.lending_date,
        description=f"Lent to {payload.person_name.strip()}",
    )
    db.add(ledger)
    db.flush()

    lending = Lending(
        user_id=current_user.id,
        linked_transaction_id=ledger.id,
        person_name=payload.person_name.strip(),
        principal_amount=payload.principal_amount,
        outstanding_amount=payload.principal_amount,
        lending_date=payload.lending_date,
        expected_return_date=payload.expected_return_date,
        purpose=payload.purpose,
        notes=payload.notes,
        status=DebtStatus.ACTIVE.value,
    )
    db.add(lending)
    db.commit()
    return db.scalar(
        select(Lending).options(joinedload(Lending.repayments)).where(Lending.id == lending.id)
    )


@router.get("/lendings", response_model=List[LendingResponse])
def list_lendings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Lending)
        .options(joinedload(Lending.repayments))
        .where(Lending.user_id == current_user.id)
        .order_by(Lending.lending_date.desc(), Lending.id.desc())
    ).unique().all()


@router.post("/lendings/{lending_id}/repayments", response_model=LendingResponse)
def receive_lending_repayment(
    lending_id: int,
    payload: RepaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lending = db.scalar(
        select(Lending)
        .options(joinedload(Lending.repayments))
        .where(Lending.id == lending_id, Lending.user_id == current_user.id)
    )
    if not lending:
        raise HTTPException(status_code=404, detail="Lending record not found.")
    if payload.amount > lending.outstanding_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Returned amount (৳{payload.amount}) cannot exceed outstanding receivable (৳{lending.outstanding_amount}).",
        )

    ledger = FinancialTransaction(
        user_id=current_user.id,
        monthly_budget_id=None,
        transaction_type=TransactionType.LENDING_RETURN.value,
        amount=payload.amount,
        transaction_date=payload.repayment_date,
        description=f"Repayment received from {lending.person_name}",
    )
    db.add(ledger)
    db.flush()

    repayment = LendingRepayment(
        lending_id=lending.id,
        linked_transaction_id=ledger.id,
        amount=payload.amount,
        repayment_date=payload.repayment_date,
        notes=payload.notes,
    )
    db.add(repayment)

    lending.outstanding_amount -= payload.amount
    if lending.outstanding_amount == ZERO:
        lending.status = DebtStatus.SETTLED.value

    db.commit()
    db.refresh(lending)
    return db.scalar(
        select(Lending).options(joinedload(Lending.repayments)).where(Lending.id == lending.id)
    )
