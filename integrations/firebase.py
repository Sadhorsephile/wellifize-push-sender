from datetime import UTC, datetime, timedelta
from logging import Logger
from typing import ClassVar

import httpx
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2.service_account import Credentials

from fastapi import status

from project_base.config import get_settings

from .cache import CacheRepository

settings = get_settings()


class FireBaseServiceError(Exception):
    """Exception for FireBase service errors."""


class FireBaseInvalidRequestError(Exception):
    """Exception for FireBase FCM token not found errors."""


class FireBaseFCMTokenNotFoundError(Exception):
    """Exception for FireBase FCM token not found errors."""


class FireBaseTokenError(Exception):
    """Exception for FireBase token errors."""


class FireBase:
    """Class for sending FireBase messages."""

    ACCESS_TOKEN_KEY = 'firebase_access_token'  # noqa: S105
    FCM_URL = f'https://fcm.googleapis.com/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send'
    SCOPES: ClassVar[list[str]] = ['https://www.googleapis.com/auth/firebase.messaging']

    def __init__(self, cache_storage: CacheRepository, logger: Logger) -> None:
        self._cache_storage = cache_storage
        self._logger = logger

    def send_message(
        self, *, fcm_token: str, title: str | None, message: str | None, extra_data: dict[str, str | None] | None = None
    ) -> None:
        """Send an HTTP request to FireBase with given message."""
        common_message = self._build_common_message(fcm_token, title, message, extra_data)

        headers = {
            'Authorization': 'Bearer ' + self._get_access_token(),
            'Content-Type': 'application/json; UTF-8',
        }

        with httpx.Client() as c:
            try:
                response = c.post(self.FCM_URL, json=common_message, headers=headers)
            except httpx.HTTPError as err:
                self._logger.exception('Firebase error')
                raise FireBaseServiceError from err

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self._logger.error(f'Firebase error with response: {response.text}')
            raise FireBaseFCMTokenNotFoundError
        if response.status_code == status.HTTP_404_NOT_FOUND:
            self._logger.error(f'Firebase error with response: {response.text}')
            raise FireBaseFCMTokenNotFoundError
        if response.status_code != status.HTTP_200_OK:
            self._logger.error(f'Firebase error with response: {response.text}')
            raise FireBaseTokenError

    def delete_access_token(self) -> None:
        """Delete the cached access token."""
        self._cache_storage.delete(self.ACCESS_TOKEN_KEY)

    def _get_access_token(self) -> str:
        """Retrieve an access token and put it into the cache."""
        if cached_token := self._cache_storage.get(self.ACCESS_TOKEN_KEY):
            return cached_token

        google_credentials = {
            'auth_provider_x509_cert_url': settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
            'auth_uri': settings.FIREBASE_AUTH_URI,
            'client_email': settings.FIREBASE_CLIENT_EMAIL,
            'client_id': settings.FIREBASE_CLIENT_ID,
            'client_x509_cert_url': settings.FIREBASE_CLIENT_X509_CERT_URL,
            'private_key': settings.FIREBASE_PRIVATE_KEY,
            'private_key_id': settings.FIREBASE_PRIVATE_KEY_ID,
            'project_id': settings.FIREBASE_PROJECT_ID,
            'token_uri': settings.FIREBASE_TOKEN_URI,
            'type': settings.FIREBASE_TYPE,
            'universe_domain': settings.FIREBASE_UNIVERSE_DOMAIN,
        }
        creds = Credentials.from_service_account_info(google_credentials, scopes=self.SCOPES)
        request = google_requests.Request()

        try:
            creds.refresh(request)
        except GoogleAuthError as err:
            self._logger.exception('Firebase error')
            raise FireBaseServiceError from err

        expires_at = (
            creds.expiry
            if creds.expiry
            else datetime.now(UTC) + timedelta(minutes=settings.FIREBASE_BEARER_TOKEN_TIMEOUT_MINS)
        )
        expires_at -= timedelta(minutes=1)
        self._cache_storage.set(self.ACCESS_TOKEN_KEY, creds.token, expires_at=expires_at)
        return creds.token

    def _build_common_message(
        self, fcm_token: str, title: str | None, message: str | None, extra_data: dict[str, str | None] | None = None
    ) -> dict:
        """Construct common notification message."""
        msg = {'token': fcm_token, 'notification': {}}

        if title:
            msg['notification']['title'] = title  # type: ignore[index]
        if message:
            msg['notification']['body'] = message  # type: ignore[index]
        if extra_data:
            msg['data'] = extra_data
        return {'message': msg}
