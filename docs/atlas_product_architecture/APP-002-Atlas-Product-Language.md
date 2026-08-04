# APP-002 — Atlas Product Language

**Status:** Draft, v0.1. This document sits directly beneath APP-000 — Atlas Product Doctrine, as a peer of APP-001 — Atlas Product Concept Taxonomy. It governs the language Atlas uses to communicate with the Investor across every written surface — onboarding, Portfolio, Discover, Daily Brief, Watchlist, Investment Case, notifications, dialogs, confirmations, AI explanations, help text, microcopy, empty states, loading states, error messages, and success messages. It introduces no product philosophy, Product Concept, or Core Domain Object of its own; it operationalizes philosophy and principles APP-000 already states into the words Atlas actually uses. It does not describe visual design, typography, layout, interaction, or implementation.

---

## 1. Purpose

### Why this document exists

Every surface of Atlas speaks. A Verdict item, an error message, a preference explanation, a button label, and an Investment Case's own Atlas Conclusion are all, at the level of language, the same act: Atlas choosing words to communicate with an Investor whose capital and judgment are at stake. Without a single governing language standard, that act drifts — one surface calm and precise, another urgent, a third accidentally promotional — and the Investor experiences not one Atlas but several, each earning or spending trust independently. APP-002 exists to close that gap: to state, once, the voice, tone, and normative language rules every surface of Atlas SHALL follow, so that no future UX specification, component library, or engineering team needs to invent Atlas's own personality a second time.

This document is required because no existing document discharges it. APP-000 states the philosophy and principles language must express (Section 6, Section 7); it does not state the words. `UX-000-Atlas-UX-Doctrine.md` governs how information is perceived, structured, and disclosed (its own Sections 10–19); it states a small number of language-adjacent rules where perception and wording are inseparable — most directly `UXD-R-056` and `UXD-R-057`, which this document adopts unchanged and does not restate as its own independent finding — but it does not state Atlas's voice, tone, or the specific wording patterns this document defines. The individual operational UX specifications (`UX-004` through `UX-016`) and their governing ADRs each write real product copy, but none of them was ever asked to state the underlying language standard that copy should follow; several were authored before this standard existed. APP-002 is that standard, stated for the first time, so that copy already written can be checked against it and copy not yet written can be authored to it directly.

### Scope

APP-002 governs the language — word choice, sentence construction, register, and the presence or absence of specific claims — used in: onboarding; Portfolio; Discover; Daily Brief; Watchlist; Investment Case; notifications; dialogs; confirmations; AI-originated explanations of any kind; help text; microcopy (buttons, links, section titles, tooltips); empty states; loading states; error messages; and success messages. It governs these surfaces regardless of which document specifies their underlying screen, interaction, or Product behavior — APP-002 states what Atlas is permitted and required to say, once a UX specification has already determined what is being said and why.

### Authority

APP-002 is subordinate to `ATLAS_CONSTITUTION.md` and `Architecture-Governance.md`, and directly to APP-000 — Atlas Product Doctrine, from which every principle this document operationalizes derives. It SHALL NOT contradict APP-000, and SHALL NOT redefine a term APP-000 or APP-001 already defines.

APP-002 is a peer of APP-001 — Atlas Product Concept Taxonomy, not subordinate to it; each governs its own territory (APP-001 governs which Product Concepts exist, APP-002 governs the language used to speak about them) without either deriving authority from the other. APP-002 SHALL remain factually consistent with APP-001's own accepted concept names, with the accepted normative behavior of every `APS` specification (`APS-001` through `APS-009`), and with `UX-000-Atlas-UX-Doctrine.md` and its subordinate UX specifications — but it is not subordinate to any of them, and none of them may override a rule this document states. Where a task description or future document states that APP-002 is "subordinate to APS specifications" or "subordinate to UX specifications," that framing SHALL be read as an error and disregarded: Product Architecture (the `APP-` and `APS-` series) governs above UX Architecture in the accepted Atlas authority chain, per `Architecture-Governance.md` and APP-000 §9's own explicit statement that a UX specification "SHALL NOT independently establish product philosophy, principle, or responsibility." A document that governs the words used to express Product Concepts and Product Principles is, by that same logic, a Product Architecture document positioned above UX Architecture, not beneath it. This correction is stated here once, explicitly, rather than left to be silently discovered later.

### Non-goals

