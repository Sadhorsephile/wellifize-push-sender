from typing import Any

from pydantic import BaseModel, model_validator

from .repositories import Token, UserId


class TokenRequestSchema(BaseModel):
    """Schema for token requests."""

    token: Token
    user_id: UserId


class SendPushSchema(BaseModel):
    """A schema for push notifications body."""

    guid: str | None = None
    status: str | None = 'initializing'

    @model_validator(mode='before')
    @classmethod
    def parse_call_object_if_needed(cls, data: Any) -> Any:  # noqa: ANN401
        """Parse 'call' object if guid is missing."""
        if not isinstance(data, dict):
            msg = 'Invalid data'
            raise ValueError(msg)  # noqa: TRY004

        if data.get('guid') is None:
            call = data.get('call') or {}
            data['guid'] = call.get('guid')
            data['status'] = call.get('status')

        return data


class SendPushByTokenSchema(SendPushSchema):
    """A schema for push sending by token."""

    token: Token


class SendPushByUserIdSchema(SendPushSchema):
    """A schema for push sending by user_id."""

    user_id: UserId
