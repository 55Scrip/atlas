import json

from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.evidence import EvidenceInput, EvidenceClaim, EvidenceSource
from atlas.profile import InvestorProfileEngine, RiskTolerance
from atlas.providers import MockCompanyAnalysisProvider
from atlas.watchlist_review import (
    WatchlistReviewEngine,
    WatchlistReviewRating,
    render_watchlist_review,
    watchlist_review_input_from_mapping,
)


def test_watchlist_review_includes_bottom_line_and_rating():
    report = WatchlistReviewEngine().review(_review_input())
    rendered = render_watchlist_review(report)

    assert "Bottom Line" in rendered
    assert "Atlas Watchlist Rating:" in rendered
    assert report.atlas_rating in set(WatchlistReviewRating)


def test_weak_evidence_does_not_make_idea_highly_rated():
    report = WatchlistReviewEngine().review(
        watchlist_review_input_from_mapping(
            {
                "name": "Weak Evidence Watchlist",
                "tickers": ["NVDA"],
                "ideas": ["viral AI chart"],
                "evidence": {
                    "viral AI chart": {
                        "source": "screenshot",
                        "claim": "A screenshot claims a dramatic change.",
                    }
                },
            },
            provider=MockCompanyAnalysisProvider(),
        )
    )
    idea = next(item for item in report.items if item.name == "viral AI chart")

    assert idea.requires_better_evidence is True
    assert idea.appears_relevant is False


def test_social_media_driven_ideas_require_better_evidence():
    report = WatchlistReviewEngine().review(
        watchlist_review_input_from_mapping(
            {
                "name": "Social Watchlist",
                "tickers": ["MSFT"],
                "ideas": ["AI demand collapse"],
                "evidence": {
                    "AI demand collapse": {
                        "source": "social media post",
                        "claim": "A social post claims demand collapsed.",
                    }
                },
            },
            provider=MockCompanyAnalysisProvider(),
        )
    )

    rendered = render_watchlist_review(report)

    assert "Ideas Requiring Better Evidence" in rendered
    assert "not strong enough for a high-confidence assessment" in rendered
    assert "AI demand collapse" in rendered


def test_investor_profile_affects_watchlist_fit_section():
    engine = InvestorProfileEngine()
    profile = engine.update_profile(
        engine.create_default_profile(),
        risk_tolerance=RiskTolerance.CONSERVATIVE,
    )

    report = WatchlistReviewEngine().review(
        watchlist_review_input_from_mapping(
            {"name": "Profile Watchlist", "tickers": ["NVDA", "AMD"]},
            provider=MockCompanyAnalysisProvider(),
            investor_profile=profile,
        )
    )
    rendered = render_watchlist_review(report)

    assert "Fit With Investor Profile" in rendered
    assert "Risk Tolerance: Conservative" in rendered


def test_noisy_watchlists_are_identified_calmly():
    report = WatchlistReviewEngine().review(
        watchlist_review_input_from_mapping(
            {
                "name": "Noisy Watchlist",
                "tickers": ["ZZZ", "YYY"],
                "ideas": ["unverified short video trend"],
                "evidence": {
                    "unverified short video trend": {
                        "source": "TikTok",
                        "claim": "A short video claims a sure trend.",
                    }
                },
            },
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert report.atlas_rating in {
        WatchlistReviewRating.NOISY,
        WatchlistReviewRating.UNCLEAR,
    }
    assert any(item.potential_noise for item in report.items)


def test_suggested_questions_are_only_material():
    report = WatchlistReviewEngine().review(_review_input())
    questions = _section_summaries(report, "Suggested Questions")

    assert questions
    assert all(
        any(marker in question.lower() for marker in ("long-term", "portfolio", "source"))
        for question in questions
    )


def test_watchlist_review_avoids_forbidden_instruction_language():
    rendered = render_watchlist_review(WatchlistReviewEngine().review(_review_input()))

    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert " Buy " not in rendered
    assert " Sell " not in rendered
    assert "Guaranteed" not in rendered
    assert "Risk-free" not in rendered
    assert "Sure thing" not in rendered


def test_language_and_evidence_layers_are_used():
    report = WatchlistReviewEngine().review(_review_input())

    assert report.language_report is not None
    assert "Watchlist Review Engine" in report.language_report.engines_used
    assert all(item.evidence_assessment for item in report.items)


def test_watchlist_review_cli_supports_file_and_demo_mode(tmp_path):
    runner = CliRunner()
    demo_result = runner.invoke(app, ["watchlist", "review"])

    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps({"name": "CLI Watchlist", "tickers": ["NVDA", "AMD"]}),
        encoding="utf-8",
    )
    file_result = runner.invoke(app, ["watchlist", "review", str(path)])

    assert demo_result.exit_code == 0
    assert "Atlas Watchlist Review" in demo_result.output
    assert file_result.exit_code == 0
    assert "CLI Watchlist" in file_result.output


def _review_input():
    return watchlist_review_input_from_mapping(
        {
            "name": "AI Watchlist",
            "tickers": ["NVDA", "AMD", "MSFT"],
            "ideas": ["AI power bottleneck"],
            "evidence": {
                "AI power bottleneck": {
                    "source": "social media post",
                    "claim": "Social posts claim AI power constraints are worsening.",
                }
            },
        },
        provider=MockCompanyAnalysisProvider(),
    )


def _section_summaries(report, title: str) -> tuple[str, ...]:
    for section in report.sections:
        if section.title == title:
            return tuple(item.summary for item in section.observations)
    return ()
