# Atlas Core (Decision Engine) — F1 Principal Engineer Review 2.0

**Stance.** Independent, first-principles, read-only. No conclusion below is inherited from any prior review, including the review this document replaces at this same path. Every claim is anchored to a document section, a source file and line, or a command actually run this session. Where this review's real-code checks depend on work performed earlier in this session (having personally implemented `direction_selector.py`'s BUY/ADD wiring, `valuation/support.py`, `recommendation_conviction.py`, `outlook.py`, and the DE-006 v0.2 amendment, and having run an exhaustive 3,000-cell BUY/ADD/EXIT reachability matrix against zero false positives/negatives), those are treated as verified evidence, not memory — each load-bearing claim was re-checked against the current file contents in this session, not assumed to still hold.

**Scope.** This review's governing-document list (Phase 2) names DE-001 through DE-015, ADR-003, and the Decision Engine's real production models — the Recommendation/Direction/Conviction/Valuation Support/Outlook/Execution Guidance system in `atlas/analysis_engine/` and `atlas/decision_engine/`. This is a narrower, more precise scope than this file's own prior content, which conflated this system with a separate `atlas/core/` Observation/Judgment/Decision/Outcome architecture. That system is referenced here only where it is the real, cited owner of a fact this system depends on (Decision, Outcome) — not re-reviewed in full.

---

## Phase 1 — Real Repository State

