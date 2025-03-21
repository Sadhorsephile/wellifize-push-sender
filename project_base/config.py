from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Envs."""

    APNS_AUTH_KEY: str
    APNS_AUTH_KEY_ID: str
    APNS_TEAM_ID: str
    APNS_USE_SANDBOX: bool = False
    # If present, each request's compared to this value
    AUTH_REQUEST_TOKEN: str | None = None
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str
    FIREBASE_AUTH_URI: str
    FIREBASE_BEARER_TOKEN_TIMEOUT_MINS: int = 60
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_CLIENT_ID: str
    FIREBASE_CLIENT_X509_CERT_URL: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_PRIVATE_KEY_ID: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_TOKEN_URI: str
    FIREBASE_TYPE: str
    FIREBASE_UNIVERSE_DOMAIN: str
    REDIS_URL: str | None = None

    class Config:
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get the settings object."""
    return Settings()  # type: ignore[call-arg]
