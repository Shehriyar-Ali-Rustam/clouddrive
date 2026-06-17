"""
Pytest fixtures.

We point the app at a throwaway SQLite DB and a temp storage dir BEFORE
importing it, so tests never touch your real data. Each test run starts clean.
"""
import os
import tempfile

import pytest

# --- configure an isolated environment before the app is imported ---
_tmp = tempfile.mkdtemp(prefix="clouddrive_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["LOCAL_STORAGE_DIR"] = f"{_tmp}/storage"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEFAULT_QUOTA_MB"] = "1"          # 1 MB quota -> easy to test limits
os.environ["PUBLIC_API_URL"] = "http://testserver"

from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app               # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """A TestClient already logged in as a fresh unique user."""
    import uuid
    email = f"user_{uuid.uuid4().hex[:8]}@test.edu"
    r = client.post("/api/auth/signup", json={"email": email, "password": "pw12345"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    client.email = email
    return client
