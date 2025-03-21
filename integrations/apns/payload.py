from typing import Any


class PayloadAlert:
    """A class for alert body initializing."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        title: str | None = None,
        title_localized_key: str | None = None,
        title_localized_args: list[str] | None = None,
        subtitle: str | None = None,
        subtitle_localized_key: str | None = None,
        subtitle_localized_args: list[str] | None = None,
        body: str | None = None,
        body_localized_key: str | None = None,
        body_localized_args: list[str] | None = None,
        launch_image: str | None = None,
    ) -> None:
        self.title = title
        self.title_localized_key = title_localized_key
        self.title_localized_args = title_localized_args
        self.subtitle = subtitle
        self.subtitle_localized_key = subtitle_localized_key
        self.subtitle_localized_args = subtitle_localized_args
        self.body = body
        self.body_localized_key = body_localized_key
        self.body_localized_args = body_localized_args
        self.launch_image = launch_image

    def as_dict(self) -> dict[str, Any]:  # noqa: C901
        """Return body."""
        result: dict[str, Any] = {}

        if self.title:
            result['title'] = self.title
        if self.title_localized_key:
            result['title-loc-key'] = self.title_localized_key
        if self.title_localized_args:
            result['title-loc-args'] = self.title_localized_args

        if self.subtitle:
            result['subtitle'] = self.subtitle
        if self.subtitle_localized_key:
            result['subtitle-loc-key'] = self.subtitle_localized_key
        if self.subtitle_localized_args:
            result['subtitle-loc-args'] = self.subtitle_localized_args

        if self.body:
            result['body'] = self.body
        if self.body_localized_key:
            result['loc-key'] = self.body_localized_key
        if self.body_localized_args:
            result['loc-args'] = self.body_localized_args

        if self.launch_image:
            result['launch-image'] = self.launch_image

        return result


class Payload:
    """A class for payload initializing."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        alert: PayloadAlert | str | None = None,
        badge: int | None = None,
        sound: str | None = None,
        category: str | None = None,
        custom: dict[str, Any] | None = None,
        thread_id: str | None = None,
        content_available: bool = False,
        mutable_content: bool = False,
    ) -> None:
        self.alert = alert
        self.badge = badge
        self.sound = sound
        self.content_available = content_available
        self.category = category
        self.custom = custom
        self.mutable_content = mutable_content
        self.thread_id = thread_id

    def as_dict(self) -> dict[str, Any]:
        """Return body."""
        result: dict[str, dict[str, Any]] = {'aps': {}}

        if self.alert is not None:
            result['aps']['alert'] = self.alert.as_dict() if isinstance(self.alert, PayloadAlert) else self.alert
        if self.badge is not None:
            result['aps']['badge'] = self.badge
        if self.sound is not None:
            result['aps']['sound'] = self.sound
        if self.content_available:
            result['aps']['content-available'] = 1
        if self.mutable_content:
            result['aps']['mutable-content'] = 1
        if self.thread_id is not None:
            result['aps']['thread-id'] = self.thread_id
        if self.category is not None:
            result['aps']['category'] = self.category
        if self.custom:
            result.update(self.custom)

        return result
