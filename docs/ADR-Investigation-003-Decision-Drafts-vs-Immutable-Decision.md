# ADR Investigation 3 — Decision Drafts vs. Immutable Decision

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document.

**Central question:** What does "Save as Draft" mean in Atlas — an incomplete Decision, a pre-Decision object, transient UI state, a Case-scoped unresolved intention, a DecisionContext-like companion, or something else?

**Method:** Read fresh for this investigation — the three prior architecture documents, `DE-005`, `DE-006`, `UX-008`, `UX-009`, `ADR-002`, the `Decision`/`DecisionContext`/`Outcome`/`Case`/`ReflectionResponse`/`Observation`/`Question`/`Conclusion` entities and value objects, and — because Phase 10 requires it — the `atlas/alpha/security_confirmation` package (models, table, package docstring), the current Daily Brief backend (`atlas/alpha/daily_brief/`, confirmed to contain no draft concept anywhere), and the frontend's one existing precedent for client-side session persistence (`frontend/src/companion/CompanionPanel.tsx`'s `sessionStorage` usage).

**Headline finding, stated up front:** a draft cannot honestly be called a Decision (Phase 1), cannot be built as `DecisionContext` (Phase 6), `ReflectionResponse` (Phase 7), `Case` state (Phase 8), or any earlier Core Loop object (Phase 9) — every one of these fails on a structural, not stylistic, ground, most often the same one: every existing object this investigation tested is immutable, and a draft is, by definition, something an investor edits. This investigation concludes new ontology is required, and says so directly, per its own governing instruction not to avoid that conclusion if the evidence leads there.

---

## Phase 1 — Decision Ontology, Re-Established

**What makes something a Decision:** satisfying every one of `Decision`'s required constructor arguments — `case_id`, `user_id`, `decision_type`, `subject`, `investment_case` (the reason), `confidence` — in one atomic call to `Decision.register()`. There is no partial constructor, no builder, no way to hold a `Decision` instance missing any of these.

**When it begins to exist:** at the exact moment `register()` succeeds. `DecisionId()` is generated *inside* that call — there is no earlier identity for a Decision to have accrued content against.

**What "recorded" means:** `recorded_at` is stamped by Atlas's own clock, at construction, distinct from `decided_at` (the investor's own account of when they decided, preserved as given). Both fields exist only once, together, at the single moment of commitment — "recorded" is not a status a thing enters gradually; it is the moment a `Decision` first exists at all.

**Why immutable:** "There is no update. A changed opinion is a new Decision" — a stated commitment against exactly the risk `UX-008` §14 names directly: a Decision that could be edited later could be quietly rewritten to match a since-known outcome, destroying the very record the Decision Workspace exists to preserve.

**Why a changed opinion becomes a new Decision:** because a `Decision`'s identity *is* its content at a moment. Mutating it would not update a decision — it would erase what was true at the moment it was made and replace it with something else wearing the same identity.

**What historical truth it preserves:** "what I committed to, and why, at this exact moment" — never "what I was in the middle of thinking about."

**Can an object that has not yet been committed honestly be called a Decision?** No — decided directly from the constructor's own shape, not assumed. `Decision.register()` requires `decision_type`, `subject`, `investment_case`, and `confidence` to already be fully-formed, valid values *before* construction is even attempted. An "incomplete Decision" is not a weaker or partial Decision — by the same logic that a class instance either satisfies its required parameters or does not exist, it is not a Decision at all. This settles half of the central question immediately: whatever a draft is, storage location aside, it structurally cannot be a `Decision`.

---

## Phase 2 — UX-009 Draft Semantics

Every passage found, re-read fresh:

- **Section 13 (Record Decision):** "Save as Draft — preserves the Workspace in its current state without committing to the record. Drafts are surfaced in the Daily Brief as unresolved decisions. Available at any time from the footer."
- **Preventing Incomplete Records:** "The user may save a draft at any time without meeting these requirements. **Drafts do not enter Atlas Memory.**" — UX-009's own text, not this investigation's inference, already answers half of Phase 15 below.
- **Navigation Behaviour:** "Return to Workspace... dismisses the overlay and returns the user to the same scroll position and expanded state... The user is prompted once: 'Exit without saving?' No data is lost unless the user confirms exit." — describes the *unsaved*, in-progress case specifically, distinct from an explicitly-saved draft.
- **`UX-012` (re-read for this investigation), "Nine elements preserved across every navigation event":** "Draft content (autosaved and recovered)" — a direct, independent textual confirmation that draft content is expected to survive ordinary navigation, not merely panel collapse.

**What UX-009 expects a draft to do:** preserve in-progress Workspace content, resumable later, and be discoverable from a *different page* (Daily Brief) as an unresolved item.

**Must it survive:**

| Requirement | Evidence | Conclusion |
|---|---|---|
| Panel collapse | "preserves the Workspace in its current state" | Yes |
| Page navigation | "surfaced in the Daily Brief" — necessarily a different page | Yes |
| Browser refresh | `UX-012`'s "autosaved and recovered" | Yes (by direct textual match) |
| Logout/login | Not stated explicitly; "surfaced in the Daily Brief" is naturally a returning-session concept | Implied, not explicit |
| Device change | Not stated; a server-backed mechanism would incidentally support it | Not required, but a natural consequence of whatever satisfies "Daily Brief" |
| Multiple days | Daily Brief is, by its own name, a repeating, multi-day surface | Yes |

