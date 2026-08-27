"""Delimiter detection and column splitting for the unified import
pipeline -- generalizes the frontend's old `parser.ts` (hard-capped at
2 columns) to real broker exports (Company, Ticker, Quantity, Price,
Value, Weight, Currency), while keeping today's informal 2-column paste
("Microsoft - 6,14%", no header) working exactly as before.

One delimiter is chosen for the whole input from its first non-blank
line, then applied consistently to every line -- a real export uses one
delimiter throughout, so detecting it once avoids the ambiguity a
per-line decision would reintroduce.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from atlas.alpha.portfolio_import.column_detection import detect_header
from atlas.alpha.portfolio_import.models import ColumnRole

_DASH_DELIMITER_PATTERN = re.compile(r"\s[-–—]\s")
_NUMERIC_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")
_CURRENCY_NOISE_PATTERN = re.compile(r"[%$€£]|\bkr\b|\bsek\b|\busd\b|\beur\b", re.IGNORECASE)
_WHITESPACE_PATTERN = re.compile(r"[\s  ]+")


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


def parse_input(raw_text: str) -> ParsedInput:
    lines = [
        (index + 1, line.strip())
        for index, line in enumerate(raw_text.split("\n"))
        if line.strip() != ""
    ]
    if not lines:
        return ParsedInput((), False)

    delimiter = _detect_delimiter(lines[0][1])
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
