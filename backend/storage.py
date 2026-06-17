"""
Storage abstraction — THE key cloud concept in this project.

The browser never streams file bytes through our API server. Instead the API
hands the browser a short-lived **pre-signed URL** and the browser talks
DIRECTLY to the storage layer. That keeps the API stateless and cheap to scale.

Two interchangeable backends implement the same interface:

  * S3Storage    -> real AWS S3 pre-signed PUT/GET URLs (production / cloud)
  * LocalStorage -> disk + HMAC-signed URLs served by our own API (laptop demo)

Because both speak the same "pre-signed URL" language, the frontend code and
the upload flow are IDENTICAL in both environments. You can develop the whole
app offline, then flip STORAGE_BACKEND=s3 and deploy to AWS unchanged.
"""
import abc
import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

from .config import settings


class Storage(abc.ABC):
    @abc.abstractmethod
    def presigned_put(self, key: str, content_type: str, expires: int = 900) -> str:
        ...

    @abc.abstractmethod
    def presigned_get(self, key: str, filename: str, expires: int = 900) -> str:
        ...

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        ...


# --------------------------------------------------------------------------- #
#  AWS S3 backend
# --------------------------------------------------------------------------- #
class S3Storage(Storage):
    def __init__(self):
        import boto3  # imported lazily so local mode needs no AWS libs at runtime
        self.client = boto3.client("s3", region_name=settings.aws_region)
        self.bucket = settings.s3_bucket

    def presigned_put(self, key, content_type, expires=900):
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
        )

    def presigned_get(self, key, filename, expires=900):
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=expires,
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)


# --------------------------------------------------------------------------- #
#  Local disk backend (mimics pre-signed URLs with an HMAC token)
# --------------------------------------------------------------------------- #
class LocalStorage(Storage):
    def __init__(self):
        self.root = os.path.abspath(settings.local_storage_dir)
        os.makedirs(self.root, exist_ok=True)

    def _path(self, key: str) -> str:
        # keys can contain "/", keep the tree on disk
        full = os.path.join(self.root, key)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return full

    def _sign(self, key: str, op: str, expires_at: int) -> str:
        msg = f"{op}:{key}:{expires_at}".encode()
        return hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()

    def make_url(self, key: str, op: str, filename: str, expires: int) -> str:
        expires_at = int(time.time()) + expires
        sig = self._sign(key, op, expires_at)
        query = urlencode({"exp": expires_at, "sig": sig, "name": filename})
        return f"{settings.public_api_url}/api/blob/{op}/{key}?{query}"

    def verify(self, key: str, op: str, expires_at: int, sig: str) -> bool:
        if int(time.time()) > expires_at:
            return False
        expected = self._sign(key, op, expires_at)
        return hmac.compare_digest(expected, sig)

    def presigned_put(self, key, content_type, expires=900):
        return self.make_url(key, "put", "", expires)

    def presigned_get(self, key, filename, expires=900):
        return self.make_url(key, "get", filename, expires)

    def delete(self, key):
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass


def get_storage() -> Storage:
    if settings.storage_backend == "s3":
        return S3Storage()
    return LocalStorage()


storage = get_storage()
