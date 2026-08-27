"""The one production guard every `atlas.dev.*` command must call first.

This codebase has no existing "production" concept anywhere -- no
deployment config, no `ATLAS_ENV`, nothing (confirmed by a repo-wide
search before writing this). `ATLAS_ENV` is new, introduced here,
minimal by design: unset or `"development"` allows dev tooling to run;
any other value refuses. Today, since nothing sets it, every dev
command works exactly as it always has -- this only starts mattering
the day something sets `ATLAS_ENV=production`.
"""
from __future__ import annotations

import os


class NotDevelopmentEnvironmentError(RuntimeError):
    """Raised when a dev-only command is invoked outside a development
    environment. Callers should let this propagate to a non-zero exit,
    never swallow it."""


def ensure_development_environment() -> None:
    env = os.environ.get("ATLAS_ENV", "development").strip().lower()
    if env != "development":
        raise NotDevelopmentEnvironmentError(
            f"Refusing to run: ATLAS_ENV={env!r}. This command only runs "
            "when ATLAS_ENV is unset or 'development'."
        )