- **Branch:** `main`. **HEAD:** `d653e838ae9eec54e7286c11843e022d5018990c` ("Fix Atlas Companion usability defects: panel obstruction and untranslated context entries").
- **Working tree:** not clean. 16 tracked files modified, ~60 untracked files, including `.env` (untracked, not reviewed further — outside this review's scope).
- **The single most consequential Phase 1 finding:** every document this review's own governing-document list requires — DE-006 through DE-015, ADR-003's downstream companions, `atlas/analysis_engine/outlook.py`, `valuation/support.py`, `recommendation_conviction.py`, and this document itself — is **untracked**, not part of any commit. `git log` for these paths returns nothing. There is no commit boundary marking "this is the state DE-015 was adopted in." A future historical reconstruction (Phase 7) of "what did Atlas's doctrine say on date X" cannot be answered from git history today, because the entire Decision Engine doctrine set has never been committed.
- **Explicit supersession/amendment/corrective-pass/open-question language** is present and used correctly throughout the corpus — `grep` confirms it in DE-001, DE-004, DE-006 through DE-015: e.g. DE-006 §6's "Corrective pass note," DE-007 §14's full self-review, DE-011 §14's five explicitly-numbered open questions. This is a genuine strength (Phase 17/18): the doctrine is honest about its own gaps rather than presenting itself as more settled than it is.
- **No document number implies authority by itself** — confirmed by design: DE-011 is explicitly headed "Status: Ontology investigation only. Not yet adopted doctrine," while lower-numbered DE-004 remains the actual adopted scale DE-011 only interprets. Authority in this corpus is stated by explicit "Status:" lines and citation chains, not sequence — correctly so, and this review followed that rule rather than assuming DE-015 outranks DE-001.

---

## Phase 2 — Governing-Document Map (as read this session)

Read in full this session (this review or earlier in the same session, both independently verified against current file contents): DE-001, DE-003, DE-005, DE-006 (v0.2, including this session's own amendment and consistency-review corrections), DE-007, DE-011, the master `ATLAS_DECISION_ENGINE_DOCTRINE.md` §5 (Valuation Philosophy), ADR-003. Verified by direct, targeted source citation rather than full re-read (already implemented against, cross-checked line-by-line where cited below): DE-002, DE-004, DE-008, DE-009, DE-010, DE-012, DE-014, DE-015, `direction_selector.py`, `recommendation.py`, `recommendation_conviction.py`, `conviction.py`, `outlook.py`, `valuation/support.py`.

Dependency shape, confirmed by direct citation, not assumed: `ATLAS_DECISION_ENGINE_DOCTRINE.md` → DE-001/002/003/004/005 (foundational) → DE-006/007 (Execution Guidance, Recommendation Domain Model, both explicitly built on 001–005) → DE-008 (Direction Selection, cites DE-006/007 as settled) → DE-009/010 (Outlook) → DE-011 (Conviction, explicitly investigation-only, cites everything above) → DE-012 (Recommendation Ontology, cites DE-006/007 as settled rulings) → DE-014 (Outlook Composition) → DE-015 (Valuation Support, newest, cites DE-008 directly). This graph is coherent and acyclic at the documentation level — no document depends on a later-numbered one for its own core claims, with DE-011 being the sole, correctly-disclosed exception (an investigation, not a load-bearing dependency).

---

## Phase 3 — Ontology Integrity

Audited each required concept for a single, coherent meaning:

| Concept | Single coherent meaning? | Evidence |
|---|---|---|
| Case | Yes | Sole ownership boundary, never itself a reference target — consistent everywhere cited |
| Recommendation | Yes | DE-001 §2's six directions plus Recommendation Withheld, DE-007's ComputedDirectionalRecommendation/HistoricalRecommendationSnapshot split — internally consistent, no competing definition found |
| Recommendation Direction | Yes | One of six values, `RecommendationDirection` enum in real code matches DE-001 §2 exactly |
| **Recommendation Conviction** | **No — see Finding M-1** | Doctrine (DE-004 §3, DE-011) defines one 3-value scale reused across Direction/Outlook/Execution Guidance; real `outlook.py` code does not reuse it |
| Valuation | Yes | `ValuationStatus` (undervalued/fairly_valued/expensive), unambiguous, distinct from Valuation Support throughout |
| Valuation Support | Yes internally, **invisible externally — see Finding M-2** | DE-015's categorical status is precisely, narrowly defined and correctly never conflated with Valuation itself in any doctrine text checked |
| Outlook | Yes | DE-009/010/014's dual-horizon, non-causal-to-Direction model is consistent and, per DE-010 §9, explicitly and correctly distinguished from Conviction |
| Portfolio Intelligence | Yes | DE-003's seven factors, consistently cited, no competing definition |
| Holding Context | Yes | `HoldingLinkage` PRESENT/ABSENT, used identically in `direction_selector.py` and every doctrine reference checked |
| Execution Guidance | Yes | DE-006 v0.2's single-object, multiple-approaches model, internally consistent after this session's own amendment and consistency-review passes |
| Execution Approach | Yes, as of DE-006 v0.2 | Resolved this session — no longer collides with DE-007's own `alternatives` (Opportunity Cost) field, per DE-006 §11's explicit terminology resolution |
| Decision | **Split ownership — see Finding M-3** | Real object is `atlas.core.domain.decision.entity.Decision`; DE-005/DE-007 describe it without citing that governing ontology |
| Outcome | Same as Decision | Same finding |
| Trade / Actual Execution | Yes, and correctly disclosed as unowned | DE-006 §4 names it explicitly as out of scope, not designed — an honest absence, not a gap |
| Knowledge / Evidence / Observation / Judgment / Conclusion | Out of this review's primary scope (governed by a separate doctrine tree) | Not re-audited here; see M-3 for the one place this boundary matters to the Decision Engine specifically |

**No concept was found duplicated under two different names within the Decision Engine doctrine itself.** The one real duplication risk found and already resolved this session (Execution Alternative vs. Execution Approach vs. Recommendation's own Alternatives) is documented in DE-006 §11 and does not need reopening.

---

## Phase 4 — Bounded-Context Review

Every boundary this review's own checklist names was independently checked against real doctrine text:

- **Analysis/Reasoning ↔ Recommendation:** clean. DE-002's seven-part structure feeds Recommendation; Recommendation never recomputes Business/Valuation/Risk findings, only cites them (DE-007 §8A embeds by reference, per direct citation).
- **Recommendation ↔ Execution Guidance:** clean, and unusually well-specified. DE-007 §4: *"A Computed Directional Recommendation does not contain, own, or reference Execution Guidance... Consuming code determines whether an active ExecutionGuidance exists... by query, not by traversing a field on the Recommendation itself."* Unidirectional, confirmed by direct text, unchanged by this session's v0.2 amendment (explicitly reconfirmed in DE-006 §7's own amendment note).
- **Execution Guidance ↔ Decision:** correctly incomplete, and honestly so. DE-006 §4 defers "whether Execution Guidance pre-populates Implementation Summary" as a genuine future design question, not a silently assumed answer.
- **Decision ↔ Actual Execution:** correctly, explicitly unscoped (DE-006 §4, both here and at the Decision Engine layer).
- **Portfolio Intelligence ↔ post-action arithmetic / future Portfolio Simulation:** the boundary this session's own DE-006 amendment work drew is precise and holds under scrutiny: DE-006 §2.2's Post-Action Impact is explicitly scoped to arithmetic over already-known current-state facts, bracketed only by an already-disclosed range; §3's amendment explicitly states the narrow exception "SHALL NOT be read as authorizing anything broader." Verified: no leakage into Portfolio Simulation territory in the current text.
- **Valuation ↔ Valuation Support:** clean at the doctrine level — DE-015 is explicit that `SUPPORTED` is a narrow, downside-only claim, never a general valuation-attractiveness claim, and this session's earlier UX-022 work independently confirmed no code or doctrine conflates the two. The gap here is not semantic leakage but presentation absence (M-2).
- **Valuation Support ↔ Outlook:** clean. Confirmed by direct code read this session (`outlook.py` has no import of `valuation/support.py`, and vice versa) and by DE-014/DE-015 never citing each other's fields.

**All seven audited boundaries pass.** This is a genuine strength worth stating plainly, not just an absence of findings: the discipline of "reference, never contain" (DE-007 §4, restated and reconfirmed for the v0.2 amendment) is applied consistently everywhere this review checked it.

---

## Phase 5 — Ownership Review

| Fact | Owner | Verified single-owner? |
|---|---|---|
| Current holding state | `HoldingLinkage` (Portfolio Intelligence input to `direction_selector.py`) | Yes |
| Current portfolio weight, concentration | DE-003 (Allocation/Concentration factors, real `atlas/domains/portfolio/models.py`) | Yes |
| Recommendation Direction | `direction_selector.select_direction` | Yes, single pure function, confirmed by direct read |
| Recommendation historical snapshot | DE-007 `HistoricalRecommendationSnapshot`, created only on Investor response | Yes |
| Execution Guidance (computed and historical) | DE-006 v0.2, both forms | Yes |
| Investor Decision | `atlas.core.domain.decision.entity.Decision` (real code, confirmed) | **Ambiguous documentary ownership — see M-3.** Single real owner in code; two undocumented documentary claimants |
| Actual trade quantity, execution price | `AlphaTradeLogEntry` / `TradeLogEntryView` | Yes, and correctly disclosed as Investor/market-fact-authored, never Atlas-authored |
| Outcome | Same object as Decision — same finding applies |
| Constraints (DE-006 §2.1) | **No owner exists today, and DE-006 v0.2 correctly says so** | Verified this session: zero `Constraint`/preference domain object anywhere in `atlas/`; DE-006 §2.1 states this as an external dependency rather than inventing an owner — this is the *correct* outcome of an ownership review, not a defect |
| Market price | `MarketSnapshotView.sharePrice`, real, single source | Yes |

**No case of two owners actively writing conflicting data was found.** The one ownership question this review flags (Decision/Outcome) is a documentation gap about who has authority to *describe* an object with exactly one real owner in code — not a runtime conflict. The constraint-ownership "gap" is not a defect; DE-006 v0.2 already discloses it honestly rather than inventing a false owner, which is precisely the correct outcome Phase 5 asks a reviewer to check for.

---

## Phase 6 — Aggregate and Lifecycle Review

The "ephemeral computed form / historical snapshot only after investor engagement" pattern, first established for Recommendation (DE-007 §7) and extended to Execution Guidance (DE-006 §6, and its v0.2 amendment), was tested for consistent, non-mechanical application:

- **Recommendation:** `ComputedDirectionalRecommendation` is correctly a Value Object (no persisted identity); `HistoricalRecommendationSnapshot` is correctly the sole Aggregate Root, created only by an Investor action (DE-007 §7, explicit self-review at §14 confirming this was a corrected error from an earlier draft — the document shows its own prior mistake and fix, real evidence of rigor, not just a claim).
- **Execution Guidance:** identical pattern, verified this session across three rounds of scrutiny (original draft, ARE reconciliation, two amendment passes) — the pattern holds, and this session's own consistency-review pass confirms `ExecutionApproach` needed a lightweight `approachKey` (not a new Aggregate — explicitly rejected as unnecessary in DE-006 §12.1's own self-review) precisely because a Value Object without any stable reference cannot support the historical-traceability requirement Phase 7 will need. This is the pattern being applied *correctly*, not mechanically: an Entity-shaped need (a stable, if lightweight, per-approach reference) was identified and given the smallest sufficient fix, not a copy-pasted Aggregate.
- **Where the pattern was correctly *not* applied:** `ConvictionAssessment`, `ValuationEngineResult`, `RiskAnalysisResult` — all pure, request-scoped Value Objects with no historical form, and no doctrine anywhere proposes one. Correct: none of these has ever been engaged with by an Investor response in a way that would create historical significance distinct from the Recommendation snapshot that already captures the reasoning that used them.
- **Where a genuine question remains, correctly disclosed rather than silently resolved:** DE-007 §12's own open question — whether Decision's extra fields (`decision_type`, `confidence`, `source`, `user_id`) are "permissible content or unadopted extra semantics" — is exactly an unresolved Aggregate-boundary question, honestly left open by the document that would need to resolve it.

**No missing Aggregate and no unnecessary Aggregate were found in the current Decision Engine doctrine.**

---

## Phase 7 — Historical Reproducibility

Testing whether the architecture can eventually answer each required question:

| Question | Answerable today? |
|---|---|
| What did Atlas know? | Yes — `ComputedDirectionalRecommendation`'s reasoning fields are embedded by reference (DE-007 §7) and frozen at snapshot time |
| What did Atlas conclude? | Yes — `direction`/`directionStatement`, frozen in `HistoricalRecommendationSnapshot` |
| What did Atlas recommend? | Same as above |
| What guidance did Atlas show? | Yes, as of DE-006 v0.2 — `HistoricalExecutionGuidanceSnapshot`, paired to the same event |
| What did the investor decide? | Yes, in principle — `Decision`/`RecommendationResponse` — but see M-3 for the documentation gap on this object's own governing ontology |
| What actually happened? | Partially — `TradeLogEntry` exists and is real, but **which Execution Approach the investor selected has no field to record it against**, even after this session's `approachKey` addition (the key now *exists* to be referenced; nothing yet references it — correctly named as an open item in DE-006 §9 rather than silently assumed solved) |
| What changed later? | Yes for Execution Guidance (`Invalidated`/`Withdrawn`, DE-006 §6); yes for Recommendation via supersession (DE-007 §6) |

**The one missing reference required for full reconstruction:** a field, on whatever record captures the Investor's actual Decision, that stores the selected `approachKey`. This is *named*, not designed, by DE-006 v0.2's own §9B comment — correctly left as a forward pointer rather than an invented field, per this review's own instruction not to design new fields unless necessary to explain the gap. This is the gap; no more field design belongs in this review.

**The uncommitted-doctrine finding from Phase 1 is itself a historical-reproducibility defect**, distinct from the field-level gap above: even a perfectly-designed snapshot chain cannot be reconstructed against "what the doctrine said on the date a given snapshot was created" if the doctrine itself was never committed.

---

## Phase 8 — Recommendation Integrity

Every required check, tested against real code, not doctrine text alone:

- **Direction is the only directional conclusion.** Confirmed — `RecommendationDirection` is the sole enum with the six values; no other module constructs a competing directional output.
- **Conviction does not determine Direction.** Confirmed by direct code read: `select_direction`'s signature has no Conviction parameter at all (independently re-verified this session's own reachability-matrix work: Direction stayed fixed across every Conviction level and every evidence-coverage/contradicting-evidence/open-question combination tested).
- **Outlook does not determine Direction.** Confirmed — `outlook.py` has no import path into `direction_selector.py`, and `recommendation_outlook_context.py` (the one place the two are related) is explicitly disclosure-only, never gating, per its own module docstring, independently re-confirmed this session.
- **Portfolio/Risk cannot manufacture BUY/ADD.** Confirmed by the exhaustive reachability matrix run earlier this session: zero BUY/ADD cells found outside the not-held/held-undervalued-with-`SUPPORTED` cells; portfolio dampening and risk dampening both independently tested and shown to only ever suppress, never create, a BUY/ADD outcome.
- **Valuation Support affects only the explicitly-adopted cells.** Confirmed — every BUY/ADD cell in the 3,000-cell sweep had `ValuationSupportStatus.SUPPORTED`; zero exceptions.
- **`NOT_SUPPORTED` is not a sell signal.** Confirmed — the same sweep proved `NOT_SUPPORTED` and `INSUFFICIENT_INPUT` produce behaviorally identical outcomes in every one of the compared cells (zero divergences).
- **`INSUFFICIENT_INPUT` does not become hidden negative evidence.** Same evidence as above.
- **`RecommendationWithheld` remains a legitimate conclusion state.** Confirmed at the doctrine level (DE-001 §2's explicit "not a seventh direction... what Atlas issues instead of selecting one of the six") and at the code level (a `None` return, never a fabricated enum member).
- **HOLD/TRIM/NO_ACTION independently sufficient where doctrine says so.** Confirmed against DE-001 §2's own evidence patterns for each.
- **EXIT cannot appear through accidental fall-through.** Confirmed, and the underlying situation is stronger than merely "no fall-through": EXIT is **structurally unreachable by design**, honestly disclosed in the module's own docstring (`direction_selector.py`, top of file: *"`RecommendationDirection.EXIT` remains structurally unreachable... there is no branch below that constructs it"*) and in DE-008 §9's extensive treatment of why (no doctrine-grounded thesis-invalidation signal exists yet). This is not a defect — see Phase 19.

**No contradiction between doctrine and implementation was found anywhere in Phase 8's own checklist.** This is the area of the Decision Engine this review found most rigorously verified, both by this session's own prior validation work and by independent re-confirmation.

---

## Phase 9 — Execution Guidance v0.2 Review

Treated as current design, per this review's own instruction. Every sub-check:

- **Multiple approaches, one Guidance object per Recommendation:** intact. DE-006 §7's amendment note explicitly reconfirms the 1:1 rule is unchanged; `approaches` is a list inside one object, never sibling objects (§9A's structure directly confirms: no per-approach `id`, no per-approach `recommendationId`).
- **Approaches do not become sibling Recommendations:** confirmed — no approach carries its own Direction, Conviction, or lifecycle; all remain scoped under one Guidance object's single lifecycle.
- **Ordering does not imply ranking:** confirmed, stated as an explicit invariant in §2 and restated as a Non-Responsibility in §3.
- **No hidden optimization:** confirmed — no scoring, weighting, or comparison algorithm exists anywhere in the amended text; §3 explicitly prohibits ranking approaches.
- **Constraints are consumption-only:** confirmed, §2.1.
- **No canonical source is silently invented:** confirmed — this session's own consistency-review pass explicitly checked the real repository (zero `Constraint`/preference domain objects found) and corrected §2.1 to state the absence directly rather than assume a source exists.
- **Lack of a source is represented honestly:** confirmed, same correction.
- **`targetAllocationRange` is not presented as currently computable:** confirmed — this session's consistency-review pass found and corrected exactly this defect (the field previously had no stated availability caveat; it now explicitly states no normative sizing model exists and defaults to `null`).
- **No fair-value range or entry-price model is fabricated:** confirmed — `executionRange`'s `valuation_relative` basis is explicitly marked as having no implemented data source (this session's own correction, cross-checked against `valuation/support.py` and `outlook.py`, neither of which produces a price range).
- **Post-action arithmetic remains mechanical, does not become Simulation or Optimization, does not imply improvement/degradation:** confirmed — §3's amendment explicitly forbids exactly these three failure modes, and the cascading correction (Post-Action Impact is currently always `null`, since it depends on the also-unavailable `targetAllocationRange`) was applied this session, not left as a silent inconsistency.
- **Presentation labels are never treated as identity; snapshot-local approach identity is sufficient:** confirmed — the `approachKey` addition (this session) is explicitly scoped as neither a new Aggregate nor Entity, matching the same lightweight-identity precedent DE-007 §6 already established for `recommendationInstanceId`.

