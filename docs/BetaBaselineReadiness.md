# Atlas Beta Baseline — Release Readiness Review

**Type:** Two-pass review. Pass 1 was review-only (no modifications). Pass 2 implemented the two Required Actions from Pass 1's architecture review, strictly scoped to dependency declaration and documentation accuracy, then re-verified. No domain code, no API behavior, and no legacy consolidation were touched in either pass.
**Scope:** The Beta Baseline — API-001 (Decision Capture), API-002 (Decision Context), and the surrounding `atlas/core/` Clean Architecture layer — evaluated in the context of the full repository.
**No commits or tags were created in either pass.**

---

## Executive Summary

**Pass 1** found the proposed baseline itself (`atlas/core/`) in excellent shape — fully isolated, Clean Architecture boundaries verified, zero lint findings, full suite passing — but identified two blocking issues in the repository's shared entry points: an undeclared test dependency that broke the documented clean-install path, and architectural guidance actively directing new work to the wrong location.

**Pass 2** resolved both, within the scope specified by the architecture review (dependency declaration, setup/architecture documentation, and this report — nothing else), and re-verified from a genuinely fresh environment.

**Recommendation: APPROVED.**

---

## 1. Repository Health *(Pass 1 findings, unchanged by Pass 2 — no code was touched)*

**Structure / packaging**
- `atlas/core/` is correctly picked up by `[tool.setuptools.packages.find] include = ["atlas*"]` — no packaging gap.
- `setup.py` coexists with `pyproject.toml` as a thin `setuptools.setup()` shim (namespace package declaration + entry point). Redundant with `pyproject.toml` but not broken; not flagged as blocking.

**Naming consistency**
- Within `atlas/core/`: `decision` and `decision_context` follow an identical layer shape (`domain/application/infrastructure/{persistence,api}`) with consistent snake_case module naming throughout. No inconsistency found in the new code.
- Across the repository as a whole, naming is not consistent — see Architecture Review below for the specific collisions.

**Dependency boundaries** — verified by direct import inspection, not inference:
- `atlas/core/domain/**` contains zero imports of `fastapi`, `sqlalchemy`, `pydantic`, or anything under `atlas.core.application`/`atlas.core.infrastructure`.
- `atlas/core/application/**` contains zero imports of `atlas.core.infrastructure`, `fastapi`, or `sqlalchemy`.
- No file under `atlas/core/` imports anything from the legacy `atlas.shared`, `atlas.domains`, `atlas.decision`, or `atlas.decision_journal` modules, and nothing in those legacy modules imports from `atlas.core`. Isolation is real, not just documented.

**Dead code / TODO markers**
- Zero `TODO`, `FIXME`, `XXX`, or `HACK` markers anywhere in `atlas/` or `tests/` (legacy and new alike).
- Zero `pdb`/`breakpoint()` leftovers anywhere. Zero stray `print()` statements in `atlas/core/`.
- No dead code identified in `atlas/core/` specifically. A broader dead-code sweep of the ~150-file legacy tree was out of scope; see Future Backlog.

**Generated artifacts tracked in git** — genuine finding, not fixed (out of scope for both passes):
- `atlas_investment_os.egg-info/*` has been committed since the initial commit (`f95bafc`) and `.gitignore` never excludes `*.egg-info/`. It is regenerated locally by `pip install -e .` — confirmed twice more during Pass 2's verification installs, and reverted both times so this review's own work wouldn't add to the drift. Cosmetic, non-blocking; see Future Backlog for the fix.
- `.DS_Store` and `__pycache__/` are correctly gitignored. No issue there.

**Temporary files** — none found tracked.

---

## 2. Architecture Review *(Pass 1 findings, unchanged by Pass 2 — no domain code was touched)*

**Confirmed intact, by direct verification:**

- `Decision` (`atlas/core/domain/decision/entity.py`) remains the aggregate root for API-001: frozen dataclass, `Decision.register()` the sole construction path, no update method anywhere on it or on `DecisionRepository`.
- `DecisionContext` (`atlas/core/domain/decision_context/entity.py`) is a genuinely separate aggregate: imports only `DecisionId` (identity) and `DecisionRepository` (interface, read-only) from the `decision` package — never `Decision` itself. `CaptureDecisionContextService` only ever calls `DecisionRepository.get()`; no code path lets capturing context mutate a `Decision`.
- Clean Architecture layering holds in both directions, confirmed by import grep, not by re-reading the design doc.
- API-001 and API-002 remain isolated from each other and from the legacy codebase (zero cross-imports either direction).

**Violation found — reported, not fixed, per this review's constraints (deferred, per architecture review, to a separate future consolidation increment):**

