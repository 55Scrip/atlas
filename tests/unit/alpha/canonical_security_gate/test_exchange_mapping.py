"""`exchange_mapping.map_exchange_display_name_to_mic` -- Sprint O."""
from __future__ import annotations

from atlas.alpha.canonical_security_gate.exchange_mapping import map_exchange_display_name_to_mic


def test_known_exchange_maps_to_its_real_mic() -> None:
    assert map_exchange_display_name_to_mic("NASDAQ").value == "XNAS"
    assert map_exchange_display_name_to_mic("NYSE").value == "XNYS"


def test_case_and_whitespace_insensitive() -> None:
    assert map_exchange_display_name_to_mic("  nasdaq  ").value == "XNAS"


def test_unknown_exchange_returns_none_never_a_guess() -> None:
    assert map_exchange_display_name_to_mic("SOME_UNKNOWN_EXCHANGE") is None


def test_none_input_returns_none() -> None:
    assert map_exchange_display_name_to_mic(None) is None
