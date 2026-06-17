"""
Pydantic request/response models — the API's public contract.
"""
import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    storage_used: int
    storage_quota: int

    class Config:
        from_attributes = True


# ---- Folders ----
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- Files ----
class FileInit(BaseModel):
    """Step 1 of upload: client announces a file it wants to upload."""
    name: str
    size: int
    content_type: str = "application/octet-stream"
    folder_id: Optional[int] = None


class UploadTicket(BaseModel):
    """Step 1 response: where + how to PUT the bytes."""
    file_id: int
    upload_url: str
    method: str  # "PUT"


class FileOut(BaseModel):
    id: int
    name: str
    size: int
    content_type: str
    folder_id: Optional[int]
    uploaded: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- Sharing ----
class ShareCreate(BaseModel):
    file_id: int
    email: Optional[EmailStr] = None     # share with a specific user
    public: bool = False                 # OR create a public link
    expires_in_hours: Optional[int] = None
    permission: str = "read"


class ShareOut(BaseModel):
    id: int
    file_id: int
    shared_with_user_id: Optional[int]
    public_token: Optional[str]
    permission: str
    expires_at: Optional[datetime.datetime]
    public_url: Optional[str] = None

    class Config:
        from_attributes = True