- **`DecisionContext` is a genuine naming collision, not just conceptual overlap.** `atlas/decision/decision_context.py` already defines a class literally named `DecisionContext` — a live portfolio/market snapshot, close to the *opposite* of what API-002's `DecisionContext` is defined to be.
- **`DecisionType` is also a name collision.** `atlas/decision_journal/engine.py` defines its own `DecisionType(str, Enum)` with values `CONSIDERING / ENTERED / EXITED / REVIEWED / PASSED` — distinct from API-001's `DecisionType` (`BUY / SELL / HOLD / WATCH / PASS`).

Neither causes a functional bug — isolation holds, both names resolve unambiguously via their distinct import paths. Both are recorded in the Future Backlog below, per the architecture review's explicit instruction, and were **not** renamed, consolidated, migrated, wrapped, or otherwise modified in Pass 2.

---

## 3. Documentation Review *(Pass 1 findings — now resolved in Pass 2 where marked)*

**Accurate and current throughout both passes:** `docs/DecisionCaptureAPI001.md`, `docs/DecisionContextAPI002.md`, `docs/ADR-004-API-Serialization-Standard.md`.

**Found outdated/contradictory in Pass 1 — resolved in Pass 2:**
- `README.md` stated new work "belongs in `atlas/domains/` and `atlas/capabilities/` only" — contradicted where API-001/002 actually live. **Fixed:** `atlas/core/` is now stated as the official location for new Product Increment work; `Decision`/`DecisionContext` under it are stated as the approved baseline concepts; the older packages are now explicitly described as not the default for new work.
- `docs/ArchitectureConsolidation.md` repeated the same contradiction ("all new product work should build on" `atlas/domains`/`atlas/capabilities`) in the document specifically responsible for architectural guardrails. **Fixed:** a new "Atlas Beta Baseline" section states the current, correct guidance; the specific contradictory rule and claim were corrected in place. The historical sprint-by-sprint log (Sprints 44–138) was left untouched — it is a historical record, not current guidance, and rewriting it was out of scope.
- `README.md`'s stale "947 tests pass as of RC2" and missing links to the three baseline docs. **Fixed:** count corrected to the current, verified figure; all three docs (plus this one) linked from the top-level Documentation table and Capabilities table.

**Found in Pass 1, deliberately not touched (pre-existing, unrelated to this baseline, per scope):**
- `docs/ProjectStructure.md` (Sprint 36) still makes no mention of `atlas/core/`.
- `CONTRIBUTING.md` ("Atlas is an AI Investment Partner") vs. `README.md` ("does not use AI or LLMs") — a real, pre-existing contradiction, unrelated to Decision/DecisionContext. Recorded in Future Backlog.

---

## 4. Required Actions Taken (Pass 2)

**Action 1 — Test dependency.**
- Added `[project.optional-dependencies]` `dev = ["pytest>=8.0"]` to `pyproject.toml` — the repository's existing PEP 621 dependency-management structure; no new packaging system introduced.
- Updated `README.md`'s Install section to `pip install -e ".[dev]"`, with a one-line explanation of what `[dev]` provides.
- Updated `.github/workflows/ci.yml`'s install step from the previous implicit `pip install -e . pytest` to `pip install -e ".[dev]"`, so CI now uses the same declared dependency group as the documented local setup, rather than its own undocumented extra install.

