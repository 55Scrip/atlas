"""Delimiter detection, column splitting, and free-form line association
for the unified import pipeline.

Real Avanza Import Fix (2026-08-28): a real broker portfolio page is not
built from a semantic `<table>` -- it's a CSS grid of `<div>`s (name,
share-class badge, daily % change, "Köp"/"Sälj" buttons, market value,
country flag, ...), each its own DOM node. When a user selects and
copies that with the mouse, the browser serializes the selection to
`text/plain` with a line break at each block-level element boundary --
so a single holding's name and its market value land on *separate
lines*, often with one or more noise lines between them (a live-
verified root cause: a hand-constructed semicolon-delimited sample
passing was never proof the real, flattened clipboard shape worked).

Two independent input shapes are handled:
1. A real delimited export (tab/semicolon/comma, one row per line) --
   `_detect_delimiter` finds a real delimiter and the existing header-
   or 2-column-per-line path applies, unchanged.
2. A flattened, no-delimiter paste (the real Avanza case, and the
   informal single-line "AMD 40" / "Microsoft – 6,14%" conventions,
   the latter still going through the dash delimiter above) --
   `_parse_flat_lines` classifies every line and associates a name
   with whichever value line follows it, skipping noise, rather than
   assuming one line is one holding.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from atlas.alpha.portfolio_import.column_detection import detect_header
from atlas.alpha.portfolio_import.models import ColumnRole

_DASH_DELIMITER_PATTERN = re.compile(r"\s[-–—]\s")
_NUMERIC_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")
_CURRENCY_NOISE_PATTERN = re.compile(
    r"[%$€£]|\bkr\b|\bsek\b|\busd\b|\beur\b|\bdkk\b|\bnok\b|\bgbp\b", re.IGNORECASE
)
_WHITESPACE_PATTERN = re.compile(r"[\s  ]+")


def normalize_numeric_text(raw: str) -> str | None:
    """Strips currency symbols/codes and whitespace (including the
    space Swedish exports use as a thousands separator), then
    disambiguates '.' vs ',' as the decimal separator by whichever
    occurs last -- "1 234,50" and "1,234.50" both normalize to
    "1234.50"."""
    text = _CURRENCY_NOISE_PATTERN.sub("", raw)
    text = _WHITESPACE_PATTERN.sub("", text)
    if not text:
        return None
    negative = text.startswith("-")
    if negative:
        text = text[1:]
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    if not text or not _NUMERIC_PATTERN.match(text):
        return None
    return ("-" + text) if negative else text


def parse_numeric(raw: str) -> float | None:
    normalized = normalize_numeric_text(raw)
    if normalized is None:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def _detect_delimiter(first_line: str) -> str | None:
    if "\t" in first_line:
        return "tab"
    if _DASH_DELIMITER_PATTERN.search(first_line):
        return "dash"
    if ";" in first_line:
        return "semicolon"
    if "," in first_line:
        return "comma"
    return None


def _split_columns(line: str, delimiter: str | None) -> list[str]:
    if delimiter == "tab":
        return [part.strip() for part in line.split("\t")]
    if delimiter == "dash":
        return [part.strip() for part in _DASH_DELIMITER_PATTERN.split(line)]
    if delimiter == "semicolon":
        return [part.strip() for part in line.split(";")]
    if delimiter == "comma":
        return [part.strip() for part in line.split(",")]
    tokens = line.strip().split()
    if len(tokens) <= 2:
        return tokens
    return [" ".join(tokens[:-1]), tokens[-1]]


@dataclass(frozen=True)
class RawRow:
    line_number: int
    raw: str
    fields: dict[ColumnRole, str]


@dataclass(frozen=True)
class ParsedInput:
    rows: tuple[RawRow, ...]
    header_detected: bool


# ---------------------------------------------------------------------
# Flat (no-delimiter) line classification and name -> value association
# ---------------------------------------------------------------------


class _LineRole(str, Enum):
    NAME_WITH_VALUE = "NAME_WITH_VALUE"
    PURE_VALUE = "PURE_VALUE"
    NOISE = "NOISE"
    NAME_ONLY = "NAME_ONLY"


@dataclass(frozen=True)
class _ClassifiedLine:
    role: _LineRole
    name: str | None = None
    value_text: str | None = None
    unit: str | None = None  # "PERCENT" | "CURRENCY" | "BARE"
    currency_code: str | None = None


# Broker-UI chrome that must never become a holding name -- action
# buttons, column headers, section labels, account/summary rows. Not
# exhaustive by construction (a denylist never is); the generic "no
# letters and no digits" and "standalone percentage" checks below catch
# most other decoration (flags, arrows, bare "+"/"-") without needing a
# name for every symbol.
_NOISE_WORDS = {
    # Swedish
    "köp", "sälj", "handla", "mer", "visa mer", "detaljer", "info",
    "innehav", "andel", "andel %", "kurs", "värde", "antal", "gav",
    "orderdjup", "graf", "totalt", "summa", "konto", "depå",
    "aktier", "aktier & fonder", "fonder", "portfölj", "portföljöversikt",
    "kontanter", "likvider", "mina innehav", "utveckling", "idag",
    # English
    "buy", "sell", "trade", "more", "details", "holdings", "weight",
    "price", "quantity", "shares", "total", "sum", "account", "cash",
    "overview", "change", "today",
}

_PURE_PERCENT_PATTERN = re.compile(r"^[+-]?\d+(?:[.,]\d+)?\s*%$")
_HAS_ALPHA_PATTERN = re.compile(r"[^\W\d_]", re.UNICODE)
_HAS_DIGIT_PATTERN = re.compile(r"\d")

# The leading integer run is unbounded (`\d+`), not capped at 3 digits --
# a cap would truncate an ungrouped 4+ digit number (e.g. "1234 kr")
# after only 3 digits and misparse the remainder. `\s*$` anchors the
# match to the end of the (stripped) line, which is what lets this
# correctly separate a name from its trailing value even when the name
# itself contains a digit (e.g. "3M 45 937 kr" -> name "3M", value
# "45 937 kr") -- any earlier candidate start position fails the anchor
# because real text still follows it.
_TRAILING_VALUE_PATTERN = re.compile(
    r"(?P<value>-?\d+(?:[   ]\d{3})*(?:[.,]\d+)?\s*"
    r"(?:kr|sek|usd|eur|dkk|nok|gbp|\$|€|£|%)?)\s*$",
    re.IGNORECASE,
)

_CURRENCY_SUFFIX_MAP = {
    "kr": "SEK", "sek": "SEK", "usd": "USD", "$": "USD",
    "eur": "EUR", "€": "EUR", "dkk": "DKK", "nok": "NOK",
    "gbp": "GBP", "£": "GBP",
}


def _currency_from_value_text(value_text: str) -> str | None:
    stripped_lower = value_text.strip().lower()
    for suffix, code in _CURRENCY_SUFFIX_MAP.items():
        if stripped_lower.endswith(suffix):
            return code
    return None


def _classify_line(raw_line: str) -> _ClassifiedLine:
    stripped = raw_line.strip()
    if _PURE_PERCENT_PATTERN.match(stripped):
        # A standalone daily-change indicator ("+2,3%") -- never a
        # weight, never a value. Weight is only ever accepted when it
        # rides along with a name on the same (delimited or trailing-
        # value) line -- see NAME_WITH_VALUE below.
        return _ClassifiedLine(_LineRole.NOISE)
    if stripped.lower() in _NOISE_WORDS:
        return _ClassifiedLine(_LineRole.NOISE)
    if not _HAS_ALPHA_PATTERN.search(stripped) and not _HAS_DIGIT_PATTERN.search(stripped):
        # Pure punctuation/symbols/flag emoji -- decoration, not data.
        return _ClassifiedLine(_LineRole.NOISE)

    match = _TRAILING_VALUE_PATTERN.search(stripped)
    if match and match.group("value").strip():
        value_text = match.group("value").strip()
        name_part = stripped[: match.start()].strip()
        is_percent = value_text.endswith("%")
        currency_code = _currency_from_value_text(value_text)
        unit = "PERCENT" if is_percent else ("CURRENCY" if currency_code else "BARE")
        if name_part:
            return _ClassifiedLine(_LineRole.NAME_WITH_VALUE, name_part, value_text, unit, currency_code)
        if is_percent:
            # A bare "%" line with nothing in front of it -- the same
            # standalone-change-indicator case as above.
            return _ClassifiedLine(_LineRole.NOISE)
        return _ClassifiedLine(_LineRole.PURE_VALUE, None, value_text, unit, currency_code)

    if _HAS_ALPHA_PATTERN.search(stripped):
        return _ClassifiedLine(_LineRole.NAME_ONLY, stripped)
    return _ClassifiedLine(_LineRole.NOISE)


def _value_role(unit: str | None) -> ColumnRole:
    # A bare number or a percentage both mean WEIGHT, matching the
    # long-established informal convention ("AMD 40", "Microsoft -
    # 6,14%") -- a currency-denominated number is the new capability:
    # a real market VALUE, never a weight.
    return ColumnRole.VALUE if unit == "CURRENCY" else ColumnRole.WEIGHT


def _parse_flat_lines(lines: list[tuple[int, str]]) -> list[RawRow]:
    rows: list[RawRow] = []
    pending: tuple[int, str] | None = None  # (line_number, name)

    def flush_pending() -> None:
        nonlocal pending
        if pending is not None:
            p_line_number, p_name = pending
            rows.append(
                RawRow(line_number=p_line_number, raw=p_name, fields={ColumnRole.COMPANY_NAME: p_name})
            )
            pending = None

    for line_number, raw_line in lines:
        classified = _classify_line(raw_line)

        if classified.role == _LineRole.NAME_WITH_VALUE:
            flush_pending()
            assert classified.name is not None and classified.value_text is not None
            fields: dict[ColumnRole, str] = {
                ColumnRole.COMPANY_NAME: classified.name,
                _value_role(classified.unit): classified.value_text,
            }
            if classified.currency_code is not None:
                fields[ColumnRole.CURRENCY] = classified.currency_code
            rows.append(RawRow(line_number=line_number, raw=raw_line.strip(), fields=fields))

        elif classified.role == _LineRole.PURE_VALUE:
            if pending is not None:
                p_line_number, p_name = pending
                assert classified.value_text is not None
                fields = {ColumnRole.COMPANY_NAME: p_name, ColumnRole.VALUE: classified.value_text}
                if classified.currency_code is not None:
                    fields[ColumnRole.CURRENCY] = classified.currency_code
                rows.append(
                    RawRow(
                        line_number=p_line_number,
                        raw=f"{p_name} / {raw_line.strip()}",
                        fields=fields,
                    )
                )
                pending = None
            # No pending name to attach this value to -- an orphan
            # fragment (e.g. a totals row's value with its label
            # already filtered as noise). Nothing honest to do with it
            # but drop it; it was never a holding on its own.

        elif classified.role == _LineRole.NAME_ONLY:
            flush_pending()
            assert classified.name is not None
            pending = (line_number, classified.name)

        # NOISE: skip entirely, never disturbs a pending name.

    flush_pending()
    return rows


def parse_input(raw_text: str) -> ParsedInput:
    lines = [
        (index + 1, line.strip())
        for index, line in enumerate(raw_text.split("\n"))
        if line.strip() != ""
    ]
    if not lines:
        return ParsedInput((), False)

    delimiter = _detect_delimiter(lines[0][1])

    if delimiter is None:
        # No real delimiter anywhere in the block -- either the
        # informal single-line convention ("AMD 40") or a flattened,
        # multi-line-per-holding broker-page copy. One classifier
        # handles both; see module docstring.
        return ParsedInput(tuple(_parse_flat_lines(lines)), False)

    header_roles = detect_header(_split_columns(lines[0][1], delimiter))
    header_detected = header_roles is not None
    data_lines = lines[1:] if header_detected else lines

    rows: list[RawRow] = []
    for line_number, line in data_lines:
        columns = _split_columns(line, delimiter)
        if header_roles is not None:
            roles = header_roles
        elif len(columns) == 2:
            # Legacy headerless convention: name, weight.
            roles = [ColumnRole.COMPANY_NAME, ColumnRole.WEIGHT]
        elif len(columns) == 1:
            roles = [ColumnRole.COMPANY_NAME]
        else:
            roles = [None] * len(columns)
        fields = {
            role: value
            for role, value in zip(roles, columns)
            if role is not None and value != ""
        }
        rows.append(RawRow(line_number=line_number, raw=line, fields=fields))

    return ParsedInput(tuple(rows), header_detected)