APP-002 does not govern, and future amendment SHALL NOT extend it to govern: visual design, typography, color, spacing, or motion (governed by `UX-012` and its own subordinate design-system documents); layout, screen architecture, or navigation (governed by each operational UX specification); interaction mechanics (governed by `UX-000` Section 18 and each operational UX specification); or implementation, algorithms, data schemas, or persistence (out of scope for the entire Product and UX Architecture, per APP-000 §1 and §10). APP-002 does not define, and SHALL NOT be read to define, any new Product Concept, Core Domain Object, or confidence scale; where this document discusses conviction or uncertainty in language terms, that discussion states word choices only and does not discharge `UX-000` `UXD-R-064`'s own still-open question of a future numeric or categorical confidence representation.

---

## 2. Communication Philosophy

Atlas communicates the way a trusted long-term investment partner does: someone who has done the reading, states plainly what they found, distinguishes what they know from what they are inferring, and never needs to raise their voice to be taken seriously. This is a specific communication register, and Atlas SHALL NOT drift toward any of the registers it more naturally resembles at a technical level:

Atlas does not communicate like **a broker**. A broker's language is transactional — it exists to move the Investor toward an action, priced and timed for the broker's own benefit. Atlas has no transaction to move the Investor toward; per APP-000 §4, it is not a trading or execution system, and its language SHALL never imply otherwise.

Atlas does not communicate like **a news service**. A news service's language is calibrated for attention and immediacy — every item competes to be read now. Atlas's language is calibrated for relevance to what the Investor already owns, follows, or has reasoned about (the discipline every APS specification in the `APS-006`–`APS-009` expansion already states at the Product layer); it does not compete for attention it has not earned.

Atlas does not communicate like **a trading platform**. A trading platform's language creates the sensation of a live, moving market demanding constant response. Atlas's language is deliberately calm regardless of how volatile the underlying market is — per `ATLAS_CONSTITUTION.md`'s own Product Philosophy, Atlas "should avoid unnecessary drama" and "should not use urgency as a product mechanic."

Atlas does not communicate like **a marketing product**. Marketing language persuades; it selects facts and framing to move a reader toward a predetermined conclusion. Atlas's language informs; it states facts and their support so the Investor can reach their own conclusion. Where the two would produce different sentences for the same fact, Atlas SHALL use the informing sentence.

Atlas values clarity over persuasion in every instance where the two could be understood to conflict. A sentence that is maximally persuasive and a sentence that is maximally clear are not always in tension, but where they are, clarity wins without exception. This is not a stylistic preference; it is a direct expression of APP-000 §6.9 ("Trust cannot be asserted; it is earned by making the basis of every claim... inspectable") and of PP-008 (Provenance Is Always Attributable). Persuasive language, by its nature, is language optimized to be believed rather than language optimized to be checked — and a product whose entire purpose is to strengthen Investor Judgment (APP-000 §3) cannot use language that discourages the Investor from checking it.

---

## 3. Voice

Voice is Atlas's constant personality — it does not change from screen to screen, surface to surface, or investor to investor. Tone (Section 4) adapts to circumstance; voice does not. Every sentence Atlas writes, regardless of surface, SHALL be recognizable as coming from the same speaker.

Atlas's voice is:

**Calm.** Atlas does not raise its register for volatile markets, large price moves, or high-stakes decisions. A falling price or a broken assumption is stated with the same evenness as a stable one, per `UX-004` §10's own established design test ("Atlas should communicate seriousness without creating panic").

**Professional.** Atlas writes the way a competent advisor writes in a client memo, not the way a chat app writes to a friend. It does not use slang, does not attempt humor at the expense of clarity, and does not perform casualness to seem approachable.

**Thoughtful.** Atlas's sentences show evidence of having considered what they say before saying it. A thoughtful sentence is not necessarily a long one — brevity and thoughtfulness are compatible, and Section 5 requires both.

**Transparent.** Atlas states its own basis for a claim in the same breath as the claim, or makes that basis one interaction away, per PP-008 and `UXD-R-054`. Atlas never asks to be trusted without being checkable.

**Respectful.** Atlas addresses the Investor as the owner of every decision, per PP-005, never as a subject to be managed, nudged, or protected from their own judgment.

**Patient.** Atlas does not rush the Investor toward reading, deciding, or acting. Silence — a session with nothing requiring attention — is treated as a legitimate, complete outcome (`DBINV-011`, `UX-004` §26), never papered over with manufactured content.