**Action 2 — Architecture guidance.**
- `README.md`: "Architecture State" section rewritten to present `atlas/core/` as the current, official location for new Product Increment work; added `Decision`/`DecisionContext` to the Capabilities table; added the naming-collision note (pointing at this report's Future Backlog) directly where the older Decision-shaped legacy modules are listed; linked all three baseline docs plus this report from the Documentation table; corrected the stale test count.
- `docs/ArchitectureConsolidation.md`: added a new "Atlas Beta Baseline (`atlas/core/`)" section stating the same, immediately after the document's introduction; corrected the one specific rule ("New product capabilities are built in `atlas/domains` and `atlas/capabilities`...") and the "all new product work should build on" claim to point at the new section instead. The historical sprint log was not touched.
- Both documents were written to state facts declaratively (what `atlas/core/` is, what it contains, where new work belongs) rather than as historical narrative, specifically so ADS's context-file ingestion receives accurate, unambiguous architectural context in future runs, per the architecture review's explicit instruction.

**One necessary consequence, disclosed rather than silently handled:** fixing `README.md`'s stale test count broke a pre-existing test, `tests/test_release_candidate.py::test_readme_mentions_947_tests`, which asserted the literal string `"947"` was present in `README.md`. This is outside the letter of "dependency declaration, setup/architecture documentation, and the readiness report" — but leaving it broken would mean the full suite no longer passes as a direct, unavoidable result of an authorized documentation fix, which conflicts with this same review's own verification requirement. The assertion was updated to check the current count instead of the frozen historical one (renamed `test_readme_mentions_current_test_count`); no other test logic was touched. The sibling test against `docs/ReleaseCandidate.md` (a dated, legitimately historical release note that should still say "947") was left exactly as it was. Flagging this explicitly rather than deciding it was in-scope by assumption.

---

## 5. Final Verification (Pass 2)

All six steps requested by the architecture review, run against a fresh environment created for this verification:

1. **Fresh virtual environment** — created via `python3 -m venv .venv` in a clean temp directory, no reuse of any prior environment.
2. **Documented installation steps, followed exactly** — `pip install -e ".[dev]"` (the now-updated README instruction) succeeded cleanly.
3. **Full test suite** — `python -m compileall atlas tests` clean; `python -m pytest -q` → **7,041 passed, 3 skipped**, matching the count now stated in `README.md`. (An intermediate run, before the `test_release_candidate.py` fix above, showed `1 failed, 7,040 passed` — the single failure was the stale-count assertion described in §4, resolved before this final run.)
4. **Lint** — `ruff check atlas/core tests/unit`: **all checks passed**, unchanged from Pass 1. Whole-repo `ruff check .`: **1,202 findings**, identical count to Pass 1 — confirms Pass 2's changes (config/doc/one test assertion) introduced zero new lint findings anywhere, including in the one test file touched.
5. **API-001 and API-002 behavior unchanged** — their test modules re-run in isolation: **130 passed** (75 Decision Capture + 55 Decision Context), identical to every prior run in this conversation. No domain, application, or infrastructure code for either was modified in Pass 2.
6. **No unrelated files or generated artifacts left modified** — final `git status` shows exactly five modified files (`pyproject.toml`, `README.md`, `docs/ArchitectureConsolidation.md`, `.github/workflows/ci.yml`, `tests/test_release_candidate.py`) plus the pre-existing untracked baseline content (`atlas/core/`, `tests/unit/`, the four `docs/*.md` files). `atlas_investment_os.egg-info/*` was regenerated twice more by this verification's own `pip install` commands and reverted (`git checkout --`) both times, specifically so this review would not itself contribute to the drift documented in §1.

---

## 6. Release Recommendation

## APPROVED

Both blocking issues from Pass 1 are resolved and verified:
1. A clean environment following the documented setup can now install and run the full test suite without relying on any CI-specific implicit step.
2. The repository's architectural guidance now accurately states that `atlas/core/` is the official Beta baseline location, that `Decision`/`DecisionContext` under it are the approved concepts, and that the older `atlas/domains/`/`atlas/capabilities/` packages are not the default for new Product Increment work — written for both human and ADS-context consumption.

No domain change, API behavior change, refactor, or legacy consolidation occurred in either pass. The two deferred naming collisions (`DecisionContext`, `DecisionType`) remain exactly as found, recorded below, untouched.

---

## 7. Future Backlog

Not implemented; listed for future Product Increments.

- **Decision-concept consolidation** — reconcile or rename the colliding `DecisionContext` (`atlas/decision/decision_context.py` vs. `atlas.core.domain.decision_context`) and `DecisionType` (`atlas/decision_journal/engine.py` vs. `atlas.core.domain.decision.value_objects`) definitions. Acknowledged non-blocking per architecture review; explicitly not touched in Pass 2. Carries more urgency now that ADS reads repository context automatically.
- **Untrack `atlas_investment_os.egg-info/`** and add `*.egg-info/` to `.gitignore`.
- **Wire `ruff check`/`ruff format --check` into CI**, not just `.pre-commit-config.yaml`, so lint/format debt stops accumulating silently the way the current 1,202 findings did. (Declaring `pytest` as a dev dependency is now done, per Action 1 above; extending the same dev group to `ruff` is a natural, still-unimplemented follow-on.)
- **Repository-wide lint/format cleanup** (1,202 `ruff check` findings, 252 files needing `ruff format` as of Pass 1) — entirely pre-existing, entirely outside this baseline; a dedicated, mechanical Product Increment of its own.
- **Resolve `docs/ProjectStructure.md` staleness and the `CONTRIBUTING.md`/`README.md` AI-mention contradiction** — both pre-date this baseline and are unrelated to Decision/DecisionContext.
- **Broader dead-code sweep of the legacy `atlas/` tree** (outside `atlas/core/`) — not attempted in either pass.

---

**End of review. Changes in Pass 2 were limited exactly to: `pyproject.toml` (dependency declaration), `README.md` and `docs/ArchitectureConsolidation.md` (architecture/setup documentation), `.github/workflows/ci.yml` (aligning CI's install step with the new dependency declaration), one test assertion in `tests/test_release_candidate.py` (disclosed in §4), and this report. No commits or tags were created. Waiting for architecture review.**
