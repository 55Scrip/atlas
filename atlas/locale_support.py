"""Shared locale boundary for Atlas renderers.

Only "en" is currently supported. Unsupported locales raise ValueError.
No translations are implemented. No locale detection. No gettext.
"""

from __future__ import annotations

SUPPORTED_LOCALE_EN = "en"


def ensure_supported_locale(locale: str) -> None:
    if locale != SUPPORTED_LOCALE_EN:
        raise ValueError(
            f"Unsupported locale: {locale!r}. Only 'en' is currently supported."
        )
