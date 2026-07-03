"""Sprint 205 guardrail tests for atlas/suitability/ package audit.

Verifies:
- All 7 public exports remain importable
- check_suitability_assessment is not an active export of atlas.suitability
- atlas/suitability/ does not import atlas.providers
- atlas/suitability/ does not import atlas.cli
- atlas/suitability/ does not import atlas.database / atlas.services / atlas.models
- atlas.suitability is importable as a package
"""
import importlib.util


def test_suitability_package_importable_sprint205():
    import atlas.suitability

    assert atlas.suitability is not None


def test_suitability_all_exports_sprint205():
    import atlas.suitability

    expected = {
        "OverallSuitability",
        "SuitabilityAssessment",
        "SuitabilityEngine",
        "SuitabilityFactor",
        "SuitabilityInput",
        "SuitabilityMismatch",
        "render_suitability_assessment",
    }
    assert set(atlas.suitability.__all__) == expected


def test_suitability_overall_suitability_importable_sprint205():
    from atlas.suitability import OverallSuitability

    assert OverallSuitability.EXCELLENT_FIT is not None
    assert OverallSuitability.GOOD_FIT is not None
    assert OverallSuitability.NEUTRAL is not None
    assert OverallSuitability.POOR_FIT is not None


def test_suitability_engine_importable_sprint205():
    from atlas.suitability import SuitabilityEngine

    assert callable(SuitabilityEngine)


def test_suitability_input_importable_sprint205():
    from atlas.suitability import SuitabilityInput

    assert SuitabilityInput is not None


def test_suitability_assessment_importable_sprint205():
    from atlas.suitability import SuitabilityAssessment

    assert SuitabilityAssessment is not None


def test_render_suitability_assessment_importable_sprint205():
    from atlas.suitability import render_suitability_assessment

    assert callable(render_suitability_assessment)


def test_check_suitability_assessment_not_exported_sprint205():
    import atlas.suitability

    assert not hasattr(atlas.suitability, "check_suitability_assessment"), (
        "check_suitability_assessment must not be an active export of atlas.suitability"
    )
    assert "check_suitability_assessment" not in atlas.suitability.__all__


def test_suitability_engine_no_provider_import_sprint205():
    source = importlib.util.find_spec("atlas.suitability.engine").origin
    with open(source) as f:
        content = f.read()
    assert "atlas.providers" not in content
    assert "from atlas.providers" not in content
    assert "YahooFinanceProvider" not in content


def test_suitability_engine_no_cli_import_sprint205():
    source = importlib.util.find_spec("atlas.suitability.engine").origin
    with open(source) as f:
        content = f.read()
    assert "atlas.cli" not in content
    assert "from atlas.cli" not in content


def test_suitability_engine_no_database_import_sprint205():
    source = importlib.util.find_spec("atlas.suitability.engine").origin
    with open(source) as f:
        content = f.read()
    assert "atlas.database" not in content
    assert "atlas.services" not in content
    assert "atlas.models" not in content
