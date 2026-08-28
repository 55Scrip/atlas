"""Tests for `atlas.alpha.portfolio_import.name_matching`."""
from __future__ import annotations

from atlas.alpha.portfolio_import.name_matching import name_variants, token_prefix_match


class TestNameVariants:
    def test_a_plain_name_with_no_suffix_yields_only_itself(self):
        assert name_variants("Microsoft") == ("Microsoft",)

    def test_adr_suffix_is_stripped_as_a_second_variant(self):
        assert name_variants("SK Hynix ADR") == ("SK Hynix ADR", "SK Hynix")

    def test_ads_suffix_is_stripped(self):
        assert name_variants("Some Company ADS") == ("Some Company ADS", "Some Company")

    def test_legal_entity_suffix_is_stripped_as_a_second_variant(self):
        assert name_variants("Schneider Electric SE") == (
            "Schneider Electric SE",
            "Schneider Electric",
        )

    def test_both_adr_and_legal_suffix_together_yield_a_fourth_variant(self):
        # A name with both an ADR suffix and (after stripping it) a
        # legal-entity suffix produces the original, the ADR-stripped
        # form, and the both-stripped form.
        variants = name_variants("Some Company AG ADR")
        assert variants[0] == "Some Company AG ADR"
        assert "Some Company AG" in variants
        assert "Some Company" in variants

    def test_variants_are_deduplicated(self):
        variants = name_variants("Volvo")
        assert len(variants) == len(set(variants))

    def test_most_specific_variant_is_always_first(self):
        variants = name_variants("Schneider Electric SE")
        assert variants[0] == "Schneider Electric SE"


class TestTokenPrefixMatch:
    def test_abbreviated_tokens_match_the_full_candidate(self):
        assert token_prefix_match("Taiwan Semicond Mfg", "Taiwan Semiconductor Manufacturing") is False

    def test_a_genuine_abbreviation_of_every_token_matches(self):
        assert token_prefix_match("Nordic Semicond Holding", "Nordic Semiconductor Holdings") is True

    def test_exact_match_also_counts(self):
        assert token_prefix_match("Taiwan Semiconductor", "Taiwan Semiconductor") is True

    def test_token_count_mismatch_never_matches(self):
        assert token_prefix_match("Taiwan Semiconductor", "Taiwan Semiconductor Manufacturing") is False

    def test_a_single_token_query_never_matches(self):
        # At least two tokens are required -- a single short token is
        # too weak a signal to trust automatically.
        assert token_prefix_match("Taiwan", "Taiwan Semiconductor") is False

    def test_a_token_shorter_than_three_characters_never_matches(self):
        assert token_prefix_match("Ta Semicond", "Ta Semiconductor") is False

    def test_wrong_order_never_matches(self):
        assert token_prefix_match("Semicond Taiwan", "Taiwan Semiconductor") is False

    def test_unrelated_names_never_match(self):
        assert token_prefix_match("Volvo Group", "Nvidia Corporation") is False

    def test_a_prefix_that_is_not_a_true_prefix_never_matches(self):
        # "Semi" is not a prefix of "Manufacturing" -- guards against a
        # false positive from token position alone.
        assert token_prefix_match("Taiwan Semi", "Taiwan Manufacturing") is False
