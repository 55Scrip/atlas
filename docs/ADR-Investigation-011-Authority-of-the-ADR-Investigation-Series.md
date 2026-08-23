# ADR Investigation 11 — Authority of the ADR Investigation Series

**Status:** Investigation only. No implementation, API, UI, schema, or migration accompanies this document. This investigation does not decide whether any prior investigation was correct — it determines what these documents are actually allowed to do.

**Central question:** What are the ADR Investigation documents (`Investigation-001` through `010`, and this one) actually allowed to do?

**Method:** This investigation is genuinely self-referential — its primary evidence is the actual, observable behavior of the ten prior documents, verified fresh by direct inspection rather than recalled from memory. Three greps were run against all ten files on disk: (1) every document's own self-declared `Status:` line; (2) whether any document ever claims "Final," "binding," or "normative" status for itself (none found); (3) whether every "ADR Candidate" section is labeled "Outline Only" (confirmed, all four occurrences across the documents that reach that phase). A fourth check confirmed `Investigation-010` alone cites prior investigations by exact document name twenty-three times. These are facts about the corpus, not interpretation, and they ground every phase below.

---

## Phase 1 — What Is an Architectural Investigation?

Testing each candidate against the verified empirical record, not assumption:

| Candidate | Verdict | Why |
|---|---|---|
| Research | Partial fit | Systematic, fresh evidence-gathering happens in every document — but "research" alone doesn't capture the decisive, single-verdict structure every one reaches |
| Architecture | **Fails** | Confirmed by direct grep: zero of ten documents ever claims Final, binding, or normative status for itself. "Architecture," in this codebase's own vocabulary (per `Investigation-009`/`010`), means precisely the normative force these documents uniformly, explicitly decline |
| Governance | Partial fit, narrow | True of `Investigation-009`/`010` specifically, which are *about* governance — but doesn't characterize the other eight, which are substantive ontology investigations |
| Design | Fails | No implementation design is ever proposed; every document states "No implementation... no schema" |
| Implementation | Fails | Zero implementation ever produced — confirmed by ten separate working-tree verifications, each showing no tracked-file change |
| Documentation | Too weak | Undersells the argumentative work — these documents test alternatives and reject them with stated reasons; documentation alone only records |
| Analysis | Close, incomplete | Analysis doesn't require a decisive, single-option verdict; every one of these documents reaches exactly one anyway |
| **Something else** | **Survives** | See below |

**The surviving characterization:** an Architectural Investigation is a **research-grade recommendation document** — argued with the same rigor architecture requires (evidence tested, alternatives rejected with stated reasons, contradictions disclosed rather than hidden), but structurally, deliberately withholding the one thing that would make it architecture: a claimed Final or binding status. This is a genuinely distinct genre from any single candidate above — closer to a fully-reasoned brief prepared *for* a decision than to the decision itself.

---

## Phase 2 — What Does an Investigation Produce?

| Output | Legitimate? | Evidence |
|---|---|---|
| Observations | Yes | Every investigation makes these (e.g., "OE-002's own closure claim exists") |
| Evidence | Yes | Every investigation cites specific files, lines, or quoted passages |
| Architectural conclusions | Yes, in a weak, non-binding sense | A reasoned position is reached, never claimed as *the* architecture |
| Recommendations | **Yes — the primary legitimate output** | Matches Phase 1's characterization directly |
| ADR candidates | Yes, but always labeled "Outline Only" | Confirmed: 4/4 occurrences of exactly this label, never presented as the ADR itself |
| Normative decisions | **No** | Confirmed empirically: zero self-claims of Final/binding/normative status across all ten documents |
| Implementation work | **No** | Confirmed empirically: zero tracked-file changes across ten working-tree verifications |

---

## Phase 3 — Can an Investigation Itself Establish Architecture?

Testing each candidate directly:

- **Never:** too strong — if investigations could never inform architecture even after further process, they would be pointless; their own stated purpose (feeding into eventual decisions) would be incoherent.
- **Always:** directly falsified by the empirical record (Phase 1/2) — and self-contradictory, since being an "investigation" (as opposed to an ADR) is *defined* by withholding this exact claim.
- **Only after approval:** plausible but underspecified — "approval" by whom is never named anywhere in any track's own doctrine.
- **Only after reconciliation:** correct specifically for cross-track claims (per `Investigation-010`'s own Phase 5/8 findings), but narrower than the general case — many investigation conclusions don't conflict with anything yet, and still need a path to becoming architecture.
- **Only after conversion into an ADR:** **the precise, surviving answer.** This is exactly how this series has already, consistently, treated its own proposed ontology — `Investigation-003`, `006`, and `007` each proposed genuinely new concepts (Draft, CaseCondition, Assumption) and in every case labeled them "illustrative, not binding," "no schema decided here," offering an "ADR Candidate (Outline Only)" as the handoff artifact for a later, separately-authored, formal act.

**"Only after approval" and "only after reconciliation" are both true, but as special cases of this more general rule** — approval is the review step inside ADR conversion; reconciliation is the specific conversion process required when a claim crosses tracks.

---

## Phase 4 — Can an Investigation Invalidate an Existing ADR?

**No, not by itself.** Directly reapplying `Investigation-010` Phase 10 (Supersession) one level up: supersession requires "an identified replacing decision" carrying an explicit status change — never a mere claim. An investigation, by Phase 1's own definition, structurally withholds the very status claim supersession requires the *replacing* document to carry.

**Under what conditions can it contribute to eventual invalidation?** An investigation can name a genuine forcing function (Domain Object Architecture Doctrine §8's own vocabulary: a newly identified domain fact, an unavoidable contradiction, a demonstrated expressive gap) that makes an existing ADR *worth reopening* — but the actual reopening and any resulting supersession must happen through that ADR's own governing track, producing a document that does claim the requisite status, which an investigation never does.

**Directly observed in this series' own practice, not merely theorized:** `Investigation-009` found a genuine tension in Judgment's three definitions; `Investigation-010` explicitly did not declare any of them invalidated — it named the ambiguity as unresolved (its own Phase 7/16). The series already follows this rule in practice, before this investigation states it as one.

---

## Phase 5 — Can an Investigation Establish Ontology, or Only Recommend It?

Only recommend — a direct corollary of Phase 3/4. Confirmed, not merely inferred: `Investigation-003`, `006`, and `007` each proposed new ontology and in every case explicitly declined to treat the proposal as established, consistently using "illustrative, not binding" language and a dedicated non-binding outline section. This is the series' own demonstrated practice, now named explicitly for the first time rather than left implicit.

---

## Phase 6 — What Evidence May an Investigation Legitimately Use?

Directly reapplying `Investigation-010` Phase 6's own findings (which asked this identical question about reconciliation specifically), generalized here:

| Evidence type | Status |
|---|---|
| Implementation, tests, commit history | Legitimate for fact-finding; never sole ground for an ontological verdict |
| Doctrines, ADRs | Legitimate, weighted highly |
| OE / design documents | Legitimate as comparative material, never as binding on the investigation's own conclusion |
| Discussions | **Not observed as a category this series actually uses** — every citation across all ten documents traces to a specific, checkable, written source; nothing is grounded in unwritten discussion or verbal understanding. A real, positive, freshly-verified discipline this series has practiced beyond what any doctrine required. |
| Experiments | Not applicable — these are documentation-only investigations; none runs an experiment |
| Historical implementation | Legitimate for fact-finding, same status as commit history |
| Previous investigations | **Legitimate and heavily used** — confirmed 23 cross-references in `Investigation-010` alone, consistently treated as "established unless directly contradicted," matching the explicit instruction given at the top of `Investigation-008` onward |

---

## Phase 7 — How Should Investigations Interact With Existing Tracks?

| Relationship | Verdict |
|---|---|
| Govern | **No** — never claimed, confirmed empirically |
| Advise | **Yes, primarily** — matches Phase 1's characterization exactly |
| Reconcile | **Partially** — `Investigation-009`/`010` performed reconciliation-*adjacent* work (naming and analyzing cross-track disagreement) but, per Phase 4, could not and did not complete any actual reconciliation; they advise on reconciliation, they do not perform it |
| Observe | **Yes, extensively** — the bulk of every investigation (the "re-establish," "existing objects," "compare against" phases common to all ten) is genuinely observational |
| Replace | **No** — never once |
| Remain independent | **True of method, not of authority** — the series is methodologically its own thing (per `Investigation-010` Phase 15/16's own "fourth quasi-track" finding), but its eventual normative force always requires conversion through one of the three existing tracks' own processes (Phase 3) |

---

## Phase 8 — Can Investigations Disagree With Existing Architecture?

**Yes, and this has already happened repeatedly** — `Investigation-009` found the implemented ontology diverges from OE-002's closed set; `Investigation-003`/`006`/`007` proposed ontology neither existing track has. **What happens next, per this series' own consistent, already-demonstrated practice: the disagreement is named precisely, documented as a real finding, and left as an explicit open question or unresolved tension — never silently smoothed over, never treated as automatically resolved in the investigation's own favor.** Disagreement is a legitimate, expected, already-repeatedly-exercised output; its *resolution* is explicitly, consistently deferred to a track's own formal process (Phase 3/4).

---

## Phase 9 — Should Investigations Ever Become Normative?

Yes, but only through conversion into an ADR within an appropriately governed track — a human or agent with the authority to author a Draft/Final ADR (Track 2's model), an OE-series document (Track 3's model), or an actual implementation sprint (Track 1's model) takes the investigation's own reasoning as *input*, and produces a new, separately-authored, appropriately-statused document through that track's own process. **The investigation itself never self-converts.** Mere continued existence as a committed file is explicitly insufficient — directly matching `atlas_domain_object_architecture/Doctrine.md` §3's own anti-inflation principle ("A candidate category MUST NOT be accepted on the grounds that... it appears in a workflow or process description"), reapplied here to the investigation documents' own status rather than to a domain object.

---

## Phase 10 — What Constitutes Completion?

Testing each candidate against the empirical record:

- **Evidence exhausted:** never claimed — every investigation is scoped to a specific, narrow question, not to exhausting all possible evidence about a topic.
- **Contradictions are documented:** **yes, consistently required and consistently satisfied** — every investigation's own Consistency Test phase instructs "document, don't resolve," and every one complies (confirmed: every document contains at least one "not decided here"/"carried forward" instance).
- **A preferred model exists:** **yes, consistently required** — every investigation's own Final Decision phase names exactly one preferred option.
- **Implementation agrees:** **never required, never checked** — no investigation verifies its conclusion against subsequent implementation, since none is ever produced.
- **Something else, precisely stated:** an investigation is complete when (a) its own narrowly-scoped central question has been answered with a single, justified, named verdict; (b) every tested alternative carries a stated reason for rejection; (c) every genuine contradiction or open question found is named explicitly rather than smoothed over; and (d) an ADR-candidate outline is produced as the handoff artifact for whoever eventually performs formal conversion (Phase 9). **This is the four-part criterion the series has already, consistently applied to itself across all ten prior documents — stated explicitly here for the first time.**

---

## Phase 11 — Should Investigations Be Permanent?

Directly reapplying `Investigation-010` Phase 10/11 (Supersession, Historical Integrity), now reflexively, to the series itself — precisely the question `Investigation-010`'s own Open Question #2 left open.

- **Permanent?** Yes, in the same sense every track's own historical record is permanent — `atlas_domain_object_architecture/Doctrine.md` §11, reused: "the historical trail of decisions... MUST remain recoverable at all times... A historical record MUST NOT become a competing source of current normative truth" but must never be erased.
- **Superseded?** Yes, legitimately and expectedly — if a later investigation (or an eventual formal ADR) reaches a different, better-evidenced conclusion on the same narrow question, the earlier one should be marked, not deleted, as superseded by the later one.
- **Archived / retired?** Treated as synonymous with the existing Historical status (§14) rather than as a new category — no demonstrated need for a distinct concept was found.
- **Deleted?** **No, never** — directly contradicted by every track's own historical-integrity principle, and by this series' own actual, observed practice: `Investigation-009` corrected `Investigation-008`'s own two-track framing to three, and `Investigation-008` was not deleted — it remains fully readable, its refinement stated explicitly rather than erased.

---

## Phase 12 — Can Investigations Contradict Each Other?

**In principle, yes.** Testing whether this has actually happened: `Investigation-009`'s refinement of `Investigation-008`'s framing (two tracks named, a third later found) is, on inspection, not a true contradiction under `Investigation-010`'s own precise Phase 7 test (two claims *both* claiming settled status about the same fact that cannot both be true) — `Investigation-008` never positively asserted "there are exactly two tracks and no more" as a tested finding; it simply had not yet discovered the third. **No genuine contradiction between investigations has occurred in this series' actual history — only refinement and extension.**

**If a genuine contradiction were to occur, the correct resolution process is the same one `Investigation-010` already established for cross-track disagreement generally:** name it explicitly, do not silently resolve it, and treat it as requiring either a third, later investigation that directly tests which claim survives (using the same evidence-based method), or eventual resolution only upon formal ADR conversion (Phase 9) by whichever track adopts the relevant conclusion. Investigations have no separate conflict-resolution mechanism of their own beyond the ordinary practice — already exercised throughout this session — of writing a new investigation that re-tests a disputed claim directly rather than assuming it.

---

## Phase 13 — Should Investigations Have Their Own Governance?

Testing directly: does the series need a new, bespoke doctrine, or can it borrow an existing track's vocabulary?

Testing "needs a new doctrine": `atlas_domain_object_architecture/Doctrine.md`'s own §3 (reused a third time in this series) explicitly warns against accepting a new category merely because it seems useful or appears in a workflow — the same anti-inflation discipline argues against inventing a bespoke doctrine for the investigation series *unless* a demonstrated gap in existing vocabulary is found.

**Testing whether such a gap exists:** the vocabulary actually needed — Draft/Final/Superseded/Historical status (§14); a reopening condition (§8); supersession requiring an identified replacing decision (§14); historical-integrity guarantees (§11) — is already precisely available, and reusable without modification, from the same track `Investigation-010`'s own Phase 17 (Model G) already recommended borrowing *by method* for general cross-track reconciliation.

**Conclusion: existing governance is sufficient. A new, bespoke doctrine is not justified — no demonstrated gap was found that the existing vocabulary cannot already express.** What is missing, and what this investigation now supplies, is simply an explicit statement that the series *adopts* this borrowed vocabulary for itself — a naming and registration act, not a new invention.

---

## Phase 14 — Governance Models

| Model | Verdict |
|---|---|
| A — Research only | Too weak — undersells the decisive, single-verdict structure and the ADR-candidate outlines every investigation actually produces |
| **B — ADR precursor** | **Matches Phase 1, 3, and 9 precisely** — investigations are the input stage to a track's own ADR process, never the ADR itself |
| C — Architecture authority | Directly falsified — zero self-claimed binding status anywhere |
| D — Independent reconciliation track | Too strong — Phase 4/8 show investigations can name and prepare for reconciliation but cannot complete it independently |
| E — Living investigation archive | Partial fit — captures Phase 11's permanence finding, but "archive" alone undersells the forward-looking, decision-directed character every investigation carries |
| F — Temporary working documents | Directly contradicted by Phase 11 — "temporary" is the wrong word entirely; nothing in this series is ever deleted |
| **G — Permanent ADR-Precursor Record** | **The complete, accurate synthesis of B + E** — B's precise functional role (input to a track's own formal process) combined with E's correct historical-permanence property (never deleted, superseded-not-erased) |

---

## Phase 15 — Consistency Test

Testing Model G against the named list:

- **Investigation 1–10:** self-consistent — Model G describes exactly how they have already, empirically behaved (Phases 1–13's own evidence, not a new constraint imposed on them retroactively).
- **Core Loop:** no conflict — investigations observe and advise, never govern (Phase 7).
- **Reasoning Foundations / Domain Object Architecture:** no conflict — investigations borrow method (Phase 13) without claiming either track's own content or authority.
- **ADR process / OE process:** complementary — investigations feed these processes as evidence and candidates (Phase 9), never substitute for them.
- **Implementation:** no conflict — zero implementation ever produced or claimed.
- **Future Atlas governance:** Model G leaves the series a clean, stable, well-defined role going forward, independent of whether the still-open Track 1 ↔ Track 3 reconciliation (`Investigation-010`'s own recommendation) is ever undertaken.

---

## Phase 16 — Unresolved Tensions, Disclosed Honestly

1. **A real, growing backlog exists between production and conversion.** No actual "conversion into an ADR" (Phase 9) has ever happened for any of this series' own proposed conclusions — Draft, CaseCondition, Assumption, the Section-3 ownership conflict, and more — the series has produced candidate material far faster than anything has been formally adopted. Not resolved here.
2. **This investigation answers, rather than reverses, `Investigation-010`'s own Open Question #2.** `Investigation-010` named the series as methodologically track-like but explicitly left its *authority* status as an open question, never asserting the series held peer authority alongside the other three tracks. This investigation answers that specific open question (advisory input, per Model G — not peer authority) rather than contradicting a settled prior conclusion. Stated precisely so the distinction is not mistaken for reversing a decision that was never actually made.
3. **No owner has been named for the conversion step itself.** The same "who does this work" gap `Investigation-010` Phase 16 flagged for cross-track reconciliation applies equally, and separately, to converting any single investigation's own findings into a real ADR within any track. A second instance of the same practical gap, not newly resolved here.
4. **Phase 12's proposed contradiction-resolution process is untested in practice** — no genuine contradiction between investigations has yet occurred, so whether "write a third, testing investigation" actually works when one is needed remains a reasoned expectation, not a demonstrated fact.

---

## Phase 17 — Preferred Governance Model

**Model G — Permanent ADR-Precursor Record.**

---

## ADR Candidate (Outline Only)

**Problem:** The ADR Investigation series has produced ten substantive documents with real, evidence-grounded conclusions, but its own authority and status have never been explicitly defined — risking either silent over-reliance (treating an investigation as if it were already binding) or silent under-use (treating the series as disposable scratch work, contrary to its own demonstrated rigor).

**Context:** Direct inspection of all ten prior documents shows a uniform, self-limiting practice already in place — every document declares itself "Investigation only," none claims Final/binding/normative status, every ADR Candidate section is explicitly labeled "Outline Only," and every genuine contradiction found is documented rather than resolved. This investigation formalizes what the series has already been doing, rather than introducing a new constraint.

**Decision:** The ADR Investigation series is a Permanent ADR-Precursor Record (Model G). It observes and advises; it never governs, replaces, or self-converts into architecture. Its documents borrow, without formally subordinating themselves to, the status/supersession/historical-integrity vocabulary already defined by `atlas_domain_object_architecture/Doctrine.md` §8, §11, and §14. Becoming architecture always requires a separate, later act of conversion, performed by an appropriately authorized track.

**Invariants:**
- No investigation document may claim Final, binding, or normative status for itself, now or in any future document in this series.
- Every ADR Candidate a future investigation produces remains explicitly labeled an outline, never presented as the ADR itself.
- No investigation is ever deleted; a later investigation or formal ADR that reaches a different conclusion on the same narrow question supersedes the earlier one explicitly, leaving it fully readable.
- Every genuine contradiction, whether found against an existing track or against a prior investigation, is documented, never silently resolved by the investigation that finds it.
- Conversion into architecture is always performed by a separately-authorized track's own process, never by the investigation itself.

**Consequences:**
- **Reasoning:** future investigations may cite this document as the settled answer to "what is an investigation allowed to do," rather than re-deriving it each time.
- **Decision Workspace:** unaffected — every finding across `Investigation-001`–`010` remains exactly as valid as before this document.
- **Atlas Memory / Daily Brief / future governance:** unaffected directly, though the newly-named conversion backlog (Phase 16, item 1) is now visible to whoever next considers formalizing any of this series' own proposals.
- **Future ADRs:** gain an explicit, reusable status model rather than each needing to reason about the series' own authority from scratch.

**Rejected Alternatives:** A (research only — undersells the decisive, verdict-producing structure actually observed); C (architecture authority — directly falsified by the empirical record); D (independent reconciliation track — overstates what investigations have ever actually completed); E (living archive alone — correct on permanence, incomplete on function); F (temporary working documents — directly contradicted by the series' own practice of never deleting anything).

**Migration/Compatibility:** None required. This decision formalizes existing, already-uniform practice; no prior document needs to change.

**Open Questions** (carried forward, not resolved here):

1. Who owns and performs the actual conversion of any given investigation's findings into a formal ADR within its relevant track, and on what timeline? (Phase 16, item 3 — the same practical gap `Investigation-010` already named for cross-track reconciliation, now shown to recur at the single-investigation level too)
2. How should the growing backlog between investigation output and formal conversion (Phase 16, item 1) be managed as the series continues to grow?
3. Is "write a third, testing investigation" (Phase 12) an adequate mechanism for resolving a genuine future contradiction between two investigations, given none has yet tested it in practice?
4. Should this document itself, once it exists, be treated as the authoritative statement of the series' own status going forward, or does it remain subject to the same non-binding, advisory status Phase 1–9 establish for every other investigation — including this one, about itself?
