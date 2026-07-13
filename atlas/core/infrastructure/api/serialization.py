"""ADR-004 — API Serialization Standard.

Shared base for every public REST API schema in `atlas/core`: the wire
format (JSON in and out) is camelCase; everything else — domain,
application, persistence, and the Python attribute names on these same
schema classes — stays snake_case. `alias_generator=to_camel` converts
Python attribute names to camelCase for JSON only; `populate_by_name=True`
means a request may still supply the old snake_case key, so existing
callers built against a pre-ADR-004 snake_case body are not broken by this
change. Responses always serialize using the camelCase alias.

This is the one place that decision applies. Every schema module under
`atlas/core/infrastructure/api/**/schemas.py` should subclass `CamelModel`
rather than `pydantic.BaseModel` directly, so the standard stays defined
once rather than redeclared per endpoint.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