**Objective.** Atlas describes what is, and what evidence supports, before it describes what it believes should follow. It separates observation from interpretation explicitly, per Section 5.

**Evidence-driven.** Every substantive claim Atlas makes traces to Evidence, Reasoning, or an already-accepted Product computation (the Atlas Priority Model). Atlas does not write sentences whose only support is that they sound right.

Atlas's voice is never:

**Emotional.** Atlas does not express enthusiasm, disappointment, alarm, or excitement about a portfolio, a position, or a market development. It reports; it does not react.

**Sensational.** Atlas does not select the most dramatic true framing of a fact when a calmer, equally true framing exists. Given a choice between "a core assumption has weakened" and "your biggest holding is in trouble," Atlas uses the former — not because the latter is false, but because it is calibrated for attention rather than accuracy.

**Promotional.** Atlas does not describe its own outputs, capabilities, or recommendations using superlative or self-congratulatory language. It does not tell the Investor how good its analysis is; it shows the analysis and lets the Investor judge it.

**Absolute without evidence.** Atlas does not use words like "always," "never," "guaranteed," "certain," or "best" to describe an investment outcome, a company, or a market condition, because doing so asserts a certainty the underlying Evidence and Reasoning virtually never support, per PP-007 and `ATLAS_CONSTITUTION.md`'s own Non-Negotiable Principle that "Atlas never exaggerates certainty." (These same words remain available, used precisely, to describe Atlas's own governed behavior — for example, "Atlas never places a trade" — where the claim is about a designed system boundary Atlas can actually guarantee, not about the market or an investment's future.)

---

## 4. Tone

Tone is how voice is inflected for a specific circumstance. Voice answers "who is speaking"; tone answers "what is the speaker responding to right now." Every tone below expresses the same unchanging voice from Section 3 — none of them licenses a departure from calm, professional, evidence-driven language; they differ only in emphasis and pacing.

**Normal guidance.** The default register: even, unhurried, structured from conclusion to detail (per `UXP-001`, Meaning Before Volume). No emphasis is added beyond what the content itself warrants.

**Uncertainty.** Tone slows and becomes more explicit about what is and is not known (Section 7). Sentences favor qualified constructions ("suggests," "appears to," "based on the evidence available") over declarative ones, without becoming evasive — qualification states a real epistemic condition, not a hedge to avoid accountability.

**High conviction.** Tone remains calm but becomes more direct and specific, because the underlying evidence supports directness. High conviction is expressed through the specificity and traceability of the supporting reasoning, never through intensifying language, exclamation, or repetition.

**Low confidence.** Tone becomes more explicit about limits and more generous with what remains unknown. A low-confidence statement is not written more tentatively out of politeness; it is written more precisely about its own weakness, per PP-007.

**Errors.** Tone is factual, brief, and forward-looking (Section 8) — what happened, what Atlas knows, what the Investor can do. No apology beyond a single, genuine acknowledgment; no self-deprecating or falsely casual language that could read as minimizing a real problem.

**Success.** Tone is quiet and specific (Section 9) — Atlas states what was actually accomplished, not that something generically "succeeded."

**First-time onboarding.** Tone is welcoming without being effusive, and explicit about control — every point at which the Investor is asked for information restates, plainly, that the information is optional and why Atlas is asking (Section 10). Onboarding tone never implies momentum the Investor has not chosen ("almost done!," "just one more step") — Atlas does not manufacture a sense of progress toward a goal Atlas itself defined.

**Long-term monitoring.** Tone treats repetition of "nothing has changed" as ordinary and correct, per `DBINV-011`, never as a state requiring apology, filler content, or an artificially generated update to justify the Investor's attention.

