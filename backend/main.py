"""
CloudDrive API — FastAPI application.

Endpoints
  Auth     POST /api/auth/signup, POST /api/auth/login, GET /api/auth/me
  Folders  POST /api/folders, GET /api/folders
  Files    POST /api/files/init        (get pre-signed upload URL)
           POST /api/files/{id}/complete
           GET  /api/files             (list)
           GET  /api/files/{id}/download
           DELETE /api/files/{id}
  Sharing  POST /api/shares, GET /api/files/{id}/shares, GET /api/public/{token}
  Blob     PUT/GET /api/blob/...        (local backend only — fakes S3)
"""
import datetime
import os
import secrets
import shutil
import uuid

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from . import models, schemas, auth
from .storage import storage, LocalStorage

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CloudDrive API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


# ======================================================================== #
#  AUTH
# ======================================================================== #
@app.post("/api/auth/signup", response_model=schemas.Token)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")
    user = models.User(
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        storage_quota=settings.default_quota_mb * 1024 * 1024,
    )
    db.add(user)
    db.commit()
    return schemas.Token(access_token=auth.create_access_token(user.email))


@app.post("/api/auth/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 form sends "username" — we treat it as the email.
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not auth.verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return schemas.Token(access_token=auth.create_access_token(user.email))


@app.get("/api/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(auth.get_current_user)):
    return user


# ======================================================================== #
#  FOLDERS
# ======================================================================== #
@app.post("/api/folders", response_model=schemas.FolderOut)
def create_folder(
    payload: schemas.FolderCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    folder = models.Folder(name=payload.name, parent_id=payload.parent_id, owner_id=user.id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@app.get("/api/folders", response_model=list[schemas.FolderOut])
def list_folders(
    parent_id: int | None = None,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Folder)
        .filter(models.Folder.owner_id == user.id, models.Folder.parent_id == parent_id)
        .order_by(models.Folder.name)
        .all()
    )


# ======================================================================== #
#  FILES  (the pre-signed upload flow)
# ======================================================================== #
@app.post("/api/files/init", response_model=schemas.UploadTicket)
def init_upload(
    payload: schemas.FileInit,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Step 1: check quota, reserve a DB row, return a pre-signed PUT URL."""
    if user.storage_used + payload.size > user.storage_quota:
        raise HTTPException(413, "Storage quota exceeded")

    key = f"u{user.id}/{uuid.uuid4().hex}_{payload.name}"
    file = models.File(
        name=payload.name,
        s3_key=key,
        size=payload.size,
        content_type=payload.content_type,
        owner_id=user.id,
        folder_id=payload.folder_id,
        uploaded=False,
    )
    db.add(file)
    db.commit()
    db.refresh(file)

    url = storage.presigned_put(key, payload.content_type)
    return schemas.UploadTicket(file_id=file.id, upload_url=url, method="PUT")


@app.post("/api/files/{file_id}/complete", response_model=schemas.FileOut)
def complete_upload(
    file_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Step 3: browser tells us the bytes landed; we mark it done + bill quota."""
    file = _owned_file(file_id, user, db)
    if not file.uploaded:
        file.uploaded = True
        user.storage_used += file.size
        db.commit()
    db.refresh(file)
    return file


@app.get("/api/files", response_model=list[schemas.FileOut])
def list_files(
    folder_id: int | None = None,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.File)
        .filter(
            models.File.owner_id == user.id,
            models.File.folder_id == folder_id,
            models.File.uploaded == True,  # noqa: E712
        )
        .order_by(models.File.created_at.desc())
        .all()
    )


@app.get("/api/files/{file_id}/download")
def download_file(
    file_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Returns a short-lived pre-signed GET URL; the browser fetches bytes directly."""
    file = _owned_file(file_id, user, db)
    return {"download_url": storage.presigned_get(file.s3_key, file.name)}


@app.delete("/api/files/{file_id}")
def delete_file(
    file_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    file = _owned_file(file_id, user, db)
    storage.delete(file.s3_key)
    if file.uploaded:
        user.storage_used = max(0, user.storage_used - file.size)
    db.delete(file)
    db.commit()
    return {"deleted": file_id}


# ======================================================================== #
#  SHARING
# ======================================================================== #
@app.post("/api/shares", response_model=schemas.ShareOut)
def create_share(
    payload: schemas.ShareCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    file = _owned_file(payload.file_id, user, db)
    share = models.Share(file_id=file.id, permission=payload.permission)

    if payload.expires_in_hours:
        share.expires_at = _now() + datetime.timedelta(hours=payload.expires_in_hours)

    if payload.public:
        share.public_token = secrets.token_urlsafe(16)
    elif payload.email:
        target = db.query(models.User).filter(models.User.email == payload.email).first()
        if not target:
            raise HTTPException(
                404,
                "No CloudDrive account uses that email. They must sign up first — "
                "or use a public link to share with anyone.",
            )
        share.shared_with_user_id = target.id
    else:
        raise HTTPException(400, "Provide an email or set public=true")

    db.add(share)
    db.commit()
    db.refresh(share)

    out = schemas.ShareOut.model_validate(share)
    if share.public_token:
        out.public_url = f"{settings.public_api_url}/api/public/{share.public_token}"
    return out


@app.get("/api/files/{file_id}/shares", response_model=list[schemas.ShareOut])
def list_shares(
    file_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    _owned_file(file_id, user, db)
    return db.query(models.Share).filter(models.Share.file_id == file_id).all()


@app.get("/api/shared-with-me", response_model=list[schemas.FileOut])
def shared_with_me(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.File)
        .join(models.Share, models.Share.file_id == models.File.id)
        .filter(models.Share.shared_with_user_id == user.id)
        .all()
    )
    return rows


@app.get("/api/files/{file_id}/shared-download")
def shared_download(
    file_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Download a file that another user shared with me (not one I own)."""
    share = (
        db.query(models.Share)
        .filter(
            models.Share.file_id == file_id,
            models.Share.shared_with_user_id == user.id,
        )
        .first()
    )
    if not share:
        raise HTTPException(404, "File not shared with you")
    if share.expires_at and _now() > share.expires_at.replace(tzinfo=datetime.timezone.utc):
        raise HTTPException(410, "Share expired")
    file = db.query(models.File).filter(models.File.id == file_id).first()
    if not file:
        raise HTTPException(404, "File no longer exists")
    return {"download_url": storage.presigned_get(file.s3_key, file.name)}


@app.get("/api/public/{token}")
def public_download(token: str, db: Session = Depends(get_db)):
    """Anyone with the link can download — until it expires.

    Redirects straight to a fresh pre-signed URL so the browser downloads the
    file (works from any device). The pre-signed URL points at S3 directly,
    so even the file bytes never touch this server.
    """
    share = db.query(models.Share).filter(models.Share.public_token == token).first()
    if not share:
        raise HTTPException(404, "Link not found")
    if share.expires_at and _now() > share.expires_at.replace(tzinfo=datetime.timezone.utc):
        raise HTTPException(410, "Link expired")
    file = db.query(models.File).filter(models.File.id == share.file_id).first()
    if not file:
        raise HTTPException(404, "File no longer exists")
    return RedirectResponse(url=storage.presigned_get(file.s3_key, file.name))


# ======================================================================== #
#  BLOB endpoints — ONLY used by the local backend to emulate S3.
#  In production (S3 backend) the browser hits AWS directly and these are dead.
# ======================================================================== #
def _check_local(op: str, key: str, request: Request):
    if not isinstance(storage, LocalStorage):
        raise HTTPException(404, "Not found")
    try:
        exp = int(request.query_params.get("exp", "0"))
    except ValueError:
        raise HTTPException(400, "Bad signature")
    sig = request.query_params.get("sig", "")
    if not storage.verify(key, op, exp, sig):
        raise HTTPException(403, "Invalid or expired URL")


@app.put("/api/blob/put/{key:path}")
async def blob_put(key: str, request: Request):
    _check_local("put", key, request)
    path = storage._path(key)
    with open(path, "wb") as f:
        async for chunk in request.stream():
            f.write(chunk)
    return Response(status_code=200)


@app.get("/api/blob/get/{key:path}")
def blob_get(key: str, request: Request):
    _check_local("get", key, request)
    path = storage._path(key)
    if not os.path.exists(path):
        raise HTTPException(404, "Object not found")
    filename = request.query_params.get("name") or os.path.basename(key)
    return FileResponse(path, filename=filename)


# ======================================================================== #
#  Helpers
# ======================================================================== #
def _owned_file(file_id: int, user: models.User, db: Session) -> models.File:
    file = (
        db.query(models.File)
        .filter(models.File.id == file_id, models.File.owner_id == user.id)
        .first()
    )
    if not file:
        raise HTTPException(404, "File not found")
    return file


@app.get("/api/health")
def health():
    return {"status": "ok", "storage": settings.storage_backend}


# ======================================================================== #
#  Serve the frontend (so the whole app runs from one process in the demo)
# ======================================================================== #
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
