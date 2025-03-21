from datetime import UTC, datetime
from typing import Protocol, Self

from redis import Redis


class CacheRepository(Protocol):
    """A protocol for cache storing."""

    def delete(self, key: str) -> None:
        """Delete value by key."""

    def get(self, key: str) -> str | None:
        """Get value by key."""

    def set(self, key: str, value: str, expires_at: datetime) -> None:
        """Set value by key with expiration time."""


class LocalCacheRepository:
    """Local singletone implementation of CacheRepository protocol based on dict."""

    _instance = None

    def __new__(cls) -> Self:
        """Singletone class."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, datetime]] = {}

    def delete(self, key: str) -> None:
        """Delete value by key."""
        self._data.pop(key, None)

    def get(self, key: str) -> str | None:
        """Get value by key."""
        value, expires_at = self._data.get(key, (None, None))

        if value is not None and expires_at and expires_at < datetime.now(UTC):
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, expires_at: datetime) -> None:
        """Set value by key with expiration time."""
        self._data[key] = (value, expires_at)


class RedisCacheRepository:
    """Redis implementation of CacheRepository protocol."""

    def __init__(self, connection: Redis) -> None:
        self._con = connection

    def delete(self, key: str) -> None:
        """Delete value by key."""
        self._con.delete(key)

    def get(self, key: str) -> str | None:
        """Get value by key."""
        return self._con.get(key)  # type: ignore[return-value]

    def set(self, key: str, value: str, expires_at: datetime) -> None:
        """Set value by key with expiration time."""
        self._con.set(key, value, exat=expires_at)