**Portfolio review.** Tone is structural and comparative — describing what a fact means for the portfolio as a system (per `UX-007A`/`UX-007P`'s own established Portfolio Workspace register), not for any one position read in isolation.

Tone changes with circumstance. Voice does not. A sentence written in the "errors" tone and a sentence written in the "success" tone SHALL still be recognizable as the same speaker if read side by side.

---

## 5. Core Communication Principles

The following normative rules govern every instance of Atlas language, across every surface named in Section 1's Scope. Each rule traces, by citation, to the Product Principle, Constitution statement, or Doctrine rule it operationalizes. A subordinate UX specification, component library, or piece of product copy that violates one of these rules is non-compliant with APP-002, regardless of how well it otherwise reads.

**APL-R-001.** Atlas SHALL explain why. A claim, a Verdict item, a flagged risk, or a surfaced opportunity SHALL be accompanied by its own reason, or a reachable path to that reason, never presented as an assertion alone. *(PP-008; `UX-014` §7 item 6; `UX-015` §8 Evidence presentation; `UX-016` §7.)*

**APL-R-002.** Atlas SHALL distinguish facts from interpretation. A statement about what is observed (a price, a filing, a reported number) SHALL be phrased differently, and SHALL NOT be blended into the same sentence as, a statement about what Atlas infers from it. *(APP-000 §5 Evidence, §5 Reasoning; `UXD-R-066`–`070`.)*

**APL-R-003.** Atlas SHALL communicate uncertainty honestly, at every point where uncertainty exists, rather than resolving it by omission or by choosing the more confident-sounding phrasing. *(PP-007; `ATLAS_CONSTITUTION.md` Trust Principles: "Be explicit about missing information," "Be clear when evidence is weak.")*

**APL-R-004.** Atlas SHALL avoid urgency. No sentence SHALL imply that a decision must be made immediately, that a window is closing, or that inaction carries a penalty Atlas has not actually established. *(`ATLAS_CONSTITUTION.md` Non-Negotiable Principle, "Atlas never encourages unnecessary trading"; Product Philosophy, "should not use urgency as a product mechanic.")*

**APL-R-005.** Atlas SHALL respect Investor ownership. Language SHALL attribute every decision, every acceptance of Atlas-originated content, and every action to the Investor as its owner, and SHALL NOT phrase Atlas's own output as though it were the Investor's completed judgment. *(PP-003; PP-005; `UXD-R-048`–`053`.)*

**APL-R-006.** Atlas SHALL acknowledge limits. Where Atlas does not have enough information to support a claim, language SHALL say so directly, rather than presenting a thinner claim as though it were a complete one. *(`ATLAS_CONSTITUTION.md` Trust Principles, "Admit when there is not enough information for a high-confidence assessment.")*

**APL-R-007.** Atlas SHALL communicate confidence proportionally. The strength of the language used for a claim SHALL match the strength of the evidence supporting it; language SHALL NOT overstate or understate what the underlying Evidence and Reasoning actually support. *(PP-007; `UXD-R-062`–`063`.)*

**APL-R-008.** Atlas SHALL avoid unnecessary words. A sentence that communicates its meaning in fewer words SHALL be preferred to a longer sentence that communicates the same meaning, provided no clarity or required qualification is lost. *(APP-000 §6.8, Simplicity as Discipline.)*

**APL-R-009.** Atlas SHALL prefer simple language. Common words SHALL be preferred to technical, financial-jargon, or internal-architecture terms wherever a common word conveys the same meaning to the Investor. *(APP-000 §6.8; Section 10 of this document.)*

**APL-R-010.** Atlas SHALL never pressure decisions. No language pattern SHALL be designed, whether through repetition, framing, or emphasis, to increase the likelihood that an Investor acts, as distinct from increasing the Investor's understanding of whether acting is warranted. *(PP-001; PP-003; `ATLAS_CONSTITUTION.md` Product Philosophy.)*

**APL-R-011.** Atlas SHALL attribute its own content. Every piece of Atlas-originated language SHALL be presented in a form that is recognizably Atlas's own statement, not phrased so that it could be mistaken for the Investor's own words or an external, independent source. *(PP-008; `UXD-R-054`–`055`.)*

**APL-R-012.** Atlas SHALL NOT use first-person belief framing. Atlas-originated language SHALL NOT use constructions equivalent to "I believe," "I think," or "I have decided"; it SHALL use clearly attributed third-person framing such as "Atlas's current analysis indicates" or "the evidence available suggests." *(`UXD-R-056`–`057`, adopted here unchanged.)*

**APL-R-013.** Atlas SHALL preserve the distinction between Atlas Recommendation, Proposed Decision Candidate Content, Proposed Decision, and Decision in its own language, and SHALL NOT use language that implies one has already become another. *(`ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, adopted here unchanged; Section 6 of this document.)*

**APL-R-014.** Atlas SHALL NOT characterize Decision Quality by reference to Outcome, whether favorable or unfavorable, in any surface's language. *(PP-009; `UXD-R-077`–`082`.)*

**APL-R-015.** Atlas SHALL state a genuine absence of change, findings, or required action plainly and as a complete, successful result, never disguised as content or apologized for. *(`DBINV-011`; `DS-F-002`; Section 9 of this document.)*

**APL-R-016.** Atlas SHALL NOT use language, structure, or repetition whose primary effect is to increase engagement (return visits, time spent, or interaction volume) independent of the Investor's own informational need. *(APP-000 §4; `ATLAS_CONSTITUTION.md` Vision, "Atlas should not become a trading signal machine.")*

Every future UX specification and every piece of product copy SHALL be checked against these sixteen rules before publication, per Section 13.

---

## 6. Recommendation Language

**Scope note.** This section governs the *register* Atlas uses whenever it expresses a directional view or a degree of conviction, in any surface — an Investment Case's own Atlas Conclusion, a Daily Brief Verdict item, a Discover Candidate's Thread rationale, the Atlas Recommendation component, or Proposed Decision Candidate Content alike. It does not redefine, rename, or add to the concepts `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` already settled: "Atlas Recommendation" and "Proposed Decision Candidate Content" remain the only two canonical uses of recommendation-adjacent terminology as *component or field names* (`ADR-003` R-01, R-02), and this section's guidance applies to the sentences those and every other conviction-bearing surface use, without altering which component or field a sentence belongs to.

Atlas never issues instructions. It states what the evidence currently supports and leaves the decision, explicitly, with the Investor, per PP-003 and `APL-R-005`.

| Instead of (command) | Atlas uses (evidence-attributed) |
|---|---|
| "Buy this stock." | "Current evidence suggests this position may be worth initiating." |
| "Great investment." | "Current evidence indicates a favorable balance of business quality and valuation." |
| "Sell immediately." | "This position deserves review — a core assumption behind it has weakened." |
| "Hold." | "No change to the current position is currently supported by the evidence." |

**By conviction level.**

*High conviction* — evidence is extensive, consistent, and directly supports the claim. Language is direct and specific, but still attributed and still framed as a matter for the Investor's own judgment: "The evidence available strongly supports [specific claim], based on [specific, named basis]." Directness comes from specificity, never from intensifying words ("definitely," "clearly," "obviously").

*Medium conviction* — evidence meaningfully supports the claim but leaves real, stated open questions. Language names both what supports the claim and what remains open: "Current evidence suggests [claim], though [specific named uncertainty] has not yet been resolved."

*Low conviction* — evidence is thin, mixed, or largely inferential. Language states this directly rather than softening the claim while keeping its confident shape: "The available evidence is limited. What exists points toward [tentative claim], but this should be treated as a starting point for further review, not a settled view."

*Insufficient evidence* — Atlas SHALL NOT manufacture a claim to avoid appearing unhelpful (`APL-R-006`; `DS-R-064`; `DS-F-009`; `DB-R-047`). Language states the absence directly: "There isn't currently enough evidence for Atlas to form a view here." This is a complete, valid statement, never treated as a gap requiring a weaker claim to fill it.

---

## 7. Uncertainty

Uncertainty is informative, not a weakness of Atlas's own analysis. Per PP-007 and APP-000 §6.3, uncertainty is "a permanent, structural condition of investing," and concealing it — not disclosing it — is the actual failure. Atlas's language SHALL treat a well-disclosed uncertainty as evidence of a more trustworthy analysis than a confident claim with no disclosed uncertainty at all.

This section states word-level distinctions for describing the epistemic status of a claim in prose. It is a language convention, not a numeric or categorical confidence scale; it does not discharge, and SHALL NOT be read as resolving, `UX-000` `UXD-R-064`'s own still-open question of a future confidence representation.

**Known.** A fact Atlas has directly observed — a reported number, a recorded filing, a price. Stated as a plain fact, with its source reachable: "Revenue grew 12% in the most recent quarter, per the company's own filing."

**Estimated.** A figure or conclusion Atlas has derived through a stated method from Known facts. Stated with the method or basis named, never presented with the same plainness as a Known fact: "Based on current multiples, fair value is estimated in the range of [X]–[Y]." The word "estimated," or an equivalent explicit marker, SHALL appear in the sentence itself, not only in a nearby label.

**Possible.** A claim that is plausible given available evidence but not established by it — a scenario, a risk, an opportunity that has not yet materialized. Stated with an explicit possibility marker and, where available, what would need to be true for it to become more or less likely: "It's possible that [development] could affect this position if [specific condition] occurs."

**Unknown.** A fact that would materially matter but that Atlas has no basis to assert in any direction. Stated as a direct, named gap, never silently omitted: "Atlas does not currently have enough information to assess [specific question]." Per `APL-R-006`, an Unknown SHALL be stated, not left implicit through the absence of a claim.

Where a single statement blends more than one of these categories, the sentence structure SHALL make the transition explicit ("The reported figure is [Known]; based on that, Atlas estimates [Estimated]") rather than allowing the reader to infer where a Known fact ends and an Estimated or Possible conclusion begins.

---

## 8. Error Communication

An error is never the Investor's fault, and Atlas's language SHALL NOT imply otherwise, even where the triggering action was the Investor's own (for example, an invalid entry). Atlas's language also SHALL NOT expose technical implementation detail the Investor has no use for (stack traces, internal service names, error codes with no stated meaning).

Every error message SHALL state four things, in this order:

1. **What happened** — a plain description of the failure, scoped to what actually failed: a failure in one item or tier SHALL NOT be described as though the entire surface failed, where it did not.
2. **What Atlas knows** — any relevant fact Atlas can state with confidence about the failure's own scope or cause, stated only where genuinely known.
3. **What Atlas doesn't know** — stated directly where relevant, per `APL-R-006`, rather than omitted.
4. **What the Investor can do next** — a concrete, available next step (retry, wait, choose an alternative method), never a dead end.

*Example:* "Atlas couldn't read three of your holdings from this file. The rest of your portfolio imported successfully. This usually happens when a row is formatted differently from the others — you can review those three rows and try again, or enter them manually."

This states what happened (three holdings failed), what is known (the rest succeeded; a likely cause), implicitly what is not asserted (no claim about which specific formatting issue, since that is not always knowable), and two concrete next steps.

---

## 9. Success Communication

Success is stated as a specific, meaningful outcome, never as a generic status word. "Success," "Done," and "Completed" SHALL NOT appear alone as a success message; each SHALL be replaced with a statement of what was actually accomplished.

| Generic (not used) | Meaningful (used) |
|---|---|
| "Success." | "Portfolio updated." |
| "Done." | "Investment Case prepared." |
| "Completed." | "Analysis complete — your first impression is ready." |
| "Saved." | "Preferences saved. You can update them at any time." |

Where the meaningful outcome is itself the absence of change or action — nothing new to report, no positions require review — that outcome is stated with the same directness and the same status as any other success, per `APL-R-015` and `DBINV-011`, never apologized for or padded with unrelated content to avoid appearing empty: "Nothing has changed since your last visit." is a complete, correct success message.

---

## 10. Microcopy

Microcopy is Atlas's language at its smallest scale, and the scale at which register drift is most likely, because each individual piece looks too small to matter. Every rule in Section 5 applies at this scale exactly as it applies to a full paragraph.

**Buttons.** A button's label states the action it performs, in the Investor's own terms, in a verb phrase ("Continue to Portfolio," "Save preferences"), never a vague directive ("OK," "Submit," "Next") where a more specific label is available.

**Links.** A link's text states its destination or the specific content it reveals ("View evidence," "View related holdings"), never a generic "Click here" or "Learn more" with no stated subject.

**Section titles.** A title states what the section contains in the Investor's own vocabulary (Verdict, What Changed, My First Impression), never an internal or architectural name.

**Tooltips.** A tooltip adds the one fact the visible label could not fit, and nothing else; it does not restate the label.

**Notifications.** A notification states the same four-part discipline as Section 8 or Section 9's own success discipline, compressed to its essential fact — never a bare status word, never an artificial urgency cue.

**Confirmation dialogs.** A confirmation states, in plain terms, what will happen if the Investor proceeds, and offers a clearly labeled way to decide either way. It never uses fear-based framing ("Are you sure? This cannot be undone!") where a calmer, equally accurate statement is available, and it reserves irreversible-action language for acts that are actually irreversible (`UX-014` §11's own discipline against borrowing heavier language for lighter acts is the governing precedent).

**Loading messages.** A loading message, where one is shown at all, states what Atlas is currently doing in concrete terms ("Atlas is evaluating portfolio dependencies…," per `UX-007A` §28), never a generic "Loading…" alone where a more specific statement is available.

**Empty states.** An empty state states the absence plainly and states the one next step available, per Section 9; it never implies something is broken.

**Settings.** A setting's label states what it controls in the Investor's own terms; where a setting has a consequence the Investor should know before changing it, that consequence is stated in the same view, not hidden behind a separate help action.

**Forms.** A form field's label states what is being asked for in plain language; a required field is marked as required only where it genuinely is (per `UX-016` §22, no field SHALL be marked required that is not).

**Preference descriptions.** Every preference explanation SHALL answer one question directly: *why is Atlas asking?* A preference description that states only what the field is, without stating why sharing it helps, is incomplete. *Example:* "Monthly investment budget — helps Atlas suggest realistic position sizing and accumulation plans." names the field and states, in one sentence, the benefit of sharing it — the same discipline already demonstrated in Atlas's own onboarding personalization screen.

---

## 11. Language Atlas Never Uses

The following patterns SHALL NOT appear anywhere in Atlas's language, on any surface, regardless of context, urgency of the underlying situation, or apparent factual accuracy of the statement. Where a real, evidence-supported fact would naturally be phrased using one of these patterns, the fact SHALL be restated in language that satisfies Section 5 instead of being omitted.

**APL-F-001 — Manufactured urgency.** "Act now," "Don't miss out," "Limited time," "Before it's too late," or any construction implying a closing window Atlas has not actually established as fact.

**APL-F-002 — False or unsupportable certainty.** "Guaranteed," "Can't lose," "Risk-free," or any claim asserting a certainty no investment can honestly carry.

**APL-F-003 — Superlative, unsupported evaluation.** "Best investment," "Perfect opportunity," "Huge upside," or any superlative framing not directly tied to, and immediately followed by, the specific evidence supporting it.

**APL-F-004 — Trading-floor cliché.** "Strong buy," "Hot stock," "Can't-miss," or any phrase borrowed from broker or trading-platform registers that Section 2 already excludes.

**APL-F-005 — Fear-based framing.** Language designed to provoke alarm, loss aversion, or anxiety beyond what the underlying fact itself warrants — including exclamation-driven warnings, repeated emphasis on downside without matching context, or framing a routine review as an emergency.

**APL-F-006 — Marketing and sales language.** Language whose primary function is to persuade toward an action or a favorable impression of Atlas itself, rather than to inform — including self-congratulatory framing of Atlas's own analysis ("our powerful AI," "cutting-edge insights").

**APL-F-007 — Clickbait.** Headlines, notification text, or section titles that withhold their own content to induce a click or open, rather than stating what they contain.

**APL-F-008 — First-person belief framing.** "I believe," "I think," "I have decided," or any construction that frames Atlas as an independent believer or decision-maker, per `APL-R-012` and `UXD-R-056`.

**APL-F-009 — Outcome-as-verdict framing.** Language that treats a favorable or unfavorable Outcome as proof of good or bad Reasoning, per `APL-R-014` and `UXD-R-077`–`082`.

**APL-F-010 — Manufactured completeness.** A generic success or loading word used alone where a specific, meaningful statement is available, per Section 9.

A pattern's absence from this list is not permission to use it; Section 5's own rules govern every pattern not explicitly named here, and any construction that violates the spirit of `APL-R-001` through `APL-R-016` SHALL be treated as non-compliant even where no specific forbidden phrase in this section literally appears.

---

## 12. Examples

Each pair below states the same underlying fact. The left column fails one or more rules in Section 5 or names a pattern forbidden in Section 11; the right column is compliant.

**Investment Case**

Bad: "This is a fantastic buying opportunity — don't wait!"
Good: "The recent decline has improved the expected return while the investment thesis remains intact. Current evidence supports reviewing whether to initiate a position." *(`APL-F-001`, `APL-F-003` avoided; `APL-R-005`, `APL-R-007` applied.)*

Bad: "Your thesis is broken."
Good: "A core assumption behind this position has broken. This deserves review." *(States the specific condition rather than an unqualified verdict; preserves Investor ownership of what follows.)*

**Daily Brief**

Bad: "3 urgent alerts require your attention right now!"
Good: "Three items connected to your portfolio have changed since your last visit." *(`APL-F-001` avoided; states the Verdict's own scope factually.)*

Bad: "Nothing to report."
Good: "Nothing has changed since your last visit." *(`APL-R-015`; a complete, specific statement rather than a dismissive one.)*

**Discover**

Bad: "Hot stock alert — everyone's talking about this one."
Good: "This connects to a theme already reflected in three of your holdings." *(`APL-F-004` avoided; states the actual Thread, per `DS-R-030`.)*

Bad: "AI-powered pick you can't miss."
Good: "Current evidence suggests this may be worth investigating further." *(`APL-F-004`, `APL-F-006` avoided; conviction stated proportionally, per Section 6.)*

**Portfolio**

Bad: "Your portfolio is doing great!"
Good: "The portfolio remains structurally sound across seven of eight positions." *(`UX-007A` §37's own established precedent; specific and calibrated, not celebratory.)*

Bad: "Warning: high risk detected."
Good: "Enterprise AI exposure is high and increasingly shared across five holdings." *(States the specific dependency rather than an unexplained severity label.)*

**Onboarding**

Bad: "Unlock your full potential — tell us everything!"
Good: "All preferences are optional. Share only what you're comfortable providing." *(`APL-F-006` avoided; matches Atlas's own established personalization language.)*

Bad: "Almost there! Just 3 more steps!"
Good: "Just two things to start — everything else can wait until you're ready." *(No manufactured momentum, per Section 4's onboarding-tone rule; still concrete about what remains.)*

**Notifications**

Bad: "You need to check this immediately!"
Good: "A position you follow has reached your entry range." *(`APL-F-001` avoided; states the fact, leaves timing to the Investor.)*

**Errors**

Bad: "Error 500: Internal server error."
Good: "Atlas couldn't complete this analysis right now. Your existing data is unaffected — you can try again in a moment." *(No exposed implementation detail; states what happened, what remains true, and a next step, per Section 8.)*

**Warnings**

Bad: "Danger! This portfolio is dangerously concentrated!"
Good: "Nearly half of the portfolio's growth now depends on a single theme." *(States the specific condition without alarm-based framing, per `APL-F-005`.)*

**Confirmations**

Bad: "Are you sure?? This action is PERMANENT and cannot be undone!!"
Good: "Removing this entry won't affect any Investment Case, Reasoning, or Decision already recorded." *(`UX-014` §11's own precedent; states the actual, proportionate consequence rather than borrowing heavier language.)*

**Preference collection**

Bad: "Risk tolerance (required)"
Good: "Risk tolerance — helps Atlas calibrate how much volatility and concentration it flags for your review." *(States the field is optional elsewhere on the same screen; states why Atlas is asking, per Section 10.)*

**Broker sync**

Bad: "Connect now to unlock personalized insights!"
Good: "Atlas connects securely and reads your holdings automatically." *(`APL-F-006` avoided; states what happens next, plainly, per Atlas's own established import-method language.)*

---

## 13. Governance

Every future Product Architecture, UX Architecture, or component-level document that contains Atlas-originated language — including every future `APS` specification's own illustrative examples, every future operational UX specification, and every component in `UX-012` and its subordinate documents — SHALL be written in compliance with this document. A new UX specification's own governance metadata (per `Architecture-Governance.md` §10) SHALL cite APP-002 as a governing authority alongside `UX-000` wherever the specification contains product copy, in the same way `UX-014`, `UX-015`, and `UX-016` already cite `UX-000` and their own governing `APS` specification.

APP-002 does not retroactively correct language already committed in `UX-004` through `UX-016` or any other existing document; those documents remain accurate as far as their own governing authority extends, and a future, separately-authorized language-correction task — following the same disclosed, non-erasing Correction Notice discipline this repository already uses throughout `docs/atlas_ux/` — is required before any existing document's own language is amended to match APP-002 more closely than it already does. This document's own Examples (Section 12) draw on language already established in `UX-004`, `UX-007A`, `UX-007P`, `UX-014`, `UX-015`, and `UX-016` precisely because that language was found, on review, to already be compliant — APP-002 formalizes a standard substantially already in practice, rather than inventing one from nothing.

Where a future amendment to `APP-000`, `APP-001`, or any `APS` specification changes a Product Concept's own name or normative behavior, APP-002's own examples referencing that concept SHALL be reviewed for continued accuracy as part of that amendment's own required review, per `APP-000` §11.2's own discipline for reviewing dependent documents after a governing change.

Amendment of this document itself follows `Architecture-Governance.md`'s own general amendment discipline: a proposed amendment SHALL state what changed and why, SHALL NOT silently redefine a rule already stated, and SHALL preserve superseded text in the document's own revision history rather than erasing it.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, APP-000, APP-001, any `APS` document, `UX-000`, or any existing UX specification. It introduces no new Core Domain Object and no new Product Concept. It governs product language only.*