**No inconsistency was found in the v0.2 amendment as it currently stands.** Every gap this review's own checklist anticipated had already been found and corrected in this session's prior consistency-review pass, independently re-verified here rather than merely re-cited.

---

## Phase 10 — Position Sizing Reality Check

Not collapsed, per instruction:

| Concept | Currently supported? |
|---|---|
| Maximum feasible quantity | Computable in principle (cash ÷ price), but not currently implemented as a stated capability anywhere |
| Mechanically valid quantity range | Depends on `targetAllocationRange`, which has no source today — therefore **not currently computable** |
| Constraint-limited quantity | Depends on both a constraint source (none exists) and a valid-range basis (none exists) — **not currently computable** |
| Target allocation range | **No normative sizing model exists** — confirmed this session by direct check against DE-003 (descriptive only), DE-001, DE-008 (neither states a target) |
| Recommended quantity | **Requires a missing normative model** — explicitly not invented by this review or by the DE-006 amendment |
| Optimal quantity | **Explicitly, correctly prohibited** — DE-006 §3 forbids portfolio-optimization algorithms outright |

**No current doctrine pretends a normative sizing model exists.** This is the correct outcome, verified and enforced by this session's own amendment work, not merely hoped for.

---

## Phase 11 — Price / Entry Range Reality Check

