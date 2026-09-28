"""Local filesystem document storage for development.

Adapter boundary: document-domain logic (upload validation, extraction,
metadata persistence) depends only on ``save``/``read``/``delete``
semantics. A future Supabase Storage (or other) backend can replace
``LocalFileStorage`` without touching that logic.

Files live under ``<local_storage_dir>/`` (default ``data/uploads/``,
relative to the backend working directory). Stored paths are always
relative, forward-slash separated, and confined to the storage root —
path traversal in requirement keys or filenames is rejected.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class DocumentStorage(Protocol):
    """Storage backend contract for uploaded document bytes."""

    def save(self, storage_path: str, content: bytes) -> str:
        """Persist content, return the canonical storage path."""
        ...

    def read(self, storage_path: str) -> bytes:
        """Read content back. Raises FileNotFoundError when absent."""
        ...

    def delete(self, storage_path: str) -> bool:
        """Best-effort delete. Returns True when a file was removed."""
        ...


class LocalFileStorage:
    """Filesystem-backed DocumentStorage rooted at a base directory."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_path: str) -> Path:
        candidate = (self.base_dir / storage_path).resolve()
        root = self.base_dir.resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError(f"Storage path escapes root: {storage_path!r}")
        return candidate

    def save(self, storage_path: str, content: bytes) -> str:
        target = self._resolve(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_path.replace("\\", "/")

    def read(self, storage_path: str) -> bytes:
        return self._resolve(storage_path).read_bytes()

    def delete(self, storage_path: str) -> bool:
        try:
            self._resolve(storage_path).unlink()
            return True
        except FileNotFoundError:
            return False


@lru_cache
def get_storage() -> LocalFileStorage:
    """Get the configured document storage backend (local filesystem)."""
    return LocalFileStorage(get_settings().local_storage_dir)
