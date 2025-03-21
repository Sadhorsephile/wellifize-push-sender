class APNSServiceError(Exception):
    """Exception for APNS service errors."""


class BadDeviceTokenError(APNSServiceError):
    """The specified device token is invalid.
    Verify that the request contains a valid token
    and that the token matches the environment.
    """


class ExpiredProviderTokenError(APNSServiceError):
    """The provider token is stale and a new token should be generated."""


class ExpiredTokenError(APNSServiceError):
    """The device token has expired."""


class UnregisteredError(APNSServiceError):
    """The device token is inactive for the specified topic.
    There is no need to send further pushes to the same device token,
    unless your application retrieves the same device token,
    refer to Registering your app with APNs.
    """


class TooManyRequestsError(APNSServiceError):
    """Too many requests were made consecutively to the same device token."""


class AnotherError(APNSServiceError):
    """Another reason."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
