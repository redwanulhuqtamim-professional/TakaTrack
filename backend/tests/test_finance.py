import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _register_fresh_user():
    email = f"fin_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Finance Tester",
            "email": email,
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert res.status_code == 201
    return res.json()


def test_exact_specification_financial_scenario():
    """
    Tests the exact Section 23 scenario:
    - Opening cash: ৳20,000
    - Monthly budget: ৳20,000
    - Rent paid: ৳5,000
    - Electricity bill paid: ৳800
    - Wi-Fi bill paid: ৳500
    - Food expense: ৳1,000
    - Transportation expense: ৳200
    Expected ordinary expenses: ৳7,500
    Expected remaining budget: ৳12,500
    Expected available cash: ৳12,500
    """
    _register_fresh_user()

    m_res = client.post(
        "/api/months",
        json={
            "year": 2026,
            "month": 10,
            "budget_amount": "20000.00",
            "opening_cash": "20000.00",
        },
    )
    assert m_res.status_code == 201
    month_data = m_res.json()
    month_id = month_data["id"]
    assert month_data["days_in_month"] == 31

    dup_res = client.post(
        "/api/months",
        json={"year": 2026, "month": 10, "budget_amount": "15000.00", "opening_cash": "0.00"},
    )
    assert dup_res.status_code == 409

    for name, amt, status in [
        ("House Rent", "5000.00", "PAID"),
        ("Electricity Bill", "800.00", "PAID"),
        ("Wi-Fi Internet", "500.00", "PAID"),
        ("Water Bill", "400.00", "UNPAID"),
    ]:
        b_res = client.post(
            "/api/bills",
            json={
                "monthly_budget_id": month_id,
                "name": name,
                "amount": amt,
                "payment_status": status,
                "payment_date": "2026-10-05" if status == "PAID" else None,
            },
        )
        assert b_res.status_code == 201

    cats = client.get("/api/categories").json()
    food_cat_id = next(c["id"] for c in cats if "Food" in c["name"])
    trans_cat_id = next(c["id"] for c in cats if "Transportation" in c["name"])

    e1 = client.post(
        "/api/expenses",
        json={
            "amount": "1000.00",
            "category_id": food_cat_id,
            "description": "Weekly groceries and rice",
            "expense_date": "2026-10-18",
        },
    )
    assert e1.status_code == 201

    e2 = client.post(
        "/api/expenses",
        json={
            "amount": "200.00",
            "category_id": trans_cat_id,
            "description": "Rickshaw and bus fare",
            "expense_date": "2026-10-18",
        },
    )
    assert e2.status_code == 201

    summary = client.get("/api/months/by-period/2026/10").json()
    assert Decimal(summary["paid_bills_total"]) == Decimal("6300.00")
    assert Decimal(summary["unpaid_bills_total"]) == Decimal("400.00")
    assert Decimal(summary["daily_expenses_total"]) == Decimal("1200.00")
    assert Decimal(summary["total_ordinary_expenses"]) == Decimal("7500.00")
    assert Decimal(summary["remaining_budget"]) == Decimal("12500.00")
    assert Decimal(summary["available_cash"]) == Decimal("12500.00")


def test_loans_lending_and_leap_year_months():
    _register_fresh_user()

    feb27 = client.post(
        "/api/months",
        json={"year": 2027, "month": 2, "budget_amount": "10000.00", "opening_cash": "10000.00"},
    ).json()
    assert feb27["days_in_month"] == 28

    feb28 = client.post(
        "/api/months",
        json={"year": 2028, "month": 2, "budget_amount": "10000.00", "opening_cash": "10000.00"},
    ).json()
    assert feb28["days_in_month"] == 29

    loan_res = client.post(
        "/api/loans",
        json={
            "person_name": "Rahim",
            "principal_amount": "5000.00",
            "borrowing_date": "2027-02-10",
            "purpose": "Emergency laptop repair",
        },
    )
    assert loan_res.status_code == 201
    loan_id = loan_res.json()["id"]

    rep_res = client.post(
        f"/api/loans/{loan_id}/repayments",
        json={"amount": "2000.00", "repayment_date": "2027-02-15"},
    )
    assert rep_res.status_code == 200
    assert Decimal(rep_res.json()["outstanding_amount"]) == Decimal("3000.00")

    bad_rep = client.post(
        f"/api/loans/{loan_id}/repayments",
        json={"amount": "4000.00", "repayment_date": "2027-02-16"},
    )
    assert bad_rep.status_code == 400

    lend_res = client.post(
        "/api/lendings",
        json={
            "person_name": "Karim",
            "principal_amount": "2000.00",
            "lending_date": "2027-02-12",
        },
    )
    assert lend_res.status_code == 201
    lending_id = lend_res.json()["id"]

    l_ret = client.post(
        f"/api/lendings/{lending_id}/repayments",
        json={"amount": "500.00", "repayment_date": "2027-02-20"},
    )
    assert l_ret.status_code == 200
    assert Decimal(l_ret.json()["outstanding_amount"]) == Decimal("1500.00")

    summary = client.get("/api/months/by-period/2027/2").json()
    assert Decimal(summary["total_ordinary_expenses"]) == Decimal("0.00")
    assert Decimal(summary["remaining_budget"]) == Decimal("10000.00")
    assert Decimal(summary["available_cash"]) == Decimal("11500.00")
    assert Decimal(summary["outstanding_loans"]) == Decimal("3000.00")
    assert Decimal(summary["outstanding_lending"]) == Decimal("1500.00")
