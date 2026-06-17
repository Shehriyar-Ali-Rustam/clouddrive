"""Auth: signup, login, token validation, duplicate prevention."""
import uuid


def _email():
    return f"u_{uuid.uuid4().hex[:8]}@test.edu"


def test_signup_returns_token(client):
    r = client.post("/api/auth/signup", json={"email": _email(), "password": "pw12345"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_duplicate_email_rejected(client):
    email = _email()
    client.post("/api/auth/signup", json={"email": email, "password": "pw12345"})
    r = client.post("/api/auth/signup", json={"email": email, "password": "pw12345"})
    assert r.status_code == 400


def test_login_with_correct_password(client):
    email = _email()
    client.post("/api/auth/signup", json={"email": email, "password": "secret99"})
    r = client.post("/api/auth/login", data={"username": email, "password": "secret99"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_with_wrong_password(client):
    email = _email()
    client.post("/api/auth/signup", json={"email": email, "password": "secret99"})
    r = client.post("/api/auth/login", data={"username": email, "password": "WRONG"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_returns_user(auth_client):
    r = auth_client.get("/api/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == auth_client.email
    assert body["storage_used"] == 0
    assert body["storage_quota"] == 1 * 1024 * 1024  # 1 MB from test config
