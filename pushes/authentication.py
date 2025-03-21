from typing import Annotated

from fastapi import Header, HTTPException, status

from project_base.config import get_settings

settings = get_settings()


def authenticate_request(authorization: Annotated[str | None, Header()] = None) -> None:
    """Compare Authorization header to env."""
    if settings.AUTH_REQUEST_TOKEN and authorization != settings.AUTH_REQUEST_TOKEN:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Authorization code is incorrect')