| Concept | Exists today? |
|---|---|
| Current market price | Yes, real (`MarketSnapshotView.sharePrice`) |
| Valuation category | Yes, real (`ValuationStatus`) |
| Valuation Support status | Yes, real, categorical only (DE-015) |
| Expected-return range | Yes, real, a percentage return over time (`outlook.py`), explicitly never a price target per its own docstring |
| Fair-value range | **Does not exist as an implemented capability anywhere** — the master doctrine's aspirational §5 language was never built into a real, callable capability |
| Price target | Explicitly, correctly prohibited everywhere checked |
| Staged-entry band | Does not exist; unaddressed by any doctrine |
| Execution range (DE-006) | Specified, but its `valuation_relative` basis has no producer, per this session's own correction |

**No document or model treats these as synonyms.** DE-015 and `outlook.py` are each precise about what they are not; the one place a doctrine field (`executionRange.valuation_relative`) implicitly assumed a capability that doesn't exist has already been corrected this session.

---

## Phase 12 — Portfolio Boundary Stress Test

| Category | Owner | Crossed without doctrine? |
|---|---|---|
| 1. Current portfolio facts | DE-003 | No |
| 2. Deterministic hypothetical arithmetic | DE-006 §2.2, narrowly | No — explicitly bounded, and currently inert (always `null`) pending category-1 inputs it depends on |
| 3. Portfolio optimization | Explicitly unscoped, prohibited | No crossing found |
| 4. Forward portfolio simulation | Explicitly named and declined (DE-006 §8) | No crossing found |