**These requirements are derived from the described behavior, not from the word "draft" alone** — per instruction. The single load-bearing requirement is "surfaced in the Daily Brief," which cannot be satisfied by anything that dies with the originating tab or session.

---

## Phase 3 — Persistence Requirement

**`SERVER_PERSISTED_PRE_DECISION`**

`EPHEMERAL_SESSION_STATE` is ruled out directly: something that dies with the session cannot appear in a Daily Brief visited on a later day. `LOCAL_CLIENT_PERSISTENCE` alone is ruled out on the same evidence: Daily Brief is naturally understood as a server-rendered reflection of server-known state; for it to see a client-local draft, either every possible originating device would need to be read from directly (which breaks under any cross-device access, explicitly acknowledged as a real future risk in Phase 13/18) or genuine server persistence is required. `SERVER_PERSISTED_DECISION` is ruled out by Phase 1: a draft cannot honestly be a `Decision`, regardless of where it lives. The remaining, evidence-supported classification is a server-persisted object that is explicitly *not* a `Decision` — hence `SERVER_PERSISTED_PRE_DECISION`.

---

## Phase 4 — Temporal Ontology

**Conceptual sequence:** `Case → Draft (0..N) → Decision → Outcome`

- **Can a draft exist before a Decision?** Yes — definitionally, this is its entire purpose.
- **Can several drafts exist for one Case?** Ontologically plausible; nothing in UX-009 restricts an investor to one open line of reasoning per Case. Cardinality is examined fully in Phase 13.
- **Can one draft produce several Decisions?** No — per `UX-008`'s own "a changed opinion is a new Decision," every act of recording produces exactly one `Decision`. A single draft, once recorded, transitions to exactly one `Decision`; a later change of mind is a *new* draft (or direct re-entry) producing a second, independent `Decision`, not the same draft producing two.
- **Can a draft be abandoned?** Yes — UX-009's own "Return to Workspace... without recording or saving" already describes this for the unsaved case; whether a *saved* draft can later be actively abandoned is not explicitly named (see Phase 12).
- **Can it be superseded?** Plausibly, by the same logic a Decision itself can be superseded by a later one, but UX-009 never defines a "supersede" action for drafts specifically — an open question, not a settled one.
- **Can it expire?** Not addressed anywhere in UX-009 or UX-008. Genuinely unspecified.
- **Does recording a Decision consume the draft?** Semantically, yes — once the reasoning the draft represents becomes a committed `Decision`, the draft's own reason for existing (an unresolved intention) is resolved. Whether "consumed" means deleted at the storage layer is an implementation question this investigation does not answer.
- **Does the draft continue to exist after Decision capture as provenance?** Genuinely unresolved by anything read for this investigation. UX-009's "Drafts do not enter Atlas Memory" reads most naturally as describing *unresolved, never-recorded* drafts — it does not explicitly say what becomes of a draft that *did* eventually get recorded. Two readings remain equally defensible: the former-draft is simply discarded once superseded by the real `Decision`; or it is retained as provenance of the drafting process itself, in the spirit of `ReflectionResponse`'s own provenance snapshot. This investigation states both, decides neither.

---

## Phase 5 — Ownership

| Draft content | Owner | Why |
|---|---|---|
| Proposed decision type | Investor | What the investor is considering — distinct from Atlas's *own* proposed decision, itself an unresolved ownership question already flagged in `Architecture-Resolution-Sprint-1.md` §12; that same ambiguity propagates directly into draft ownership and is not re-litigated here |
| User-written decision statement | Investor | Same shape as `Decision`'s eventual commitment field |
| Rationale | Investor | Same shape as the eventual `Decision.investment_case.reason` |
| Confidence | Investor | Same shape as the eventual `Decision.confidence` |
| Alternatives considered | Investor | Same shape as `DecisionContext.alternatives_considered` — raises directly the question answered decisively in Phase 6 |
| Uncertainties | Investor | Same shape as `DecisionContext.uncertainties` |
| Implementation intent | Investor | Forward-looking content with **no existing post-Decision home at all** — `Architecture-Resolution-Sprint-1.md` §9 already found this; a draft cannot inherit a home its eventual, recorded form doesn't have either |
| Review intent | Investor | Same "no existing home" finding, from §8 of the same prior document |
| Unresolved questions | **Atlas**, tracked by the draft, not authored by it | The one field in this list that is not investor-authored at all — these are Atlas-surfaced open questions the investor has not yet resolved; the draft *references* them, it does not originate them |

**Pattern:** most draft content is the *pre-Decision version* of fields that already have a well-defined home once a `Decision` (and, separately, a `DecisionContext`) exists — `reason`↔rationale, `confidence`↔confidence, `alternatives_considered`↔alternatives, `uncertainties`↔uncertainties. A small remainder (implementation intent, review intent) has no home even *after* commitment. This is the key fact Phase 6 tests directly.

---

## Phase 6 — Draft vs. DecisionContext

An actual attempt to make the model work, not an assertion of difference:

| Dimension | Fit? | Why |
|---|---|---|
| Temporal fit | **Fails, structurally** | `CaptureDecisionContextService.capture()` raises `DecisionNotFoundError` if the referenced `Decision` does not already exist — not a design preference, an enforced application-layer precondition. A draft is by definition pre-Decision; `DecisionContext` cannot be instantiated before one exists, under any circumstance. |
| Cardinality | Fails | `DecisionContext` is capped 0..1 *per Decision*; a draft has no Decision to be "per," and would need a different scoping axis (Case, or investor × Case) entirely. |
| Required existing Decision | Fails | The single hardest blocker, restated. |
| Authorship | **Fits** | Investor-only in both — the one dimension where the two genuinely align. |
| Mutability | **Fails, structurally** | `DecisionContext` has no update path anywhere (insert-only, confirmed in both prior investigations). A draft is, by UX-009's own text, something re-entered and further edited ("preserves the Workspace in its current state" implies resumable editing). This is a second, independent, structural mismatch, not merely a difference in degree. |
| Semantic scope | Fails | Even setting the two blockers above aside, `DecisionContext`'s own fields (`situation`, `alternatives_considered`, `uncertainties`, `portfolio_relevance`, `capital_considerations`) never cover `decision_type`, `confidence`, or the primary reason — the parts of draft content that most directly mirror `Decision` itself, not `DecisionContext`. |
| Persistence behavior | Fails | Same conflict as mutability — insert-only vs. an object that must support repeated updates before finalization. |

**Conclusion: the merge fails on two independent, structural grounds — temporal precedence and immutability — not a stylistic preference.** This is a decisive rejection, not a judgment call.

---

## Phase 7 — Draft vs. ReflectionResponse

The same direct-attempt method, applied to the second candidate:

| Dimension | Fit? | Why |
|---|---|---|
| Trigger/occasion | **Fails** | `ReflectionResponse` requires a prior, Atlas-computed occasion (a `DecisionReflection` + `CoachingQuestion`, per `Investigation-002` §1/§4); a draft requires none — it is the investor's own spontaneous, self-initiated reasoning. This is a direct mismatch on the exact axis `Investigation-002` established as `ReflectionResponse`'s defining trait. |
| Temporal order | **Fails, structurally, and more strictly** | `ReflectionResponse.register()`'s own docstring: "anchored to an already-recorded Decision... valid because a Decision, once recorded, never changes." Same hard blocker as `DecisionContext`, stated even more explicitly. |
| Authorship | Fits | Investor-only, and preserved with even stricter fidelity (no normalization at all) — an interesting design signal for any future draft-editing implementation, not itself grounds for reuse. |
| Decision dependency | Fails | Same hard requirement as temporal order. |
| Provenance | **Fails** | `ReflectionResponse`'s entire shape is organized around snapshotting an occasion; a draft, being unoccasioned, has no such occasion to snapshot — the identical shape mismatch `Investigation-002`'s own Phase 6 merge attempt already found, recurring here against a third candidate. |
| Multiplicity | Plausible fit | `ReflectionResponse` carries no confirmed cap (`Investigation-002`'s own finding) — the one dimension that is not a blocker, since a draft plausibly could tolerate uncapped multiplicity too. Not sufficient to overcome the other five. |
| Semantic content | **Fails** | About the investor's reaction to their *own past pattern* — categorically different from draft content, which is about the *current, in-progress* investment decision, not the investor's historical behavior. |

**Conclusion: fails more decisively than `DecisionContext` — every load-bearing trait of `ReflectionResponse` (occasioned, post-Decision, meta/behavioral content) is the direct opposite of what a draft needs (unoccasioned, pre-Decision, situational content).**

---

## Phase 8 — Draft vs. Case

Challenged seriously, not dismissed by assumption:

- **Is the draft fundamentally about the Case before commitment?** Partially, yes — its *subject matter* concerns a specific Case. But "about a Case" is not the same as "is Case state," the same distinction that already keeps `DecisionContext` off of `Case` (no `case_id` field on that table at all).
- **Would putting it on Case violate Case semantics?** Yes, directly. `Case`'s own docstring (re-read for this investigation): "no further lifecycle, status, title, description, or content is canonically forced" and "Case does not depend on, and is never automatically accompanied by, Decision, Outcome, Judgment, Knowledge Reference, Reasoning Trace, Evaluation, Learning, Hypothesis, or reasoning_link." Attaching draft state directly to `Case` would be the single most direct violation of `Case`'s own stated minimalism found anywhere in this investigation series.
- **Is Case immutable?** Yes — exactly two fields (`id`, `recorded_at`), no update path, and deliberately named `create()` rather than `capture()`, "since there is nothing to capture, only an ownership boundary to establish." A draft, needing repeated edits, is exactly the kind of state `Case`'s own immutability structurally forbids holding directly.
- **Does Case already hold mutable workflow state?** No — confirmed, zero mutable fields exist.
- **Would a draft become generic Case metadata rather than a real domain concept?** This is the real risk worth naming precisely: examined carefully, "draft on Case" does not offer a genuinely different structure from a separate aggregate merely referencing `case_id` — it collapses into exactly what Option C (Phase 17) already represents, only under a less honest name that avoids acknowledging it as its own domain concept.

**Conclusion: fails on both Case's explicit doctrinal minimalism and its confirmed immutability — and, examined carefully, the option does not even offer a structurally distinct alternative to a separate aggregate.**

---

## Phase 9 — Draft vs. Observation / Question / Conclusion / ReasoningTrace / Judgment

| Object | Shape | Test result |
|---|---|---|
| `Observation` | "Something the investor noticed... immutable... introduces no relationship to Decision" | **Fails** — retrospective (a record of something already noticed) where a draft is prospective (leading toward a decision); also immutable, the same blocker recurring a fourth time. |
| `Question` | Root of the Core Loop; a single `Statement` + `raised_at`; immutable; references nothing | **Fails** — far too narrow (a draft needs decision type, rationale, confidence, alternatives, uncertainties, not one open-ended prompt) and immutable. Interesting nuance: an investor's own unresolved Questions could plausibly be *referenced by* a future draft without the draft *being* a Question — a sub-component relationship, not an equivalence. |
| `Conclusion` | "The output of the reasoning process... anchored to a single Evidence record... immutable" | **Fails on authorship alone** — Atlas/reasoning-authored, drawn from Evidence, not investor-authored intention. Also wrong-directioned: `Conclusion` is itself upstream input to a Decision (via `reasoning_link.ConclusionDecisionLink`), not a stand-in for the draft that leads to one. |
| `ReasoningTrace` | Case-scoped; "one or more accepted, same-Case Domain Objects provide epistemic support"; a `frozenset` of typed references, never narrative content | **Fails on shape** — reference-only, not narrative — the identical shape mismatch already found against it in `Investigation-002`'s own Phase 7, reapplied here. |
| `Judgment` | Case-scoped; a single `characterization` field; immutable; explicitly a *settled* characterization | **Fails on the cleanest semantic opposition found in this investigation** — "settled" is the direct antonym of what a draft is (definitionally unsettled), on top of the same immutability blocker every other candidate shares. |

**No existing pre-Decision Core Loop object fits.** Every candidate is either immutable (the same structural blocker recurring across all nine objects tested across this and the two prior investigations) or has a shape too narrow or wrong-directioned for draft content. This strongly reinforces, from a fifth and sixth independent angle, that a draft requires new ontology if built at all.

---

## Phase 10 — Immutability Compatibility (Critical)

### Model A — Mutable Draft (one row, updated repeatedly)

- **Semantic integrity:** weakest — would be the *first* mutable row-level object anywhere in this domain model, a genuine, disclosed precedent-breaking choice.
- **Post-hoc rationalization risk:** real, but categorically lower-stakes than mutating a `Decision` — a not-yet-committed thought being edited is not the same as a permanent record being silently rewritten. Stated plainly, not glossed over.
- **Complexity:** lowest of the three models.
- **Recoverability:** poor — an overwritten row loses all prior state with no recovery path.
- **Auditability:** none — Atlas cannot answer "how did this draft evolve."
- **Consistency with Decision:** breaks the codebase's uniform-immutability convention, albeit at lower stakes than mutating `Decision` itself would be.
- **Consistency with Security Confirmation:** **contradicts it directly.** Security Confirmation's own package docstring (Sprint 20) states a resubmission is idempotent and a differing value is "rejected outright (409), never silently overwritten"; Sprint 22 then formalized a full append-only event model specifically so correction/revocation could exist *without* ever violating row-level immutability. Model A would be a direct regression from a pattern this exact codebase already, deliberately, moved away from once.
- **Suitability for Alpha:** possible as a minimal MVP, but sets a precedent this codebase has already outgrown.

### Model B — Append-only Draft Revisions (every edit creates a new immutable revision)

- **Semantic integrity:** strong — every prior state remains inspectable; matches the codebase's uniform immutability convention with no exception anywhere.
- **Post-hoc rationalization risk:** essentially none.
- **Complexity:** higher than A — "current state" requires reading the latest revision, a query, not a single-row lookup.
- **Recoverability / Auditability:** excellent.
- **Consistency with Decision:** excellent — `Decision` itself is, in effect, the "final revision" in exactly this sense; the pattern generalizes cleanly.
- **Consistency with Security Confirmation:** **this is, almost exactly, the `SecurityConfirmationEvent` pattern** already shipped and tested in this codebase — append-only events, current state always derived from the latest one, history never mutated.
- **Suitability for Alpha:** good — a real, working precedent already exists.

### Model C — Current-state Draft + Append-only Audit (a derived projection over immutable events)

- **Semantic integrity:** strong, and — this is the load-bearing finding of this phase — **Model C is not a third, independent model. It is Model B's own read-side optimization**, and it is *exactly* what the Security Confirmation package already implements: `SecurityConfirmationEvent` is the append-only source of truth; `ConfirmedSecuritySelection` is, in its own docstring's words, "the public 'what is currently confirmed' view, unchanged in shape... never a reference to those objects" — a derived, always-recomputable, non-authoritative convenience projection over the true source.
- **Post-hoc rationalization risk:** none — identical to B, since events remain the true source and the "current" row is never edited directly.
- **Complexity:** marginally higher than B to build (two things to keep consistent), but the Security Confirmation precedent shows this is a solved, working pattern in this codebase already — and it is *lower* in practice for any consumer that only needs "what does the draft say right now" (a resumed panel, a Daily Brief summary) without needing history.
- **Recoverability / Auditability:** identical to B — the underlying events remain fully recoverable regardless of whether a convenience projection also exists.
- **Consistency with Decision / Security Confirmation:** this *is* the Security Confirmation pattern, directly, not merely analogous to it.
- **Suitability for Alpha:** the best of the three — a proven, already-implemented pattern in this exact codebase, not a new persistence philosophy.

**This phase's own finding, carried into Phase 19: Model C, because it is not a new architectural risk — it is a second application of an already-proven one.**

---

## Phase 11 — Commit Boundary

**The event:** the investor's explicit Record Decision action. Sufficient? Yes — UX-009's own Section 13, consistent across all three prior documents' own re-reading of it, already treats this as the sole, investor-driven boundary ("Record Decision... cannot be triggered by Atlas"). Nothing found in this investigation surfaces a need for any other trigger.

- **What becomes immutable at that moment:** a brand-new `Decision`, constructed via the *same, unmodified* `Decision.register()` call that already exists today. This investigation finds no reason to change that mechanism itself — only to identify what supplies its arguments.
- **What data crosses the boundary:** `decision_type`, `subject`, `reason`, `confidence`, `decided_at` — exactly what `Decision` already requires, sourced from whatever the draft held at the moment of commit.
- **What data remains outside Decision:** everything `DecisionContext` already owns (`situation`, `alternatives_considered`, `uncertainties`, `portfolio_relevance`, `capital_considerations`) would, if the draft held it, cross into a separate, also-unmodified `DecisionContext.capture()` call — not into `Decision`. Implementation intent, review intent, and any still-pending unresolved questions remain outside *both* objects, per `Architecture-Resolution-Sprint-1.md` §§7–9's own still-undesigned-home findings.
- **Is the draft deleted, retained, archived, or referenced?** Not decided here — an implementation question, explicitly outside this investigation's scope. Phase 4's two-reading finding (discard vs. retain-as-provenance) remains open.
- **Does Decision need provenance back to the draft?** A real, evidence-adjacent option worth naming without deciding: `Decision` already has exactly one precedent for an optional, provenance-style back-reference — `observation_id`, added in "Decision Sprint 1" as "an optional anchor to the Observation this Decision was recorded from," fully backward-compatible and non-breaking. A `draft_id` field, added the same way, would be a second instance of an already-accepted pattern, not a new kind of change to `Decision`'s shape — worth carrying forward as a low-risk future option, not decided now.

---

## Phase 12 — Cancellation and Abandonment

| Action | Distinct concept? | Needs durable history? |
|---|---|---|
| Cancel editing (discard unsaved keystrokes) | Ordinary UI behavior — already covered by UX-009's own "Exit without saving?" prompt | No — never touches persisted state at all |
| Abandon draft (a previously-*saved* draft is set aside) | Yes, distinct from cancel — a real state transition (active → abandoned) once persistence exists | Yes, under Model B/C — an "abandoned" event, directly analogous to Security Confirmation's own "revoked" event type |
| Delete draft | Possibly distinct from abandon (soft vs. hard) — **not named anywhere in UX-009 or UX-008** | Unresolved — genuinely unspecified by any governing document read |
| Supersede draft | Relevant only if multiple drafts per Case are permitted (Phase 13) | Yes, under Model B/C — a new event type, no new mechanism |
| Expire draft | **Not addressed anywhere in UX-009 or UX-008** | Unresolved — genuinely unspecified |

Care taken not to over-formalize ordinary editing: only *persisted* state transitions (abandon, supersede) require durable history; in-progress, never-saved editing does not, and should not, become ontology.

---

## Phase 13 — Multiple Drafts

| Rule | Fit against evidence |
|---|---|
| One active draft per Case | Plausible default; matches Investment Case's own singular per-ticker shape; simplifies Daily Brief surfacing to one row |
| One active draft per investor × Case | Functionally identical to the above under Alpha's current single-investor model (`Decision.user_id` is already durable and investor-scoped, per `Investigation-002`'s own ATLAS-009B finding) — only diverges once multi-user access to a shared Case exists, which nothing in this codebase supports today |
| Many parallel drafts | Not forbidden by UX-009, but the *current* frontend's own single-`pendingAction`-at-a-time shape (confirmed across all three prior documents' own reading of `InvestmentCasePage.tsx`) implicitly assumes one line of reasoning at a time, even though the ontology does not strictly require it |
| Draft per proposed action | Plausible middle ground (e.g., a draft "Add" alongside a draft "Trim" for the same Case); not evidenced as required, not ruled out |
| No enforced uniqueness | Simplest to build; defers the question to a later product decision rather than the ontology |

