# Decision Workspace UI Implementation Report

**Sprint 13 — Product integration implementation.** Implementation notes only. No ADR was written or modified this sprint. This is the first frontend work in this program — every prior sprint (9–12) was backend-only.

---

## 1. Execution Report

Built the first complete Decision Workspace product surface: a route consuming Sprint 12's Reasoning Workspace API to assemble Decision, DecisionContext, DecisionDraft, Assumption, and CaseCondition state in one screen; a unified Reasoning Timeline merging three existing per-aggregate event histories; full create/revise/challenge/retire management for Assumptions and create/revise/evaluate/retire for CaseConditions, each a direct call to its own existing endpoint (Sprints 10–11); and a Draft Commit flow wrapping Sprint 12's `commit-with-reasoning` orchestration endpoint. **Zero backend files were touched.** Every fact shown in the UI is read from an existing endpoint; every mutation is a direct call to an existing endpoint; nothing is computed, validated, or derived client-side beyond a pure chronological sort of already-fetched events (the Reasoning Timeline).

The feature was verified two ways: the full automated suite (46 new frontend tests, `tsc --noEmit`, `vite build`), and a live, manual end-to-end pass — both backend and frontend dev servers running together, real `Case`/`Decision`/`DecisionContext`/`Assumption`/`CaseCondition` rows created via the real API, the workspace page loaded in a real browser, and two real write actions performed (evaluating a CaseCondition, challenging an Assumption) — confirmed by the on-screen status changing and the Reasoning Timeline growing by one correctly-ordered entry after each action.

No ADR conflict was found.

## 2. Files Created