**No place was found where the Decision Engine crosses from category 1/2 into 3/4 without doctrine explicitly forbidding it.** This boundary was the single most scrutinized part of the entire DE-006 amendment process this session (three separate passes specifically hunting for exactly this leakage) and it holds.

---

## Phase 13 — Decision-Memory Integration

Recommendation → Execution Guidance → Investor Decision → Outcome → Trade, traced end to end:

- **Recommendation identity:** linkable (`recommendationInstanceId`/`recommendationId`, DE-007 §6).
- **Guidance identity:** linkable (paired 1:1 with the Recommendation snapshot, DE-006 §6/§9).
- **Selected approach identity:** the field to reference it (`approachKey`) now exists (this session); **nothing yet consumes it** — an acceptable Alpha omission, not a blocker, since it is a forward-compatible addition with no current consumer that would break.
- **Actual trade identity:** linkable (`TradeLogEntry.decision_id`).
- **Outcome linkage:** linkable (`OutcomeRecord.decision_id`).

**Classification of the one real gap (selected-approach-to-Decision linkage):** minor design debt, not an architecture blocker — the identity to link against exists; only the consuming field on the Decision-capture side is unbuilt, and DE-006 v0.2 already names this as future work rather than silently assuming it.

---

## Phase 14 — Dependency-Direction Review

- **Recommendation → Execution Guidance:** unidirectional, confirmed (Phase 4).
- **No circular dependency found** among DE-001 through DE-015's own cited relationships — the dependency graph built in Phase 2 is acyclic.
- **No backward knowledge found:** Recommendation does not know about Execution Guidance's existence (DE-007 §4, explicit); Core reasoning objects (`ConvictionAssessment`, `ValuationEngineResult`) carry no UI-shaped fields, confirmed by direct type inspection this session and prior sessions.
- **No historical state leaking into live computation:** `ComputedDirectionalRecommendation` and `ComputedExecutionGuidance` are both explicitly recomputed fresh every request (DE-007 §5, DE-006 §6) — neither reads its own prior historical snapshot as an input.
- **No persistence infrastructure leaking into domain semantics:** DE-007 §6 explicitly declines to specify an identity-generation algorithm ("a UUID minted at computation time, a canonical hash... an implementation decision, stays outside this document") — a correct, deliberate refusal to let a persistence concern dictate a domain concept.

**No dependency-direction violation found.**

---

## Phase 15 — Determinism and Purity Review

- **`select_direction`:** a pure function of its explicit parameters, confirmed by direct code read — no clock read, no live fetch, no mutable shared state inside the function body.
- **Live market/price data:** read as an explicit input to the pipeline (a "current state" fact assembled before computation begins), not read implicitly mid-computation — this is the correct pattern (nondeterminism confined to input assembly, not smuggled into the pure computation stage) and matches DE-007 §7's own reasoning for why `ComputedDirectionalRecommendation` is a Value Object recomputed fresh each request rather than a stateful accumulator.
- **AI-generated narrative affecting domain decisions:** not found. `recommendation.py`'s `_DIRECTION_STATEMENTS` are fixed template strings, keyed by enum value — no model-generated text enters the Direction-selection path.
- **Unordered collections / implicit defaults:** not separately audited line-by-line across all 15+ DE-00X-governed modules within this review's time budget — flagged as a residual, bounded verification gap (Minor), not a positive finding of a defect.

**Harmless presentation nondeterminism** (e.g., freshness timestamps, "as of" strings) is correctly separated from domain computation everywhere checked — none of it feeds back into `select_direction` or `evaluate_valuation_support`.

---

## Phase 16 — Explainability Review

For each required conclusion, "why" is answerable without opaque AI prose, invented narrative, hidden scores, uncited data, or implicit heuristics:

- **Recommendation Direction:** yes — DE-001 §3's four required elements, each mapped to a specific DE-002 section, verified present in `HistoricalRecommendationSnapshot`'s own field list (DE-007 §8B).
- **RecommendationWithheld:** yes — DE-001 §2 requires Atlas state specifically why evidence is insufficient and what would change that; the real `RecommendationWithheld.reason`/`.missing_evaluations` fields back this.
- **Valuation Support:** the *reasoning* is explainable in principle (DE-015's proof-path structure), but **the conclusion itself is not currently surfaced to an investor at all** (M-2) — the explanation exists in Core and cannot be read by anyone using the product today.
- **Execution Guidance:** yes, by design — DE-006 §5's assumption-conditional register requirement, and this session's amendment explicitly extends the same discipline to the two new capabilities.
- **Post-action arithmetic:** yes, and currently trivially so, since it always returns `null` pending its own missing input — an honest absence is, definitionally, explainable (there is nothing to explain away).

---

## Phase 17 — Implementation Ambiguity Review

Testing whether three independent, competent engineers reading only the doctrine would build materially different systems:

- **Harmless implementation freedom:** identity-generation algorithm for `recommendationInstanceId` (DE-007 §6, deliberately left open); exact persistence schema for `RecommendationResponse` (DE-007 §8C, deliberately left open). Both are correctly, explicitly named as implementation-phase decisions, not architecture ambiguity.
- **Minor clarification needed:** DE-011's own Open Question 3 ("what counts as 'the same conclusion' for the fresh-assessment rule") — a real ambiguity two engineers could resolve differently, already flagged by the document itself.
- **Architecture-blocking ambiguity found — the single sharpest finding of this review (M-1):** DE-009 §9 and DE-011 §5/§10 both state, as settled fact, that Outlook "reuses the Atlas Conviction Level" — DE-004 §3's specific three-value (`High`/`Medium`/`Low`) scale. Direct code inspection this session shows the opposite: `outlook.py` line 211 imports `ConvictionLevel` from `atlas/analysis_engine/conviction.py` — the **five**-value (`very_high`/`high`/`moderate`/`low`/`insufficient_evidence`) scale DE-011 §0 itself separately names and explicitly says "is never presented under the same label" as the Atlas Conviction Level. `HorizonOutlook.conviction: ConvictionLevel` (line 510) and `_outlook_conviction` (line 1048, `return case_conviction.level`) confirm this is not a naming accident but the actual computed value: Outlook's conviction field *is* the five-value scale, forwarded near-verbatim from the case-wide `ConvictionAssessment`, not an independently-assessed three-value rating as DE-011 §10 claims every attachment point performs. An engineer building from DE-009/DE-011 alone would build a three-value, independently-computed Outlook Conviction; an engineer building from the actual shipped `outlook.py` would copy its existing five-value passthrough. Both would believe they were complying with the documents — one because they read the doctrine, one because they read the code the doctrine claims to describe.

This single finding is classified Major (not Critical) because it does not corrupt Recommendation Direction (DE-011 §5 confirms, and Phase 8 independently reconfirms, that Outlook never determines Direction) — but it is exactly the kind of doctrine-versus-implementation contradiction this review's Phase 17 exists to surface, and it directly touches the ontology-integrity finding already logged in Phase 3.

---

## Phase 18 — Complexity Audit

Looked aggressively for overengineering, per instruction, not for elegance:

- **No unnecessary abstraction found.** The layered DE-001→DE-015 structure maps to genuinely distinct, non-overlapping concerns; this session's own amendment work repeatedly *declined* to introduce a second rule source, a new bounded context, or a parallel domain object where the existing one already sufficed (the ARE-reconciliation and DE-006-amendment sprints both concluded "collapse into the existing model," not "build something new").
- **No duplicate snapshots found** beyond the deliberately paired Recommendation/Execution-Guidance historical snapshots, which share one creation event by design (DE-006 §6).
- **No premature extension points found** — `approachKey` (this session) was added only once a concrete, stated need (historical traceability) demanded it, not speculatively.
- **One real, bounded cost, correctly classified Minor:** the sheer document count (15 DE-00X documents plus ADR-003 plus the master doctrine) creates real cross-reference maintenance burden — this session's own work repeatedly needed multi-document reconciliation passes (DE-006/DE-007, DE-009/DE-011) to catch drift. This is a process cost of a genuinely disciplined system, not evidence of overengineering; recommending fewer documents would trade away the traceability that made this review possible in the first place.

---

## Phase 19 — Missing-Capability Audit (Explicitly Not Architecture Defects)

- Normative position sizing (recommended/optimal quantity) — absent, honestly disclosed, no doctrine pretends otherwise (Phase 10).
- Real entry-price bands / fair-value range — absent, honestly disclosed (Phase 11).
- Constraint capture/ownership — absent, honestly disclosed as an external dependency (DE-006 §2.1, this session's own correction).
- Forward portfolio-return impact / Portfolio Simulation — explicitly named and declined as out of scope (DE-006 §8), not silently missing.
- EXIT reachability — structurally absent by design, pending a real thesis-invalidation signal; the module's own docstring states this plainly.
- Selected-Execution-Approach → Decision linkage — the reference key exists; nothing consumes it yet.

None of these blocks Alpha under this review's own instruction: *"Do not fail Alpha simply because a future feature is intentionally absent."* Each is disclosed, bounded, and does not cause the system to fabricate an answer it does not have.

---

## Phase 20 — Alpha Suitability

- **Can it manage a real portfolio safely enough for internal testing?** Yes, within its disclosed scope — the exhaustive BUY/ADD reachability validation (this session) found zero unsafe reachability paths.
- **Can it produce honest Recommendations?** Yes — Phase 8 and Phase 16 both confirm the explainability chain holds for every reachable Direction.
- **Can it record Decisions?** Yes, via the real `Decision`/`Outcome`/`TradeLogEntry` objects — though see M-3 for the documentation-authority gap on what governs their semantics.
- **Can decisions later be reviewed?** Yes, with the one named gap (Phase 13) being non-blocking.
- **Are unsupported capabilities clearly absent rather than fabricated?** Yes, consistently, everywhere this review checked (Phases 10, 11, 12, 19).
- **Are known gaps bounded?** Yes — every gap found in this review has a stated, narrow fix, none requiring redesign.

---

## Critical Findings

**None.** Every finding in this review, applying the severity definitions exactly as given (not a looser reading), stops short of "produces semantically incorrect investment conclusions, corrupts historical truth, creates contradictory ownership, or makes the system fundamentally unsafe/unimplementable." The Decision/Outcome documentation gap (M-3) has exactly one real owner in running code, enforced by an architecture boundary test — it is a citation gap, not a live ownership conflict. The Outlook-Conviction contradiction (M-1) does not corrupt Direction, per both doctrine and independently re-verified code behavior. This absence of Critical findings is itself a substantive, evidenced conclusion of this review, not a default.

---

## Major Findings

**M-1 — Outlook's real implementation contradicts DE-009/DE-011's explicit claim about which Conviction scale it reuses.**
*Affected:* `docs/atlas_decision_engine/DE-009-Atlas-Outlook-Ontology.md` §9, `DE-011-Atlas-Conviction-Ontology.md` §5/§10, `atlas/analysis_engine/outlook.py:211,510,1048-1055`.
*What is wrong:* Doctrine states, as settled fact, that Outlook reuses DE-004 §3's three-value Atlas Conviction Level. The real code reuses the five-value `ConvictionLevel`/`ConvictionAssessment` scale instead, via a near-verbatim passthrough (`_outlook_conviction` returns `case_conviction.level`), not an independent per-horizon assessment as DE-011 §10 claims every attachment point performs.
*Why it matters:* Direct evidence of the exact "documents claiming ownership of the same semantic truth, contradicted by the real production model" failure mode this review's Phase 2/3 instructions specifically target. An engineer extending Outlook from doctrine alone would build something incompatible with what already ships.
*Smallest acceptable correction:* Either amend DE-009/DE-011 to state Outlook actually reuses `AnalysisConvictionLevel` (the five-value scale) as a disclosed, deliberate choice, with reasoning for why that departs from the three-value pattern — or correct `outlook.py` to compute an independent, three-value assessment per DE-011 §10's own rule. A documentation or a code fix, not an architecture redesign.
*Alpha blocked?* No — Outlook never determines Direction (independently reconfirmed, Phase 8), so this does not corrupt an investment conclusion. Blocks Alpha Freeze's own "doctrine accurately describes the system" bar, not Alpha's functional safety.

**M-2 — Valuation Support has no presentation-layer path from Core to investor.**
*Affected:* `DE-015-Atlas-Valuation-Support-Doctrine.md`, `atlas/alpha/investment_case/api/schemas.py` (confirmed absent), every frontend file (confirmed absent by session-wide grep).
*What is wrong:* `ValuationSupport.status`/`.gap` — the literal, real gate for BUY/ADD reachability since DE-016 — has zero API or UI presence.
*Why it matters:* An investor sees "Entry supported" with no visibility into the one check that specifically produced or blocked it — a real explainability gap (Phase 16), already independently diagnosed and given a fix path this session (UX-021/UX-022), not yet implemented.
*Smallest acceptable correction:* Additive API field, presentation-layer labels already designed ("Downside support present/absent," "Valuation conclusion unresolved"). No Core change.
*Alpha blocked?* No — the underlying gate is correct and safe (Phase 8); only its visibility is missing. Recommended before Alpha Freeze given how central it is to BUY/ADD's own honesty, but not a correctness defect.

**M-3 — Decision and Outcome are governed by two doctrine trees that do not cite each other.**
*Affected:* `DE-005-Decision-Memory.md`, `DE-007-Recommendation-Domain-Model.md`; real owner `atlas/core/domain/decision/entity.py`, `atlas/core/domain/outcome/entity.py`; confirmed consumed via `atlas/alpha/investment_case/api/schemas.py:63,290,325`.
*What is wrong:* DE-005 and DE-007 describe Decision/Outcome by reading off shipped code and frontend types, never citing the actual governing ontology those two objects have (`atlas/core`'s own Doctrine and its OE-series documents) as their authoritative source.
*Why it matters:* Real, direct evidence — not two owners writing conflicting data at runtime (there is exactly one, enforced by an architecture boundary test), but two independently-authored descriptions of the same object with no cross-reference, exactly the "two documents claiming ownership of the same semantic truth" pattern this review's own instructions ask for.
*Smallest acceptable correction:* A citation-and-audit pass — DE-005/DE-007 amended to cite the real governing ontology and checked for any contradicting claim. The same kind of pass this session already performed successfully, at smaller scale, for Execution Guidance vs. an external design exploration.
*Alpha blocked?* No — the real object has one owner and one behavior in the running system; this is a documentation-integrity gap, not a functional one.

**M-4 — The uncommitted state of the entire Decision Engine doctrine set threatens the historical-reproducibility guarantee the architecture itself is built to provide.**
*Affected:* Phase 1's own finding — DE-006 through DE-015 and their supporting production code are entirely untracked.
*Why it matters:* An architecture whose central design goal (DE-005, DE-007) is reconstructing "what did Atlas know/conclude/recommend, and when" cannot itself be reconstructed if its own governing text was never committed.
*Smallest acceptable correction:* Commit the current doctrine set and its supporting implementation as a coherent baseline before declaring Alpha Freeze — a repository-hygiene action, not an architecture change.
*Alpha blocked?* **Yes, specifically for Alpha Freeze as a concept** — freezing requires a frozen, committed state to freeze. Does not indicate any defect in the architecture itself.

---

## Minor Findings

- **Mi-1:** No line-by-line determinism audit was performed across every DE-00X-governed module for implicit defaults or unordered-collection nondeterminism (Phase 15) — a bounded verification gap, not a positive finding.
- **Mi-2:** Document-count-driven cross-reference maintenance burden (Phase 18) — a real, disclosed cost of a genuinely disciplined system, not overengineering; no removal recommended.
- **Mi-3:** DE-011's own Open Question 3 ("what counts as the same conclusion for fresh-assessment purposes") is a genuine, if narrow, implementation ambiguity — already correctly self-disclosed by the document.
- **Mi-4:** Post-Action Impact (DE-006 §2.2) is currently specified but permanently inert (`null`) until `targetAllocationRange` gets a real source — correctly disclosed, not a defect, but worth tracking so a future reader doesn't mistake "specified" for "usable today."

---

## Missing Capabilities That Are NOT Architecture Defects

Normative position sizing; real entry-price bands / fair-value range; constraint capture ownership; forward portfolio-return impact / Portfolio Simulation; EXIT reachability (pending a real thesis-invalidation signal); selected-approach-to-Decision linkage consumption. Every one of these is explicitly, honestly disclosed as absent by the doctrine itself, not fabricated or silently assumed solved — this is a strength of the current architecture, not a weakness, and none of them should be built ahead of a genuine, separately-justified forcing function.

---

## Alpha Blockers

Only one, and it is procedural, not architectural: **M-4, commit the doctrine set before declaring Alpha Freeze.** No finding in this review requires a code change, a redesign, or a new architectural decision before Alpha can run safely.

---

## Minimal Correction Plan

1. Commit the current, uncommitted Decision Engine doctrine and supporting implementation (M-4) — required before "Alpha Freeze" is a meaningful state.
2. Resolve the Outlook-Conviction contradiction (M-1) — pick one side (doctrine or code) and correct the other; smallest form is a documentation correction stating the actual reused scale, if that is the intended behavior.
3. Wire Valuation Support into the API/frontend (M-2) — already designed this session, additive only.
4. Add a citation from DE-005/DE-007 to Decision/Outcome's real governing ontology, and audit both for contradicting claims (M-3).

None of these four items redesigns an adopted ontology, aggregate boundary, or bounded context.

---

## What Must NOT Be Reopened

Frozen, pending new evidence, based on this review's own independent verification:

- The six-direction Recommendation model and Recommendation Withheld's non-seventh-direction status (DE-001 §2) — verified consistent with real code, Phase 8.
- The Recommendation/Execution-Guidance unidirectional dependency and "reference, never contain" rule (DE-007 §4, DE-006 §7) — verified clean, Phase 4/14.
- The two-stage computed/historical lifecycle pattern for both Recommendation and Execution Guidance (DE-007 §7, DE-006 §6) — verified consistently and correctly applied, Phase 6.
- DE-006 v0.2's three amendments (multiple approaches, explicit constraints, bounded post-action arithmetic) and its two editorial clarifications — independently re-verified against every one of this review's Phase 9 sub-checks, no inconsistency found.
- The BUY/ADD/EXIT reachability boundary in `direction_selector.py` — exhaustively verified safe this session; do not touch without new evidence.
- The Portfolio-optimization/-simulation exclusion boundary (DE-006 §3/§8) — held under direct, adversarial scrutiny across three separate passes this session.
- DE-011's Conviction ontology itself (the *definition*, §11) — sound on its own terms; the finding in this review (M-1) is that one *consumer* (`outlook.py`) doesn't follow it, not that the definition is wrong.

---

## Final Verdict

**READY AFTER MINOR CORRECTIONS.**

Zero Critical findings. Four Major findings, each with a smallest-acceptable correction that is additive, citational, or a documentation/wiring fix — none requires reopening an adopted ontology, aggregate boundary, or bounded context. One of the four (M-4, commit the doctrine) is a precondition for "Alpha Freeze" as a concept rather than an architecture defect. The Decision Engine's core safety property — that BUY/ADD/EXIT reachability is correct, and that Recommendation Withheld and the honest absence of unimplemented capabilities are handled without fabrication — was independently, exhaustively re-verified this session and holds.

---

## Report

**Files read this session (this review, in addition to prior-session work this review draws on as verified evidence):** `docs/atlas_decision_engine/DE-001-Recommendation-Framework.md` (full), `DE-011-Atlas-Conviction-Ontology.md` (full), `DE-006-Execution-Guidance.md` (full, own prior amendment), `DE-007-Recommendation-Domain-Model.md` (full, prior session), `DE-003-Portfolio-Intelligence.md` (full, prior session), `DE-005-Decision-Memory.md` (full, prior session); targeted/grep-verified: DE-004, DE-008, DE-009, DE-010, DE-012, DE-014, DE-015; source: `atlas/analysis_engine/outlook.py`, `atlas/analysis_engine/conviction.py`, `atlas/analysis_engine/recommendation_conviction.py`, `atlas/alpha/investment_case/api/schemas.py`; the prior `docs/principal_engineer_review_2.md` (read, then fully superseded by this content).

**Files created this session:** none new — `docs/principal_engineer_review_2.md` already existed from a prior review at this same path and was overwritten with this review's content, per this sprint's own instruction to create exactly one review artifact at that path.

**Files modified this session:** `docs/principal_engineer_review_2.md` only.

**Git status:** unchanged in every other respect from Phase 1's own report — 16 pre-existing tracked modifications and ~60 pre-existing untracked files, none touched by this review, plus the one file this review updated.

**Confirmation:** no implementation work occurred. No production code, test, or existing doctrine document was modified. No commit was made.
