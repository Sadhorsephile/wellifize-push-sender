import json
from enum import StrEnum
from logging import Logger

import httpx

from fastapi import status

from .credentials import TokenCredentials
from .errors import (
    AnotherError,
    APNSServiceError,
    BadDeviceTokenError,
    ExpiredProviderTokenError,
    ExpiredTokenError,
    TooManyRequestsError,
    UnregisteredError,
)
from .payload import Payload


class NotificationType(StrEnum):
    """Push types."""

    VOIP = 'voip'


class APNSClient:
    """Client class for Apple Push Notification service."""

    SANDBOX_SERVER = 'https://api.sandbox.push.apple.com:443'
    PRODUCTION_SERVER = 'https://api.push.apple.com:443'

    def __init__(self, logger: Logger, credentials: TokenCredentials, *, use_sandbox: bool = False) -> None:
        self._logger = logger
        self._credentials = credentials
        self._use_sandbox = use_sandbox

    def send_notification(
        self, device_token: str, payload: Payload, *, topic: str | None = None, expiration: int | None = None
    ) -> None:
        """Send push.

        docs: https://developer.apple.com/documentation/usernotifications
        /sending-notification-requests-to-apns
        """
        payload_json = json.dumps(payload.as_dict(), separators=(',', ':')).encode()
        headers = self._get_headers(topic, expiration)

        url = (self.SANDBOX_SERVER if self._use_sandbox else self.PRODUCTION_SERVER) + f'/3/device/{device_token}'

        with httpx.Client(http2=True) as c:
            try:
                resp = c.post(url, json=payload_json, headers=headers)
            except httpx.HTTPError as err:
                self._logger.exception('APNS error')
                raise APNSServiceError from err

        if resp.status_code == status.HTTP_200_OK:
            return

        try:
            reason = resp.json()['reason']
        except (json.JSONDecodeError, KeyError) as err:
            self._logger.exception(f'APNS error with response: {resp.text}')
            raise APNSServiceError from err

        if reason == 'BadDeviceToken':
            raise BadDeviceTokenError
        if reason == 'ExpiredProviderToken':
            raise ExpiredProviderTokenError
        if reason == 'ExpiredToken':
            raise ExpiredTokenError
        if reason == 'Unregistered':
            raise UnregisteredError
        if reason == 'TooManyRequests':
            raise TooManyRequestsError
        raise AnotherError(reason)

    def _get_headers(self, topic: str | None = None, expiration: int | None = None) -> dict:
        """Return headers for a request."""
        headers = {}

        if topic:
            inferred_push_type = None
            headers['apns-topic'] = topic

            if topic.endswith('.' + NotificationType.VOIP):
                inferred_push_type = NotificationType.VOIP

            if inferred_push_type:
                headers['apns-push-type'] = inferred_push_type

        if expiration is not None:
            headers['apns-expiration'] = str(expiration)

        headers['authorization'] = 'bearer ' + self._credentials.get_token()
        return headers