**Frontend** (`frontend/src/decisionWorkspace/`): `reasoningWorkspaceApi.ts` (client for Sprint 12's five endpoints, plus the three existing per-aggregate `.../events` endpoints), `assumptionApi.ts` (create/revise/challenge/retire), `caseConditionApi.ts` (create/revise/evaluate/retire), `reasoningTimeline.ts` (the pure event-merge function), `ReasoningTimelineView.tsx`, `AssumptionsSection.tsx`, `CaseConditionsSection.tsx`, `DecisionWorkspacePage.tsx` (route), `DraftCommitPage.tsx` (route), and their eight `*.test.ts(x)` files.

**Frontend test infrastructure** (new to this repository — see §6, Implementation Findings): `vitest.config.ts`, `src/testSetup.ts`, `src/testUtils.tsx`.

**Documentation**: this report.

No new backend file — this sprint's own brief explicitly scopes it to "reuse the existing Reasoning Workspace API," and no gap was found requiring one.

## 3. Files Modified

- **`frontend/package.json`** / **`frontend/package-lock.json`** — added `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom` as devDependencies, plus a `"test": "vitest run"` script. No existing dependency version changed.
- **`frontend/src/App.tsx`** — two new `<Route>` lines (`decisions/:decisionId/workspace`, `decision-drafts/:draftId/commit`) and their imports. No existing route changed.
- **`frontend/src/i18n/translations/en.ts`** / **`sv.ts`** — one new `decisionWorkspace.*` namespace (109 lines each, kept in exact 1:1 key parity — `tsc` enforces this structurally, per `LanguageContext.tsx`'s own `Record<Language, Record<TranslationKey, string>>` typing). No existing key changed.
- **`atlas/core/infrastructure/api/app.py`** — diff stat shows 37 lines, identical to Sprint 12's own final state; **this sprint added no further change to it.** (The diff is inherited from Sprint 12, not new.)

No backend domain, application, persistence, or API file was touched — confirmed by `git diff --stat` showing no backend path beyond `app.py`'s already-existing Sprint 12 diff.

## 4. Tests

| Category | File(s) | Result |
|---|---|---|
| Pure-function (projection) | `reasoningTimeline.test.ts` | 5 passed |
| Component | `ReasoningTimelineView.test.tsx`, `AssumptionsSection.test.tsx`, `CaseConditionsSection.test.tsx` | 17 passed |
| API interaction | `assumptionApi.test.ts`, `caseConditionApi.test.ts`, `reasoningWorkspaceApi.test.ts` | 17 passed |
| Integration | `DecisionWorkspacePage.test.tsx` | 7 passed |
| **New tests, total** | | **46 passed, 0 failed** |
| Backend regression | Full `pytest tests/` (10,236 passed, 210 pre-existing unrelated CLI-subprocess failures, unchanged in count from Sprint 9's own baseline) | Unaffected — zero backend files modified |
| `tsc --noEmit` | Whole frontend | Clean |
| `vite build` | Whole frontend | Clean, 119 modules |

The API interaction tests assert the exact request shape (`method`, `path`, `body`) each client function sends, against the real backend contract each endpoint already defines (Sprints 9–12) — not against a reimplementation of it. `DecisionWorkspacePage.test.tsx` is the integration layer: it mocks only the network boundary (`reasoningWorkspaceApi`'s own fetch functions) and exercises the real `DecisionWorkspacePage` → `AssumptionsSection`/`CaseConditionsSection` → `ReasoningTimelineView` component tree together, including the loading/error/loaded states and the resume-link to `DraftCommitPage`.

**Live, manual end-to-end verification** (both dev servers running, real backend, real browser): created a `Case`, `Decision`, `DecisionContext`, `Assumption`, and `CaseCondition` via direct API calls; loaded `/decisions/{id}/workspace` and confirmed every section rendered the real data correctly, including the Originating Draft section correctly showing "recorded directly, not from a draft" for a Decision with no draft; evaluated the CaseCondition via the human-assertion checkbox and confirmed its status changed from Active to Satisfied on screen and a new, correctly-ordered entry appeared in the Reasoning Timeline; challenged the Assumption and confirmed the identical pattern (status changed to Challenged, note text appeared, a fourth timeline entry appeared after the first three, correctly ordered).

## 5. Build Results

`npm run typecheck` — clean. `npm run build` — clean, 119 modules (up from 109 before this sprint), one pre-existing chunk-size advisory unrelated to this change. `npm run test` (`vitest run`) — 46 passed. Backend `create_app()` and the full pytest suite are unaffected, since no backend file was modified.

## 6. Implementation Findings

Three findings — two tooling/infrastructure decisions and one interpretive resolution of the sprint's own brief. None introduces a new ontology, aggregate, or backend concept.

1. **No frontend test framework existed before this sprint.** Confirmed: no `vitest`/`jest` config and no `*.test.*` file existed anywhere in `frontend/` prior to this sprint. Sprint 13 §7 explicitly requires component/integration/API-interaction tests, so a minimal, standard Vite-native stack (`vitest` + `@testing-library/react`) was added as devDependencies — a tooling choice, not an architectural one, and the natural pairing for an already-Vite project (shares its transform pipeline, needs no separate bundler config). `globals: false` was chosen deliberately (explicit imports in every test file, keeping test-only globals out of application code's own type space) — this required one additional fix: Testing Library's own auto-`cleanup()` only self-registers when a test runner's *global* `afterEach` is detected, so `src/testSetup.ts` registers it explicitly; without this, component trees from one test leaked into the next test's DOM (found and fixed while writing `AssumptionsSection.test.tsx`, the first component test with more than one `it()` block).

2. **`renderWithProviders`'s own `path` parameter.** `useParams()` returns `{}` unless the element under test is rendered through a matching `<Route>` — a bare `<MemoryRouter>` around a page component, with no `<Routes>`/`<Route>` in between, never populates route params, even though the current location is set correctly. `testUtils.tsx`'s `renderWithProviders` accepts an optional `path` (the route *pattern*, e.g. `"/decisions/:decisionId/workspace"`) alongside `route` (the concrete URL) for exactly this reason — found and fixed while writing `DecisionWorkspacePage.test.tsx`.

3. **"DecisionDraft (if active)" in the UI is two visually distinct sections, following Sprint 12's own identical resolution.** `ReasoningWorkspaceService.load_workspace` (Sprint 12) already splits this into `originatingDraft` (the committed draft that became this Decision, if any) and `activeCaseDrafts` (other in-progress drafts on the same Case) — this sprint's UI renders both as named, separate sections ("Originating Draft" / "Other Active Drafts on This Case") rather than collapsing them, since collapsing them would silently discard the distinction Sprint 12 deliberately introduced.

**Decision explicitly made against duplicating orchestration client-side:** every mutation handler (`AssumptionsSection`, `CaseConditionsSection`, `DraftCommitPage`) calls exactly one existing endpoint and then either navigates away or invokes a parent-supplied `onMutated` callback that re-fetches the *entire* workspace from the backend. No component computes a new `status`, patches a `linkedCaseConditionIds` array, or otherwise predicts what the backend will say next — every render shows exactly what the last real fetch returned, confirmed directly by the live end-to-end test (§4): after each write, the UI's own displayed status came from a fresh GET, not from local state manipulation.

## 7. ADR Conflicts

None. No ADR governs frontend presentation; this sprint's own engineering rules ("UI consumes existing APIs only," "no duplicated orchestration logic in the frontend") were followed as stated, not as a substitute for one.

## 8. Final Conformance Statement

Sprint 13's own Definition of Done is met in full:

- **The Decision Workspace is fully usable through the UI** — verified live, not just by automated test: viewing Decision/DecisionContext/Assumptions/CaseConditions/originating draft/other active drafts, and performing real create/revise/challenge/retire/evaluate actions, all confirmed against a real backend in a real browser.
- **The frontend consumes existing orchestration APIs without duplicating backend logic** — every API client function is a direct, unmodified-shape wrapper (verified by the API interaction tests asserting exact request bodies); the one piece of client-side computation (`buildReasoningTimeline`) is a pure sort of already-fetched data, explicitly not a projection of anything the backend didn't already compute.
- **Event histories are presented through a unified timeline** — `ReasoningTimelineView`, backed by `reasoningTimeline.ts`, merges `DecisionDraftEvent`/`AssumptionEvent`/`CaseConditionEvent` histories from their three existing endpoints into one chronological list, confirmed live (a CaseCondition evaluation and an Assumption challenge each appeared as new, correctly-ordered timeline entries in the same live session).
- **Assumptions and CaseConditions can be managed entirely through existing endpoints** — confirmed both by component tests (mocked) and the live session (real): create, revise, challenge, retire for Assumptions; create, revise, evaluate, retire for CaseConditions.
- **The full regression suite passes** — 10,236 backend tests unaffected (zero backend files modified), plus this sprint's own 46 new frontend tests, `tsc --noEmit`, and `vite build`, all clean.

## Related

`docs/ReasoningWorkspace-Implementation-Report.md` (Sprint 12, the orchestration layer this UI consumes). `docs/Assumption-Implementation-Report.md`, `docs/CaseCondition-Implementation-Report.md`, `docs/DecisionDraft-Implementation-Report.md` (Sprints 9–11, the individual APIs this UI's management sections call directly). `docs/Atlas-Architecture-Conformance-Register.md` (Wave F — the first product-facing wave).
