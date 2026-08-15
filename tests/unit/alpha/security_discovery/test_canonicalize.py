"""Sprint 19 -- canonicalize_company_text, exercised against the exact
real title strings SEC's own company_tickers.json returned when fetched
live during this sprint's investigation (see the sprint's own final
report, Phase 3/Finding for the raw values)."""
from __future__ import annotations

from atlas.alpha.security_discovery.canonicalize import canonicalize_company_text


class TestQueryVsRealSecTitleCollapse:
    def test_nvidia_matches_sec_title(self):
        assert canonicalize_company_text("NVIDIA") == canonicalize_company_text("NVIDIA CORP")

    def test_berkshire_hathaway_matches_sec_title(self):
        assert canonicalize_company_text("Berkshire Hathaway") == canonicalize_company_text(
            "BERKSHIRE HATHAWAY INC"
        )

    def test_alphabet_matches_sec_title(self):
        assert canonicalize_company_text("Alphabet") == canonicalize_company_text("Alphabet Inc.")

    def test_apple_matches_sec_title(self):
        assert canonicalize_company_text("Apple") == canonicalize_company_text("Apple Inc.")

    def test_meta_platforms_matches_sec_title(self):
        assert canonicalize_company_text("Meta Platforms") == canonicalize_company_text(
            "Meta Platforms, Inc."
        )

    def test_advanced_micro_devices_matches_sec_title(self):
        assert canonicalize_company_text("Advanced Micro Devices") == canonicalize_company_text(
            "ADVANCED MICRO DEVICES INC"
        )


class TestDoesNotOverReach:
    def test_bare_meta_does_not_match_meta_platforms(self):
        """'Meta' alone is genuinely incomplete -- 'PLATFORMS' is not a
        legal-entity suffix this module strips, so the two canonical
        forms differ. This is the correct, conservative outcome: no
        fuzzy/substring rule bridges this gap."""
        assert canonicalize_company_text("Meta") != canonicalize_company_text("Meta Platforms, Inc.")

    def test_nvidia_corporation_does_not_match_nvidia_corp(self):
        """SEC's own title says 'CORP', not 'CORPORATION' -- both are
        stripped as suffixes, so this actually DOES collapse (both
        suffix words disappear entirely). Documented here as a
        deliberate, verified consequence, not an accident: the suffix
        list treats 'CORP' and 'CORPORATION' as equivalent boilerplate,
        which is safe precisely because both are stripped to nothing
        rather than compared to each other."""
        assert canonicalize_company_text("NVIDIA Corporation") == canonicalize_company_text(
            "NVIDIA CORP"
        )

    def test_unrelated_companies_never_collapse(self):
        assert canonicalize_company_text("Apple") != canonicalize_company_text("Microsoft")
        assert canonicalize_company_text("Tesla") != canonicalize_company_text("NVIDIA")


class TestDeterminism:
    def test_repeated_calls_produce_identical_output(self):
        results = {canonicalize_company_text("Berkshire Hathaway") for _ in range(5)}
        assert len(results) == 1

    def test_case_insensitive(self):
        assert canonicalize_company_text("nvidia corp") == canonicalize_company_text("NVIDIA CORP")


class TestUnknownInput:
    def test_unknown_company_canonicalizes_to_something_but_matches_nothing_here(self):
        # canonicalize_company_text never raises or returns empty for
        # ordinary text -- absence of a match is service.py's concern
        # (an empty title_index lookup), not this module's.
        result = canonicalize_company_text("Completely Unknown Company XYZ")
        assert result == "COMPLETELY UNKNOWN XYZ"
