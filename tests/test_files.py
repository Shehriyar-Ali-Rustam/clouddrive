"""The full pre-signed upload/download lifecycle + quota enforcement."""


def _upload(client, name="file.txt", content=b"hello world"):
    """Runs the real 3-step pre-signed flow against the local backend."""
    init = client.post("/api/files/init", json={
        "name": name, "size": len(content), "content_type": "text/plain",
    })
    assert init.status_code == 200, init.text
    ticket = init.json()

    # Step 2: PUT bytes to the pre-signed URL (strip host -> relative path for TestClient)
    put_path = ticket["upload_url"].replace("http://testserver", "")
    put = client.put(put_path, content=content)
    assert put.status_code == 200, put.text

    # Step 3: complete
    done = client.post(f"/api/files/{ticket['file_id']}/complete")
    assert done.status_code == 200, done.text
    return ticket["file_id"], done.json()


def test_upload_lifecycle(auth_client):
    fid, meta = _upload(auth_client)
    assert meta["uploaded"] is True
    assert meta["size"] == 11


def test_uploaded_file_appears_in_list(auth_client):
    _upload(auth_client, name="listed.txt")
    r = auth_client.get("/api/files")
    assert r.status_code == 200
    names = [f["name"] for f in r.json()]
    assert "listed.txt" in names


def test_download_returns_original_bytes(auth_client):
    content = b"the actual file contents 123"
    fid, _ = _upload(auth_client, name="dl.txt", content=content)

    r = auth_client.get(f"/api/files/{fid}/download")
    assert r.status_code == 200
    dl_path = r.json()["download_url"].replace("http://testserver", "")
    blob = auth_client.get(dl_path)
    assert blob.status_code == 200
    assert blob.content == content


def test_quota_is_billed_after_upload(auth_client):
    _upload(auth_client, content=b"x" * 500)
    me = auth_client.get("/api/auth/me").json()
    assert me["storage_used"] == 500


def test_quota_exceeded_is_rejected(auth_client):
    # Quota is 1 MB; ask to upload 2 MB -> 413
    r = auth_client.post("/api/files/init", json={
        "name": "huge.bin", "size": 2 * 1024 * 1024, "content_type": "application/octet-stream",
    })
    assert r.status_code == 413


def test_delete_frees_quota(auth_client):
    fid, _ = _upload(auth_client, content=b"y" * 300)
    assert auth_client.get("/api/auth/me").json()["storage_used"] == 300

    d = auth_client.delete(f"/api/files/{fid}")
    assert d.status_code == 200
    assert auth_client.get("/api/auth/me").json()["storage_used"] == 0


def test_cannot_access_another_users_file(auth_client, client):
    fid, _ = _upload(auth_client, name="private.txt")

    # second, different user
    import uuid
    other = f"other_{uuid.uuid4().hex[:6]}@test.edu"
    tok = client.post("/api/auth/signup", json={"email": other, "password": "pw12345"}).json()["access_token"]
    r = client.get(f"/api/files/{fid}/download", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 404  # not visible to other users
