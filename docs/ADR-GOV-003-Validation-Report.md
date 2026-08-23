# ADR-GOV-003 Validation Report

**Sprint:** ADR Adoption Program, Sprint 4 — ADR Validation Review.
**Subject:** `ADR-GOV-003-Investigation-Lifecycle.md`.
**Method:** Re-read the ADR fresh against `Atlas-Recommendation-Register.md`, `Atlas-Governance-Adoption-Review.md`, `docs/ADR-Investigation-011`, and the two sibling ADRs, applying the eight-part validation framework.

**Process note:** Same disclosure as the other two reports — this ADR was marked `Accepted` before any validation gate existed. Corrected as part of this report's disposition.

---

## 1. Scope Validation

**Does the ADR answer exactly one architectural problem?** Yes — "what is an Investigation, and how do its findings become architecture." Every Decision point supports this question.

**Has any content drifted in that belongs in another ADR?** §6 (no deletion, explicit supersession) correctly defers to `ADR-GOV-002` §6 rather than restating it — good discipline, no drift. §4's conversion-path enumeration (implementation / Reasoning Foundations / Domain Object Architecture / governance ADR) names all three other tracks, which is necessary here since this ADR's own subject is precisely how an Investigation's findings reach any of them — not drift.

**Is the scope appropriately narrow?** Yes.

---

## 2. Normative Validation

Checked point by point:

- §1, §3 (Investigation = research-grade recommendation document; series is advisory input, not a peer track): trace directly to `INV11-R1`, `INV11-R8`, and the paired resolution of `INV10-R7`. Well-grounded.
- §4 (conversion requires an authorized track's own process): `INV11-R6`, direct match.
- §5 (ADR Candidate = outline only): `INV11-R4`, direct match.
- §6 (no deletion): `INV11-R5`, direct match.

**A significant finding on §2 (the Open/Complete/Converted/Superseded status model).** Checked against every Sprint-2-approved recommendation individually: **no single `INV11-R` item, and no item from Investigations 009 or 010, states this specific four-value taxonomy.** Its components are real and traceable individually — `INV11-R1` establishes the series has its own lifecycle in general terms; `Investigation-011`'s own Phase 10 states a four-*criterion* test for when an Investigation is complete (a question answered, alternatives tested, contradictions disclosed, an outline produced) — but that is a completion *test*, not a named status *label*, and it does not include "Open," "Converted," or "Superseded" as terms at all. The specific four-label taxonomy in §2 is new synthesis performed during this ADR's own drafting in Sprint 3, not a verbatim conversion of an approved recommendation.

This is not necessarily wrong — turning a general, approved principle into a concrete, followable rule is legitimate ADR-drafting work, and Sprint 2 itself required exactly this kind of concretization for `INV10-R1`'s forcing-function criteria. But per this validation's own governing question — "has any new normative rule been introduced that was not actually adopted during Sprint 2" — the honest answer for §2's specific taxonomy is: **partially yes**, and it should be disclosed as synthesis rather than presented as if drawn directly from an approved recommendation, exactly as the Context section currently implies by citing only `INV11-R1` through `R9` without distinguishing which parts are direct conversions and which are new operational structure built to make an approved principle followable.

**A related finding: §7 (traceability requirement).** The same issue, smaller in scale: no single `INV11-R` item states "every Investigation must cite its specific phase and evidence" as its own discrete recommendation. This describes real, observed practice (documented in `Investigation-011` Phase 6 and the Register's own "Method note") rather than a separately-voted-on item. Lower-stakes than §2, since it codifies uncontested, already-uniform behavior rather than introducing new structure, but it should be traced to its actual source (`Investigation-011` Phase 6, and the Register itself) rather than left implicitly bundled into the general `INV11` citation.

---

## 3. Consistency Validation

**Does the ADR conflict with `ADR-005`?** No — no relevant overlap; `ADR-005` does not address the Investigation Series.

**Does it conflict with any existing Doctrine?** No — `INV11-R2`'s own principle (reuse existing vocabulary rather than inventing a bespoke doctrine) is respected in spirit for supersession (§6, deferring to `ADR-GOV-002`), though see the §2 finding above for where new vocabulary was nonetheless introduced.

**Does it conflict with previously adopted architectural decisions?** Checked against `ADR-GOV-001`: §4 correctly applies, rather than contradicts, `ADR-GOV-001`'s own general no-self-conversion principle. Checked against `ADR-GOV-002`: the status-vocabulary overlap already identified in the `ADR-GOV-002` validation report applies symmetrically here — `ADR-GOV-002` §7's Draft/Final/Superseded/Historical vocabulary and this document's own Open/Complete/Converted/Superseded vocabulary share "Superseded" but are not otherwise reconciled. Restated here, not re-argued, since it is the same finding viewed from the other side.

**Internal contradictions within this document?** **Yes, a real one, found on close reading of §2.** The section's opening sentence states an Investigation "carries one of the following statuses" — language implying a single, exclusive value at any given time. The very next paragraph states these statuses "are not mutually exclusive across an Investigation's own lifetime... a Complete Investigation may later become Converted... and, independently, portions of it may later become Superseded" — language implying an Investigation can hold more than one status concurrently (e.g., Complete *and* Converted at once). **These two statements are in tension as written**: "carries one of the following" reads as a strict enumeration; "not mutually exclusive" reads as compound, simultaneous tagging. The intended meaning is almost certainly "an Investigation's status can change over time, and a later status does not erase an earlier true one" — but as literally written, a careful reader cannot tell whether §2 describes a linear progression (Open → Complete → Converted → Superseded, one value at a time) or an accumulating set of independent tags. This needs clarification, not because the underlying idea is wrong, but because the current wording genuinely supports two different readings.

---

## 4. Minimality Validation

**Can anything be removed without changing the decision?** No — §1–7 each carry independent content.

**Is any rule duplicated?** No in-document duplication. The cross-document vocabulary overlap with `ADR-GOV-002` (§3, above) is a consistency issue, not duplication within this document.

**Are any examples accidentally presented as normative rules?** No — checked the Alternatives Considered section specifically, since it names five rejected models; each is stated as a rejected alternative, not smuggled in as an example of acceptable practice.

---

## 5. Boundary Validation

**What does this ADR explicitly not govern?** Stated directly in Open Questions: Investigation-to-Investigation contradiction resolution (explicitly deferred, since `INV11-R7` was not adopted in Sprint 2) and conversion-initiation ownership (deferred to `ADR-GOV-002` §3's own open model). Clear and adequate — and correctly does *not* attempt to resolve either, consistent with the constraint against reopening deferred items.

**Is there any hidden scope expansion?** Checked §2 again from this angle: introducing a four-value status taxonomy is a form of scope expansion relative to what was literally approved, even though it stays within this ADR's own subject matter (it does not reach into another track's territory). Recorded here as the boundary-validation angle on the same finding already raised under Normative Validation.

**Are responsibilities clearly separated from neighboring ADRs?** Yes for `ADR-GOV-001`. For `ADR-GOV-002`, see the vocabulary-overlap finding (Consistency Validation).

---

## 6. Alternative Validation

**Were all major alternatives considered fairly?** Five alternatives with specific, evidenced rejections, matching `INV11-R9` (Adopt) precisely.

**Is there a stronger alternative available?** None identified.

**Are the rejected alternatives adequately justified?** Yes — each ties to a specific piece of empirical evidence (the grep-verified behavior of the ten prior Investigations), not a generic dismissal.

---

## 7. Implementation Validation

**Can this ADR actually be followed in practice?** Mostly yes. The conversion process (§4) is realistic in that it does not invent new machinery — it routes to each track's own existing process. The status model (§2), once its internal tension (Consistency Validation) is resolved, is straightforward to apply as bookkeeping.

**Does it require roles, governance structures, or processes that do not currently exist?** No new role is created. §7's traceability requirement is already, in practice, satisfied by how every existing Investigation is written — no new operational burden.

**Does it create operational ambiguity?** Yes, specifically from the §2 tension already identified: a future contributor trying to record an Investigation's status would not know, from this document alone, whether to record one value or a compound set of values. This is a genuine, practical ambiguity, not merely a theoretical one, since §2 explicitly instructs that status "should be recorded" going forward (Consequences, Migration) without a resolved format for what "recorded" means when more than one status could apply.

---

## 8. Final Decision

**Accept with Changes.**

Required changes before promotion to `Accepted`:
1. Resolve the §2 internal tension: state explicitly whether Investigation status is a single, current value (with a defined transition rule) or a set of independently-tracked, non-exclusive tags — and make the "carries one of the following" opening sentence consistent with whichever reading is intended.
2. Add explicit traceability for §2's specific four-value taxonomy, citing it as a synthesis of `INV11-R1` and `Investigation-011` Phase 10's own completion criteria, rather than presenting it as a direct, verbatim conversion.
3. Add explicit traceability for §7, citing `Investigation-011` Phase 6 and the Register's own "Method note" as its actual source.
4. Coordinate with the `ADR-GOV-002` revision to add the cross-reference clarifying how this document's Investigation-status vocabulary relates to that document's general document-status vocabulary.
5. Correct the `Status` header to `Draft` until the above changes are applied, then re-promote to `Accepted`.

No change to the substance of any Decision point is required — the underlying conclusions (advisory role, no self-conversion, permanent record, traceability) are all well-supported. The findings above are about internal clarity and citation completeness, concentrated specifically in §2, which is this ADR's own most novel piece of structure and therefore warranted the closest scrutiny.
