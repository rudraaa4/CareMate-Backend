from abc import ABC, abstractmethod
from typing import BinaryIO


class FileStorage(ABC):
    """Storage interface — routes and services depend on this, never on a
    concrete backend, so swapping local disk for real object storage later
    (Phase 33+) means writing one new class, not touching every caller."""

    @abstractmethod
    def save(self, storage_key: str, file: BinaryIO) -> None: ...

    @abstractmethod
    def open(self, storage_key: str) -> BinaryIO: ...

    @abstractmethod
    def delete(self, storage_key: str) -> None: ...
