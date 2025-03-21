from typing import NewType, Protocol

from redis import Redis

Token = NewType('Token', str)
UserId = NewType('UserId', str)


class TokenRepository(Protocol):
    """A protocol for tokens storing."""

    def add(self, user_id: UserId, token: Token) -> None:
        """Save token."""

    def delete(self, user_id: UserId, token: Token) -> None:
        """Delete specified token."""

    def get_all_by_user_id(self, user_id: UserId) -> list[Token]:
        """Get all user tokens by user_id."""


class RedisTokenRepository:
    """Redis implementation of TokenRepository protocol."""

    def __init__(self, connection: Redis, key_pattern: str) -> None:
        self.key_pattern = key_pattern
        self._con = connection

    def add(self, user_id: UserId, token: Token) -> None:
        """Save token."""
        key = self.key_pattern.format(user_id=user_id)
        self._con.sadd(key, token)

    def delete(self, user_id: UserId, token: Token) -> None:
        """Delete specified token."""
        key = self.key_pattern.format(user_id=user_id)
        self._con.srem(key, token)

    def get_all_by_user_id(self, user_id: UserId) -> set[Token]:
        """Get all user tokens by user_id."""
        key = self.key_pattern.format(user_id=user_id)
        return self._con.smembers(key)  # type: ignore[return-value]
