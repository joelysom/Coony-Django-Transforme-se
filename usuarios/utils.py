from django.utils.text import slugify


def normalize_username(value: str) -> str:
    """Convert raw input into a slug suitable for Usuario.username."""
    raw = (value or '').strip()
    if raw.startswith('@'):
        raw = raw[1:]
    slug = slugify(raw)
    return slug[:60]
