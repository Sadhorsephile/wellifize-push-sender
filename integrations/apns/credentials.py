import time
from datetime import UTC, datetime, timedelta

import jwt

from ..cache import CacheRepository


class TokenCredentials:
    """JWT based authentication.

    docs: https://developer.apple.com/documentation/usernotifications
    /establishing-a-token-based-connection-to-apns
    """

    ACCESS_TOKEN_CACHE_KEY = 'apns_access_token'  # noqa: S105
    ENCRYPTION_ALGORITHM = 'ES256'
    DEFAULT_TOKEN_LIFETIME_MINS = 55

    def __init__(self, cache_storage: CacheRepository, auth_key: str, auth_key_id: str, team_id: str) -> None:
        self._cache_storage = cache_storage
        self._auth_key = auth_key
        self._auth_key_id = auth_key_id
        self._team_id = team_id

    def get_token(self) -> str:
        """Retrieve an access token from the cache or create it."""
        if cached_token := self._cache_storage.get(self.ACCESS_TOKEN_CACHE_KEY):
            return cached_token

        token = self._create_token()
        expires_at = datetime.now(UTC) + timedelta(minutes=self.DEFAULT_TOKEN_LIFETIME_MINS)
        self._cache_storage.set(self.ACCESS_TOKEN_CACHE_KEY, token, expires_at=expires_at)
        return token

    def delete_access_token(self) -> None:
        """Delete the cached access token."""
        self._cache_storage.delete(self.ACCESS_TOKEN_CACHE_KEY)

    def _create_token(self) -> str:
        """Create JWT token."""
        payload = {'iss': self._team_id, 'iat': int(time.time())}
        headers = {'alg': self.ENCRYPTION_ALGORITHM, 'kid': self._auth_key_id}
        return jwt.encode(
            payload, self._auth_key, algorithm=self.ENCRYPTION_ALGORITHM, headers=headers, sort_headers=False
        )
