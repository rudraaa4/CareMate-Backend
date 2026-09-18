import shutil
from pathlib import Path
from typing import BinaryIO

from app.storage.base import FileStorage

# backend/uploads — resolved relative to this file, not the process's cwd,
# so it's correct regardless of where uvicorn/pytest happens to be launched
# from. Gitignored since Phase 0.
DEFAULT_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


class LocalFileStorage(FileStorage):
    def __init__(self, base_dir: Path = DEFAULT_UPLOAD_DIR):
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_key: str) -> Path:
        """storage_key is always server-generated (uuid4 hex + a whitelisted
        extension — see documents.py), never derived from client input, so
        traversal via storage_key isn't reachable through normal use. This
        containment check is defense in depth, not the primary defense."""
        path = (self.base_dir / storage_key).resolve()
        if path.parent != self.base_dir:
            raise ValueError(f"Refusing to use storage key outside upload dir: {storage_key!r}")
        return path

    def save(self, storage_key: str, file: BinaryIO) -> None:
        with open(self._resolve(storage_key), "wb") as destination:
            shutil.copyfileobj(file, destination)

    def open(self, storage_key: str) -> BinaryIO:
        return open(self._resolve(storage_key), "rb")

    def delete(self, storage_key: str) -> None:
        self._resolve(storage_key).unlink(missing_ok=True)
