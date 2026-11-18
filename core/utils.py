import re
import html


def sanitize_input(value: str) -> str:
    if not isinstance(value, str):
        return value
    value = value.strip()
    value = html.escape(value)
    value = re.sub(r'[\x00-\x1F\x7F]', '', value)
    return value


def sanitize_email(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value.strip().lower()