import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


def test_register_and_me_flow():
    email = _unique_email()
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Redwanul Tamim",
            "email": email,
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == email
    assert data["settings"]["currency"] == "BDT"
    assert data["settings"]["timezone"] == "Asia/Dhaka"

    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


def test_reject_duplicate_registration():
    email = _unique_email()
    payload = {
        "full_name": "Test User",
        "email": email,
        "password": "Password123",
        "confirm_password": "Password123",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409


def test_reject_invalid_credentials_and_protect_private_route():
    email = _unique_email()
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Valid User",
            "email": email,
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    client.post("/api/auth/logout")

    unauth_me = client.get("/api/auth/me")
    assert unauth_me.status_code == 401

    bad_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword999"},
    )
    assert bad_login.status_code == 401