**Tested against:** real investor behavior (plausible that an investor abandons stale reasoning and starts fresh rather than resuming it, arguing against a hard single-draft lock); UX-009 (silent on this question entirely); Decision immutability (irrelevant to cardinality-of-drafts specifically); future collaboration (a shared-Case scenario, which does not exist today, would make Case-scoped-alone cardinality ambiguous — "whose draft?" — arguing for investor-scoping from the outset even though nothing forces the question yet); Daily Brief discoverability (a strict one-per-Case cap keeps surfacing simple; many-per-Case would require UI complexity UX-009 never anticipates).

**Conclusion: not decided by any governing document.** Evidence leans toward the ontology itself not enforcing a hard cap, while acknowledging the current UX pattern behaves as though there is effectively one active line of reasoning at a time. Recorded as unresolved by evidence — a product decision, not an architectural one.

---

## Phase 14 — Daily Brief

UX-009's own text is minimal: "Drafts are surfaced in the Daily Brief as unresolved decisions." No granularity is specified beyond that.

| Candidate content | Classification | Why |
|---|---|---|
| Draft existence + subject/Case | **Required by existing UX** | The minimum that satisfies UX-009's own stated text — surfacing "an unresolved decision" necessarily names *which* one |
| A resume/next-action link | **Required by existing UX** | Implicit in the feature's own stated purpose — surfacing something unresolved without a way back to resolve it would not satisfy what UX-009 describes |
| Draft summary (excerpt of in-progress reasoning) | Optional future capability | Not specified by UX-009's minimal text |
| Draft age | Optional future capability | Not mentioned; plausible and low-risk, given this codebase's existing staleness-signal precedents elsewhere in Daily Brief/History |
| Outstanding questions within the draft | Optional future capability | Not required by UX-009's text |
| **Proposed decision / leaning** | **Inappropriate leakage, flagged explicitly** | Surfacing a half-formed, not-yet-committed leaning on a *separate* page risks presenting tentative private reasoning as more settled than it is — directly against `UX-008`'s own "Atlas must not... imply that analysis is complete when it is not," and against the privacy concern developed fully in Phase 15 |

