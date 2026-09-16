"""The opaque boundary a client carries between History pages.

History is append-only and rows can also be retracted, so an offset is the
wrong instrument: "skip 25" stops meaning the same thing the moment a row
enters or leaves the visible set, and a reader silently loses or repeats an
analysis. A cursor names a *position in the ordering* instead, so the next
page resumes exactly after the last row the client actually saw, whatever
has happened to the rows around it since.

The cursor carries the three values the history is ordered by and nothing
else. In particular it carries no identity, no scope and no permission:
scope is re-derived from live membership on every request, and the cursor is
only ever allowed to narrow a result, never to widen one. A client that
invented a cursor for someone else's Case would still receive only its own.

It is opaque on purpose. The encoding is this module's business, `VERSION`
lets it change without stranding a client mid-traversal, and nothing outside
here -- least of all the frontend -- may parse it.
"""
from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass

__all__ = ["VERSION", "HistoryCursor", "InvalidCursorError", "decode_cursor", "encode_cursor"]

#: Bumped only when the ordering the cursor describes changes. An older
#: cursor is then refused rather than silently misread against new ordering.
VERSION = 1


class InvalidCursorError(ValueError):
    """The cursor is not one this server issued. Distinct from a cursor that
    is well-formed but now points past the end of a shortened history: that
    is an ordinary, empty result, not an error."""


@dataclass(frozen=True)
class HistoryCursor:
    """A position in the history ordering: the row last returned, named by
    exactly the three values that order it."""

    captured_at: str
    case_id: str
    content_hash: str


def encode_cursor(cursor: HistoryCursor) -> str:
    payload = json.dumps(
        {"v": VERSION, "at": cursor.captured_at, "case": cursor.case_id, "hash": cursor.content_hash},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(raw: str | None) -> HistoryCursor | None:
    """`None` for "start at the beginning". Anything that is not a cursor
    this server issued raises, so a client learns its request was wrong
    rather than silently receiving page one again -- which would loop a
    traversal forever."""
    if raw is None or raw == "":
        return None
    try:
        padded = raw + "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise InvalidCursorError("The history cursor is not readable.") from error
    if not isinstance(payload, dict):
        raise InvalidCursorError("The history cursor is not readable.")
    if payload.get("v") != VERSION:
        raise InvalidCursorError(
            f"The history cursor was issued for an older ordering (version {payload.get('v')!r}).")
    values = (payload.get("at"), payload.get("case"), payload.get("hash"))
    if not all(isinstance(value, str) and value for value in values):
        raise InvalidCursorError("The history cursor is missing its position.")
    captured_at, case_id, content_hash = values
    return HistoryCursor(captured_at=captured_at, case_id=case_id, content_hash=content_hash)
