"""The scheduled batch must compose through the production path.

The sprint's central constraint is that a scheduled run is not a second,
quieter way of analysing a Case -- it is the same composition an opened Case
performs. The API wires that service through FastAPI `Depends`, which a
command cannot use, so the factory rebuilds the identical graph from an
engine. These tests pin the two together: if the API grows a collaborator
and the factory does not, a scheduled batch would start composing from less
evidence than the screen does, and the frozen history would quietly diverge
from what Atlas actually showed.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from atlas.alpha.investment_case import api as investment_case_api
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.scheduled_composition import factory as factory_module
from atlas.alpha.scheduled_composition.factory import build_scheduled_composition_service
from atlas.alpha.scheduled_composition.service import ScheduledCompositionService


@pytest.fixture
def service(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'atlas.db'}", future=True)
    return build_scheduled_composition_service(engine)


def _call_keywords(source: str, callee: str) -> set[str]:
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == callee):
            return {keyword.arg for keyword in node.keywords if keyword.arg}
    raise AssertionError(f"no call to {callee} found")


def test_the_factory_builds_a_usable_scheduled_service(service) -> None:
    assert isinstance(service, ScheduledCompositionService)
    assert service.scope() == ()


def test_the_factory_passes_every_collaborator_the_api_passes() -> None:
    """The one test that keeps a scheduled batch honest. Both call sites
    construct `InvestmentCaseCompositionService`; they must agree on what
    a composition is made of."""
    api_source = Path(inspect.getfile(investment_case_api)).parent / "dependencies.py"
    assert (_call_keywords(factory_module.__loader__.get_source(factory_module.__name__),
                           "InvestmentCaseCompositionService")
            == _call_keywords(api_source.read_text(), "InvestmentCaseCompositionService"))


def _constructions(source: str) -> dict[str, set[frozenset[str]]]:
    found: dict[str, set[frozenset[str]]] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            name = f"{node.func.value.id}.{node.func.attr}"
        else:
            continue
        if name[0].isupper():
            found.setdefault(name, set()).add(frozenset(k.arg for k in node.keywords if k.arg))
    return found


def test_each_collaborator_is_constructed_the_way_the_app_constructs_it() -> None:
    """Passing the right collaborators is not enough -- they must be built
    the same way.

    This caught a real defect: the factory built the security share-evidence
    repository without `listing_mics`, which its signature makes optional.
    Composition still ran, but an issuer with more than one listed share
    class (GOOG/GOOGL) resolved no historical share counts, so every prior
    epoch vanished and a Case the app calls EXPENSIVE composed as
    INSUFFICIENT_INPUT -- and the batch wrote that to history as though
    Atlas had concluded it.
    """
    factory = _constructions(factory_module.__loader__.get_source(factory_module.__name__))
    built = {name for name in factory if name.startswith(("Sql", "Alpha", "Case", "Issuer"))}
    assert built, "expected the factory to construct repositories"

    app_shapes: dict[str, set[frozenset[str]]] = {}
    for path in Path("atlas").rglob("dependencies.py"):
        for name, shapes in _constructions(path.read_text()).items():
            if name in built:
                app_shapes.setdefault(name, set()).update(shapes)

    missing = built - set(app_shapes)
    assert not missing, f"the app never constructs: {sorted(missing)}"
    for name in sorted(built):
        assert factory[name] == app_shapes[name], (
            f"{name} is built as {[sorted(s) for s in factory[name]]} here but "
            f"{[sorted(s) for s in app_shapes[name]]} in the app"
        )


def test_no_optional_collaborator_is_left_unwired(service) -> None:
    """Every optional collaborator defaults to `None`, and each `None`
    silently removes evidence: no Change Intelligence, no snapshot written,
    no v3 valuation. A scheduled batch composing with any of them missing
    would record a conclusion Atlas never showed anyone."""
    composition = service._composition_service
    assert isinstance(composition, InvestmentCaseCompositionService)
    optional = [name for name, parameter in
                inspect.signature(InvestmentCaseCompositionService.__init__).parameters.items()
                if parameter.default is None]
    assert optional, "expected the service to still have optional collaborators"
    for name in optional:
        assert getattr(composition, f"_{name}") is not None, f"{name} was left unwired"


def test_the_snapshot_repository_is_shared_with_the_composition_service(service) -> None:
    """The batch reports a snapshot as written by reading the same store
    composition writes to. Two repositories over one database would still
    work, but the shared instance is what makes that reasoning obvious."""
    assert service._snapshot_repository is service._composition_service._snapshot_repository


def test_scope_and_composition_read_the_same_membership(service) -> None:
    """Scope comes from Portfolio and Watchlist; so does composition's own
    ticker resolution. Different stores could disagree about a Case."""
    assert service._portfolio_store is service._composition_service._portfolio_store
    assert service._watchlist_store is service._composition_service._watchlist_store


def test_the_factory_creates_every_table_it_reads(tmp_path) -> None:
    """A dev command runs against whatever database it is pointed at,
    including a fresh one; `sync_table_schema` is how every other command
    handles that."""
    database = tmp_path / "fresh.db"
    engine = create_engine(f"sqlite:///{database}", future=True)
    built = build_scheduled_composition_service(engine)
    assert built.run(scope=[]).attempted == 0
    assert database.exists()


def test_the_factory_imports_no_provider_package() -> None:
    """Composition cannot reach the network, and the wiring must not be the
    thing that hands it a way to."""
    source = factory_module.__loader__.get_source(factory_module.__name__)
    for forbidden in ("business_data_providers", "httpx", "requests", "urllib", "alpha_vantage"):
        assert forbidden not in source