**Architectural conclusion, not a UI decision:** the boundary UX-009 actually requires is a *narrow summary projection* (existence, subject, resume link) — not full draft content. This is consistent with how this codebase already exposes narrow, purpose-built read models elsewhere (Portfolio Cockpit, Case Intelligence) rather than raw domain objects to consuming surfaces, and it is the architectural shape a future implementation should target regardless of storage model.

---

## Phase 15 — Atlas Memory

UX-009 already states directly: **"Drafts do not enter Atlas Memory."** This is not derived here — it is the document's own explicit text, and it answers most of this phase before any further analysis.

- **Is an abandoned thought part of long-term memory?** Per UX-009's own text: no.
- **Is an unfinished draft evidence of investor reasoning?** Arguably yes in principle — `UX-008` §15's own Decision Memory concept cares about behavioral patterns, and a repeatedly-started-then-abandoned draft (e.g., on Reduce decisions for a core holding) could plausibly be a meaningful signal. **This is a real, disclosed tension, not resolved here:** UX-009's own text forecloses drafts from Atlas Memory as currently scoped, even though the content could in principle be meaningful to exactly the kind of pattern recognition this codebase already builds elsewhere (`Investigation-002`'s own Pattern/Strategy Signature lineage).
- **Should deleted drafts truly disappear?** Two different questions must be kept separate, and conflating them would be a mistake: *storage-layer retention* (crash-recovery, audit, consistent with Model B/C's own append-only event history) is not the same question as *product-layer memory-surfacing* (whether Atlas ever treats the content as part of the investor's remembered, surfaced history). UX-009's "do not enter Atlas Memory" answers only the second question.
- **Could preserving all drafts create surveillance-like behavior?** Yes, and this deserves to be taken seriously rather than dismissed. An Atlas that silently retains every abandoned, half-typed thought an investor ever had about a position — even if never shown back to them — is a materially different privacy posture than one that lets truly-abandoned reasoning genuinely go away. This is the same principle the Atlas Companion design (read in this session) already applied to its own `sessionStorage` choice: "session continuity... not durable memory... a durable, silently resurfacing week-old conversation would itself be a transparency problem." The same reasoning applies here, arguably at higher stakes, since draft content plausibly reveals genuine investment intentions the investor chose not to act on.
- **What should Atlas remember versus intentionally forget?** What becomes a real `Decision` (and, downstream, `DecisionContext`/`Outcome`) should be remembered permanently, per the existing immutable-aggregate philosophy. Abandoned draft content should *not* be treated as part of the investor's permanent, surfaced memory, consistent with both UX-009's own explicit text and the Companion precedent's own stated privacy reasoning. Whether the underlying storage nonetheless retains abandoned-draft *events* indefinitely for crash-recovery/audit, entirely separate from what is ever shown back to the investor as "memory," is a real, disclosed, and explicitly unresolved design tension.

---

## Phase 16 — Imported / Automated Decisions

`Decision.source` already carries four values: `MANUAL`, `IMPORT`, `BROKER_SYNC`, `API` (confirmed directly, `decision/value_objects.py`). A broker-imported trade, an API-created Decision, and any future automated workflow all construct a `Decision` directly via `Decision.register(source=..., ...)`, with no draft ever having existed — this is not hypothetical, it is how three of the four existing source values already work today. Migrated historical Decisions are further, directly evidenced by `Investigation-002`'s own ATLAS-009B finding: historical Decisions were retroactively reconciled to carry a durable `user_id` *without* ever needing a retroactively-constructed draft — direct precedent that "Decision without a preceding draft" is an already-solved, legitimate case in this codebase, not a hypothetical this investigation is inventing.

**Must every Decision have a draft? No — decisively, on strong existing evidence.**

**Implication for cardinality/provenance:** any future draft-to-Decision link (per Phase 11's `draft_id` discussion) must be optional, following the exact same pattern `Decision.observation_id` already uses — never required, since a majority of `DecisionSource` values structurally cannot and should not ever have one. **A draft architecture that made every Decision require a preceding draft would be directly incompatible with this codebase's own already-existing `DecisionSource` taxonomy — a hard constraint any future design must respect, not a preference.**

---

## Phase 17 — Alternative Architectures

### Option A — No persisted draft (transient UI state only)

Clean, adds nothing to the ontology, zero migration cost — but **fails UX-009's own explicit Daily Brief requirement directly** (Phase 3): transient, single-session state cannot appear on a different page in a later session by construction. Failure mode: silent data loss on refresh/device change/session end, in real tension with `UX-008`'s own insistence that the Workspace "feel appropriate... when revisited years later."

### Option B — Decision has DRAFT status (same aggregate evolves)

Fails Phase 1 outright — an "incomplete Decision" is not a coherently definable object, since `Decision`'s own constructor requires every field populated already. Worse than a mismatch: it would make the previously-immutable `Decision` itself mutable, directly contradicting `ReflectionResponse`'s own stated safety invariant ("valid because a Decision, once recorded, never changes") and untold existing tests/consumers that currently trust Decision never changes after being read. The single most severe failure mode of any option evaluated.

### Option C — Separate DecisionDraft aggregate

Matches every finding from Phases 1, 6, 7, 8, 9: pre-Decision, editable, investor-authored, Case-scoped (not Case-owned), structurally distinct from every existing object. Preserves `Decision`'s immutability completely untouched. Follows an already-proven shape in two dimensions at once: structurally closest to `DecisionContext` minus its Decision-dependency; lifecycle-mechanically closest to the already-shipped `SecurityConfirmationEvent`/`ConfirmedSecuritySelection` pattern (Phase 10). Fully additive — no migration to any existing object. Satisfies UX-009's Daily Brief, panel-re-entry, and multi-day requirements via ordinary server persistence, with the narrow-projection boundary Phase 14 already established. The only disclosed risk is scope creep (letting it prematurely accumulate every UX-009 field) — real, but not fatal, and not triggered by this investigation's own no-implementation scope.

### Option D — DecisionContext doubles as draft

Already decisively rejected in Phase 6, on two independent structural grounds. Not re-argued here.

### Option E — Generic Case Workspace State

Superficially appealing, but Phase 8 already found it collapses into Option C once examined — the only real difference is a less honest label that avoids acknowledging the concept as its own domain object. Risks becoming exactly the "dumping ground" `Architecture-Resolution-Sprint-1.md` explicitly warned the Decision Workspace itself against, one level down. Weaker contract than C (no inherent expectation of append-only history, no explicit invariants) for no offsetting benefit. Risks under-protecting genuinely significant content (an investor's own investment reasoning) by treating it identically to ordinary UI chrome (scroll position, expanded-section state — `UX-012`'s own "nine elements" list already mixes these together, a conflation this option would import rather than avoid).

### Option F — Event-only draft stream (no current-state projection)

Consistent with the append-only philosophy, but Phase 10 already found this is Model B *without* Model C's own read-side optimization — and the Security Confirmation precedent deliberately did not stop at events alone; it built `ConfirmedSecuritySelection` specifically because raw event-replay on every read is worse for every ordinary consumer (a resumed panel, a Daily Brief summary). Strictly dominated by Option C built on Model C, not an independent, competitive alternative.

---

## Phase 18 — Consistency Test

Challenging Option C directly, against every named neighbor, documenting rather than resolving:

- **vs. Decision immutability:** no contradiction — `Decision` untouched; structurally incapable of confusion with a draft, per Phase 1's own constructor argument.
- **vs. DecisionContext 0..1:** no contradiction — a `DecisionDraft` would reference `case_id` (or investor + case), never `decision_id`, avoiding any collision.
- **vs. ReflectionResponse:** no contradiction — different trigger, different temporal position, no shared reference.
- **vs. Outcome / Trade:** no contradiction — both strictly post-Decision, unrelated content.
- **vs. Case:** a real point worth stating precisely, not assumed away — does a `DecisionDraft` referencing `case_id` directly violate `Case`'s own "does not depend on... Decision, Outcome, Judgment..." independence principle? Examined carefully: that principle governs `Case` not *requiring* those objects to exist — it says nothing about *other* objects referencing `Case`. `Decision` itself already carries a direct `case_id`, an accepted, existing precedent; a `DecisionDraft` doing the same would follow `Decision`'s own precedent, not `DecisionContext`'s narrower, transitive-only one. No contradiction, but the precedent being followed must be named correctly.
- **vs. KnowledgeReference / ReasoningTrace:** no contradiction — confirmed disjoint shape across both prior investigations, unaffected here.
- **vs. Daily Brief:** no contradiction, *given* Phase 14's narrow-projection conclusion is respected; a future implementation exposing full draft content to Daily Brief instead would reintroduce the "inappropriate leakage" finding — a design-discipline requirement, not an ontology-level conflict with Option C itself.
- **vs. History:** ATLAS-004's own Decision Timeline depends only on `Decision`/`Outcome`/`Evaluation`/`Learning` repositories — a `DecisionDraft`, being pre-Decision, would not appear there, consistent with Phase 15's "do not enter Atlas Memory" finding. No contradiction, but a real, disclosed consequence worth naming: an abandoned draft would leave no trace in History/Decision Timeline at all, by design, not by omission.
- **vs. Atlas Memory:** consistent with Phase 15 — storage-layer persistence (for Daily Brief, crash-recovery) is compatible with *not* treating the content as part of the investor's permanent, surfaced memory. Option C is compatible with either resolution of that tension; it does not itself resolve it.
- **vs. Portfolio:** no contradiction — no relationship to Portfolio Intelligence, same as every other object tested.
- **vs. imported Decisions:** no contradiction — confirmed directly in Phase 16; Option C's own natural shape (an optional provenance link, per the `observation_id` precedent) accommodates `IMPORT`/`API`/`BROKER_SYNC` Decisions with zero special-casing.
- **vs. future collaboration:** a genuine, disclosed open risk, not a present contradiction — Phase 13 already found a Case-scoped-only draft model becomes ambiguous ("whose draft?") the moment multi-user access to a shared Case exists, which nothing in this codebase supports today. Flagged, not resolved.
- **vs. offline/mobile editing:** a genuine, disclosed open question — no offline-sync mechanism exists anywhere in the current frontend (confirmed: no service worker, no offline queue found). Model C's synchronous, server-persisted shape would need real additional design for offline-first editing, not evidenced or resolved by anything read for this investigation.

**Two contradictions/tensions documented, not resolved, per instruction:** the Case-scoping-only model's future ambiguity under multi-user access; and the storage-retention-vs-product-memory tension from Phase 15, which Option C leaves open rather than settles. Two further genuinely *unaddressed* (not contradictory) questions are carried forward: offline/mobile editing, and Daily Brief's exact granularity beyond the evidence-grounded minimum already established in Phase 14.

---

## Phase 19 — Architecture Decision

**`SEPARATE_DECISION_DRAFT`**

**This requires new ontology, stated explicitly per instruction.** No existing object — `DecisionContext`, `ReflectionResponse`, `Case`, `Observation`, `Question`, `Conclusion`, `ReasoningTrace`, `Judgment`, every one tested directly in Phases 6–9 — can hold pre-Decision, editable, investor-authored draft content without either violating its own stated immutability (every single case) or requiring a precondition (an already-existing `Decision`) a pre-Decision concept cannot satisfy by definition. This is not a preference among comparably-valid options; Phases 6 through 9 each independently reached a structural, evidenced incompatibility, not a stylistic one. Given this investigation's own instruction not to add new ontology *unless the evidence concludes one is required*, and given that conclusion is now reached by direct, repeated, structural evidence rather than speculation, the honest answer names it rather than works around it.

---

## Phase 20 — ADR Candidate (Outline Only)

**Problem:** UX-009 requires Save-as-Draft with cross-session, Daily-Brief-visible persistence. No existing domain object can hold this content without violating its own stated invariants.

**Context:** `Decision` is immutable by explicit design and cannot represent an incomplete commitment (Phase 1). `DecisionContext` and `ReflectionResponse` both require an already-existing `Decision` and are both themselves immutable (Phases 6–7). `Case` is deliberately content-free (Phase 8). No earlier Core Loop object fits either shape or authorship (Phase 9). This codebase already has a proven pattern for mutable-seeming, auditable state — the `SecurityConfirmationEvent`/`ConfirmedSecuritySelection` append-only-events-plus-derived-projection model (Phase 10) — and a proven precedent for optional, additive provenance fields on `Decision` itself (`observation_id`, Phase 11).

**Decision:** Adopt a new, minimal, illustratively-named `DecisionDraft` concept — Case-scoped (following `Decision`'s own direct `case_id` precedent, not `DecisionContext`'s narrower one), built on the append-only-events-plus-derived-current-state pattern already proven by Security Confirmation, not a novel persistence philosophy.

**Invariants (illustrative, not binding — no schema decided here):**
- References `case_id` and investor identity, never `decision_id` (none exists yet).
- Content is investor-authored only, mirroring the field shapes it will eventually help populate on `Decision`/`DecisionContext`.
- "Current state" is always a derived projection over an append-only event stream, never a directly-mutated row.
- The commit boundary is the existing, unmodified `Decision.register()`/`DecisionContext.capture()` calls — the draft object itself never *becomes* a Decision; it only supplies the arguments to construct one.
- Daily Brief consumes only a narrow summary projection (existence, subject, resume link) — never full draft content (Phase 14).

**Consequences:** `Decision`'s immutability, and every object that already relies on it (`ReflectionResponse`, Security Confirmation, Decision Timeline), remains completely untouched. `DecisionContext`'s 0..1-per-Decision invariant is undisturbed. Imported/API/BrokerSync Decisions remain fully valid with zero draft involvement (Phase 16). A future optional `draft_id` provenance field on `Decision`, should it ever be wanted, would follow an already-accepted pattern, not establish a new one.

**Rejected Alternatives:** A (fails the Daily Brief requirement outright); B (destroys `Decision`'s core invariant and everything downstream that relies on it — the most severe failure of any option); D (fails on two independent structural grounds); E (collapses into C once examined, with a weaker contract); F (strictly dominated by C, per Security Confirmation's own design choice not to stop at raw events).

**Migration/Compatibility:** None required to any existing object. Fully additive.

**Open Questions** (carried forward, not resolved here):

1. Is a recorded-and-superseded draft retained as provenance, or discarded? (Phase 4, 11)
2. Are "abandon" and "delete" the same action, or two? (Phase 12)
3. Should drafts ever expire? (Phase 4, 12)
4. Should multiple simultaneous drafts per Case be permitted, or capped at one? (Phase 13)
5. Should the Case-scoped-only model be revisited before any future multi-user/collaboration capability is built? (Phase 18)
6. Should abandoned-draft events be retained indefinitely at the storage layer even though their content never enters investor-facing Atlas Memory — and if so, for how long, and under what access controls? (Phase 15, 18)
7. Does offline/mobile editing ever need to be supported, and if so, does Model C's synchronous shape need a local-first layer? (Phase 18)
8. Should `Decision` eventually gain an optional `draft_id` field, following the `observation_id` precedent? (Phase 11)
