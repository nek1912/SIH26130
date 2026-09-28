"""Document storage adapter boundary — local filesystem for development."""

from app.storage.local import DocumentStorage, LocalFileStorage, get_storage

__all__ = ["DocumentStorage", "LocalFileStorage", "get_storage"]
