"""
Database tables.

Design principle: the database stores only METADATA (who owns what, where the
bytes live, how big they are). The actual file bytes live in S3 / on disk.
This separation is what lets the system scale.
"""
import datetime

from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from .database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    storage_used = Column(BigInteger, default=0)        # bytes currently used
    storage_quota = Column(BigInteger, nullable=False)  # bytes allowed
    created_at = Column(DateTime, default=_now)

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="owner", cascade="all, delete-orphan")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime, default=_now)

    owner = relationship("User", back_populates="folders")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)          # location of bytes in storage
    size = Column(BigInteger, default=0)             # bytes
    content_type = Column(String, default="application/octet-stream")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    uploaded = Column(Boolean, default=False)        # flipped true after bytes land
    created_at = Column(DateTime, default=_now)

    owner = relationship("User", back_populates="files")
    shares = relationship("Share", back_populates="file", cascade="all, delete-orphan")


class Share(Base):
    """A file shared with another user, or via a public expiring token."""
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    public_token = Column(String, unique=True, index=True, nullable=True)
    permission = Column(String, default="read")      # "read" or "write"
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    file = relationship("File", back_populates="shares")
