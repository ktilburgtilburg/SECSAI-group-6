from urllib.parse import urlsplit

from secsai_group_6.categories import Category

MAX_URL_LENGTH = 2048


class InvalidInput(ValueError):
    """Unusable client input. The message is safe to show to the client."""


def json_object(body: object) -> dict:
    if not isinstance(body, dict):
        raise InvalidInput(
            "Body must be a JSON object (Content-Type: application/json)"
        )
    return body


def clean_url(value: object) -> str:
    if value is None:
        raise InvalidInput("Field 'url' is required")
    if not isinstance(value, str):
        raise InvalidInput("Field 'url' must be a string")
    url = value.strip()
    if not url:
        raise InvalidInput("Field 'url' must be non-empty")
    if len(url) > MAX_URL_LENGTH:
        raise InvalidInput(f"Field 'url' must be at most {MAX_URL_LENGTH} characters")
    return url


def clean_category(value: object, field: str) -> Category:
    if value is None:
        raise InvalidInput(f"Field '{field}' is required")
    try:
        return Category(value)
    except ValueError:
        allowed = ", ".join(c.value for c in Category)
        raise InvalidInput(f"Field '{field}' must be one of: {allowed}") from None


def redact_url(url: str) -> str:
    """Reduce a URL to scheme://hostname so no private data is stored."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        raise InvalidInput("Field 'url' is not a valid URL") from None
    if parts.scheme not in ("http", "https") or not host:
        raise InvalidInput("Field 'url' must be an http(s) URL")
    return f"{parts.scheme}://{host}"
