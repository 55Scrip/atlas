"""Shared locale boundary for Atlas renderers.

Supported locales: "en" (English), "sv" (Swedish).
Unsupported locales raise ValueError.
No translations are implemented. No locale detection. No gettext.
"""

from __future__ import annotations

SUPPORTED_LOCALE_EN = "en"
SUPPORTED_LOCALE_SV = "sv"

_SUPPORTED_LOCALES = frozenset({SUPPORTED_LOCALE_EN, SUPPORTED_LOCALE_SV})


def ensure_supported_locale(locale: str) -> None:
    if locale not in _SUPPORTED_LOCALES:
        raise ValueError(
            f"Unsupported locale: {locale!r}. Supported locales: 'en', 'sv'."
        )
