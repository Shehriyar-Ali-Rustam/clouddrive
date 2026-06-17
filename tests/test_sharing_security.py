"""Sharing (user + public links) and storage security (signed URLs)."""
from tests.test_files import _upload


def test_share_with_user(auth_client, client):
    fid, _ = _upload(auth_client, name="shared.txt")

    import uuid
    target = f"target_{uuid.uuid4().hex[:6]}@test.edu"
    client.post("/api/auth/signup", json={"email": target, "password": "pw12345"})

    r = auth_client.post("/api/shares", json={"file_id": fid, "email": target})
    assert r.status_code == 200
    assert r.json()["shared_with_user_id"] is not None


def test_share_with_unknown_user_404(auth_client):
    fid, _ = _upload(auth_client)
    r = auth_client.post("/api/shares", json={"file_id": fid, "email": "ghost@nowhere.edu"})
    assert r.status_code == 404


def test_public_link_download(auth_client):
    content = b"public bytes"
    fid, _ = _upload(auth_client, name="pub.txt", content=content)

    share = auth_client.post("/api/shares", json={"file_id": fid, "public": True})
    assert share.status_code == 200
    token = share.json()["public_token"]

    # anonymous client can resolve + download
    pub = auth_client.get(f"/api/public/{token}")
    assert pub.status_code == 200
    dl_path = pub.json()["download_url"].replace("http://testserver", "")
    blob = auth_client.get(dl_path)
    assert blob.content == content


def test_public_link_unknown_token_404(client):
    r = client.get("/api/public/does-not-exist")
    assert r.status_code == 404


def test_tampered_signature_rejected(auth_client):
    """A pre-signed URL with a forged signature must be refused."""
    fid, _ = _upload(auth_client, name="secure.txt")
    dl = auth_client.get(f"/api/files/{fid}/download").json()["download_url"]
    path = dl.replace("http://testserver", "")

    # Corrupt the signature
    tampered = path.replace("sig=", "sig=deadbeef")
    r = auth_client.get(tampered)
    assert r.status_code == 403


def test_health_reports_backend(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["storage"] == "local"
