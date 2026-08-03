# APP-000 — Atlas Product Doctrine

**Status:** Draft, v0.4. This is the highest governing document within the Atlas Product Architecture. It establishes the philosophy, principles, responsibilities, and governance discipline from which every subordinate product document derives. It does not itself describe any workflow, screen, workspace, interaction, algorithm, or visual design.

---

## 1. Purpose and Scope

This Doctrine states why Atlas exists, what Atlas fundamentally is, the enduring principles that govern the product, the responsibilities Atlas and the Investor each carry, and the discipline by which every future product document is written and evaluated.

This Doctrine governs:

- product philosophy;
- product principles;
- the responsibilities of Atlas and of the Investor;
- product governance, including the authority, interpretation, amendment, and traceability of product documents.

This Doctrine SHALL NOT describe:

- workflows;
- screens, pages, or workspaces;
- interaction design or navigation;
- visual design;
- implementation, architecture, or data models;
- specific AI models, algorithms, or techniques;
- product roadmap or release sequencing.

Those subjects belong to subordinate specifications, including Atlas Product Specifications (APS), UX Specifications, Visual Design Artifacts, and product implementations. Where a future author is uncertain whether a statement belongs in this Doctrine, the test is this: a complete change to Atlas's interface, technology, or implementation would require changing the statement if it belongs elsewhere. A statement belongs in this Doctrine only if it would remain true regardless of how Atlas is built.

This Doctrine does not govern Atlas Core's architecture, ontology, or engineering process. Those are governed by the Atlas Core doctrine documents, which this Doctrine treats as a separate, independent authority. Where a concept defined by Atlas Core (for example, at the level of domain ontology) and a concept defined by this Doctrine appear to overlap, this Doctrine governs product philosophy and responsibility; Atlas Core governs domain ontology and architecture. A conflict between the two SHALL be treated as a defect requiring reconciliation, not as license to treat one authority as displacing the other.

## 2. Document Authority

APP-000 is the highest governing document within the Atlas Product Architecture.

Every subordinate product document — including but not limited to APS Product Specifications, UX Specifications, Visual Design Artifacts, and product implementations — SHALL derive its behavior, its priorities, and its constraints from this Doctrine.

This Doctrine SHALL NOT derive behavior, priority, or constraint from any subordinate document. Where a subordinate document appears to establish a product commitment that this Doctrine does not support, that commitment has no standing until this Doctrine is amended to support it, per Section 11.

A subordinate document MAY elaborate, specialize, or operationalize a principle stated in this Doctrine. A subordinate document SHALL NOT contradict a principle stated in this Doctrine, redefine a term this Doctrine defines, or adopt a responsibility for Atlas or the Investor that this Doctrine does not authorize.

Where a subordinate document conflicts with this Doctrine, this Doctrine prevails, regardless of the subordinate document's recency, level of detail, or degree of implementation.

## 3. Why Atlas Exists

Investing is a repeated act of committing capital under conditions that cannot be resolved before the commitment is made. The relevant future is not knowable in advance. The evidence available at the time of a decision is always partial. The person making the decision has finite time, finite attention, and a documented tendency to judge decisions by their outcomes rather than by the reasoning that produced them.

These conditions do not go away with better information, faster access, or more sophisticated tools. They are structural to investing itself. A product that treats them as solvable — that promises certainty, automation of Investor Judgment, or outcomes independent of the investor's own reasoning — misrepresents what investing is.

Atlas exists because these structural conditions are better addressed by strengthening the investor's own reasoning than by replacing it. An investor who commits capital without articulating why is not protected by having been right; a favorable outcome reached through unexamined reasoning is not evidence of decision quality, and an unfavorable outcome reached through sound reasoning is not evidence of its absence. Without a durable, inspectable record of reasoning, an investor cannot reliably distinguish a good decision from a lucky one, or a bad decision from an unlucky one. Without that distinction, there is no way to learn.

Atlas exists to make that distinction possible, and to make it durable over time. It exists to help the investor allocate attention to what matters, to make the reasoning behind a decision explicit and examinable, to make uncertainty visible rather than hidden, and to preserve the connection between reasoning and outcome across an investing lifetime — so that Investor Judgment, not chance, is what improves.

## 4. What Atlas Fundamentally Is

Atlas is an instrument for improving the quality of an investor's own decisions. It is not a replacement for Investor Judgment, and its value SHALL NOT be measured by the accuracy of any prediction it produces.

Atlas fundamentally is:

- a means by which an investor's attention is directed toward what is relevant to a decision, and away from what is not;
- a means by which evidence relevant to a decision is gathered, organized, and made available for examination;
- a means by which the reasoning behind a decision is articulated, recorded, and preserved;
- a means by which uncertainty is made visible rather than concealed or resolved by assertion;
- a means by which an investor's past decisions and the reasoning behind them can be revisited, so that Investor Judgment improves over time.

Atlas fundamentally is not:

- an autonomous decision-maker; Atlas SHALL NOT commit an investor's capital, and no product behavior SHALL be designed to make it appear that Atlas has done so;
- a source of certainty; Atlas SHALL NOT present a conclusion as certain where the underlying evidence or reasoning does not support certainty;
- a performance-prediction system whose value is measured by forecast accuracy;
- a trading or execution system; the presence of a course of action in Atlas SHALL NOT be conflated with the capacity, or the intent, to execute it;
- a passive record-keeping system; Atlas's value lies in actively supporting reasoning and attention, not only in storing what has already been decided.

## 5. Definitions

The terms defined in this section carry the meaning stated here throughout every document that derives from this Doctrine. A subordinate document MAY introduce additional terms of its own, but SHALL NOT redefine a term defined in this section. Only concepts expected to remain stable regardless of how Atlas is designed, built, or presented are defined here. Concepts specific to a particular product surface, interaction model, or implementation — including, without limitation, the concepts of a session, a workspace, a home, a portfolio, or an investment case — are defined, if at all, by subordinate specifications, not by this Doctrine.

Several terms defined below — most notably Decision, Investor Judgment, and Reasoning — are also used, with an independently governed meaning, by the Atlas Core doctrine and its Domain Object Model. This section defines each term solely in its product-language sense: how the concept is experienced and owned by the Investor. It does not define, redefine, constrain, or assert any correspondence with an Atlas Core Domain Object, ontological primitive, or architectural term of the same or a similar name. Atlas Core's own doctrine governs that ontology exclusively, per Section 1. Investor Judgment carries an additional, explicit qualification — in its own name and in its own definition below — because its collision with Atlas Core's Judgment Domain Object is direct and categorical (an act, as this Doctrine defines it, versus a settled object, as Atlas Core defines it); Decision and Reasoning rely on this general boundary alone. This boundary applies equally to any term Atlas Core later adopts, including a term — such as Evidence — not yet settled by Atlas Core at the time of this Doctrine's authorship; no amendment to this Doctrine is required for the boundary to hold.

**Investor.** The person who holds ownership of, and accountability for, a body of capital allocation decisions. This includes both a person deciding for their own capital and a person authorized to make capital allocation decisions under an investment mandate on behalf of another party. In either case, the Investor is the sole human party whose Investor Judgment is exercised and whose accountability is at stake in a Decision; an investment mandate does not transfer ownership of Investor Judgment to the party granting the mandate, to an organization, or to Atlas. Every reference in this Doctrine to a person using Atlas refers to the Investor.

**Decision.** A commitment, made by the Investor, to a course of action regarding capital, which could have been made differently. A Decision is distinct from a plan not yet committed to, and distinct from the outcome that later follows it. A Decision exists at the moment of commitment, not at the moment its consequences become known.

**Reasoning.** The explicit chain of premises, Evidence, and Investor Judgment that connects what is known to a Decision. Reasoning is what makes a Decision inspectable by the Investor who made it, and by that Investor at a later time. A Decision without articulated Reasoning cannot be evaluated for Decision Quality; it can only be evaluated for outcome.

**Evidence.** A fact or observation that bears on the truth of a premise used in Reasoning. Evidence has a source and a degree of reliability. Evidence is not itself a conclusion, and the presence of Evidence does not imply that any particular conclusion follows from it.

**Attention.** The Investor's finite capacity to engage deliberately with information. Attention is scarce; it does not scale with the volume of information available. Anything that competes for the Investor's Attention without being relevant to a Decision degrades Decision Quality by displacing what the Investor might otherwise have considered.

**Uncertainty.** The condition in which a fact relevant to a Decision is not, and cannot presently be, known with confidence. Uncertainty is a permanent, structural condition of investing. It is not a defect to be eliminated, and its presence in a Decision's Reasoning is not itself a weakness of that Reasoning; concealing Uncertainty is a weakness.

**Learning.** The Investor's capacity to improve future Reasoning by examining prior Decisions, the Reasoning that produced them, and what subsequently became known, in relation to one another. Learning requires that Reasoning be preserved in a form that can later be revisited; it does not occur merely because an outcome became known.

**Decision Quality.** The soundness of the Reasoning behind a Decision, assessed as of the time the Decision was made, independent of the outcome that later occurred. A Decision made through sound Reasoning does not become a high-quality decision retroactively because its outcome was favorable, nor a low-quality decision because its outcome was unfavorable.

**Investor Judgment.** The Investor's own act of weighing Evidence, Reasoning, and Uncertainty to reach a Decision. Investor Judgment belongs exclusively to the Investor. It can be informed, supported, and challenged; it cannot be delegated, automated, or exercised on the Investor's behalf by Atlas or by any other party. Atlas Core's own Judgment Domain Object names the settled determination a completed act of reasoning produces, not the act of reaching it; Investor Judgment names that act itself, not any settled record of its result. The two SHALL NOT be treated as interchangeable.

## 6. Product Philosophy

### 6.1 Decision Quality Over Outcome

A product that surfaces only outcomes cannot help an investor distinguish skill from chance. Atlas protects Decision Quality as the value it holds most directly, and treats outcome as informative about the world — never as a verdict on Investor Judgment.

### 6.2 Human Ownership

The Investor owns every Decision. Ownership is not a courtesy extended to the Investor; it is the condition without which the concepts of Reasoning, Learning, and Decision Quality lose their meaning. A decision made on an investor's behalf, or made to appear as though it were the investor's own when it was not, cannot be owned, and therefore cannot be learned from. Atlas's philosophy treats human ownership as a precondition of everything else it does, not as one feature among others.

### 6.3 Uncertainty as a Permanent Condition

Investing does not become certain with more data, faster analysis, or better tools. Atlas treats Uncertainty as a fact to be represented faithfully, not a problem to be engineered away. A product that hides uncertainty to appear more confident produces investors who are less prepared for the futures that do not match their expectations.

### 6.4 Attention as the Scarce Resource

Information is abundant; an investor's capacity to engage with it deliberately is not. Atlas's philosophy treats attention, not information, as the resource to be protected. A product that maximizes the volume of information presented to an investor, without regard to what currently deserves that investor's attention, degrades the very Investor Judgment it claims to support.

### 6.5 Reasoning as the Durable Artifact

An outcome is a fact about the world; reasoning is a fact about the investor's own mind at the time of a decision. Only the latter can be examined, questioned, and improved. Atlas's philosophy treats the preservation of reasoning — not the recording of transactions or the tracking of performance — as its central and most durable responsibility.

### 6.6 Learning as the Purpose of Memory

A record of past decisions has value only insofar as it supports learning. Atlas does not preserve history for its own sake, or as an audit trail incidental to some other purpose. It preserves history because Investor Judgment improves by examining what was reasoned, what was uncertain, and what later became known, together.

### 6.7 Artificial Intelligence as Assistant to Investor Judgment

Atlas's philosophy holds that artificial intelligence exists, within this product, to extend the investor's capacity to reason — to surface evidence, organize information, propose considerations, and challenge assumptions — never to exercise Investor Judgment on the investor's behalf. An AI-originated contribution is always attributable as such, and is always subject to the investor's own scrutiny. Atlas's use of artificial intelligence is bounded by this role; it does not expand to any role in which the investor's own commitment to a decision is no longer the operative act.

### 6.8 Simplicity as Discipline

Simplicity, in Atlas's philosophy, is not the absence of depth but the deliberate withholding of complexity until it is warranted by the investor's own reasoning. A product may possess considerable depth and still be simple, if that depth is never presented before it is relevant. Simplicity that is achieved by omitting something the investor needed is not simplicity; it is a failure to inform.

### 6.9 Trust Earned Through Transparency

Atlas's philosophy holds that trust cannot be asserted; it is earned by making the basis of every claim, suggestion, and piece of evidence inspectable by the investor who relies on it. A product that asks to be trusted without being examinable asks for something it has not earned. Atlas's obligation is to remain examinable, not to appear trustworthy.

## 7. Product Principles

The following principles operationalize the philosophy stated in Section 6. Each carries a stable identifier, cited in parentheses alongside the philosophy subsection it derives from. A subordinate document invoking a principle SHALL cite it by identifier. Together, they bind every subordinate specification.

**PP-001 — Attention Before Information** *(6.4).* Where Atlas proactively selects, prioritizes, recommends, or presents information as deserving the Investor's Attention, Atlas SHALL determine that the information deserves that Attention before presenting it. This principle governs Atlas's own proactive choices; it does not restrict the Investor's deliberate exploration or retrieval of information the Investor has directly requested. A subordinate specification SHALL NOT justify a proactive presentation solely on the grounds that the underlying information exists or is available.

**PP-002 — Thinking Before Action** *(6.5).* Atlas SHALL support the Investor's Reasoning before, and as a precondition of, supporting any substantive investment decision or capital-allocation commitment available to the Investor. A subordinate specification SHALL NOT present such a decision or commitment in a way that invites commitment before the Reasoning behind it has been engaged. This principle does not extend to a product action that carries no capital-allocation consequence.

**PP-003 — Artificial Intelligence Supports Investor Judgment, and Never Replaces It** *(6.7).* Every capability that uses artificial intelligence SHALL be designed so that Investor Judgment remains the operative act in every Decision. A subordinate specification SHALL NOT introduce a capability in which a Decision is made, or is reasonably perceived by the Investor to have been made, by Atlas rather than by the Investor.

**PP-004 — Complexity Is Disclosed Progressively, and Withheld by Default** *(6.8).* Atlas SHALL reveal complexity only where it is materially relevant to the Investor's current objective, or where the Investor has explicitly requested it. Atlas SHALL NOT present complexity meeting neither condition. This obligation is continuous: a subordinate specification SHALL reassess it as the specification evolves, not treat it as satisfied once and set aside.

**PP-005 — Human Ownership Is Preserved in Every Decision** *(6.2).* Every Decision SHALL be attributable to the Investor as its owner. No subordinate specification SHALL design a capability under which a Decision is recorded without an identifiable act of commitment by the Investor.

**PP-006 — Reasoning Is Preserved Independently of Outcome** *(6.5–6.6).* Atlas SHALL preserve the Reasoning behind a Decision in a form that remains inspectable regardless of the Decision's later outcome. A subordinate specification SHALL NOT design a capability that discards, overwrites, or obscures previously recorded Reasoning.

**PP-007 — Uncertainty Is Disclosed, Not Concealed** *(6.3).* Where a Decision's Reasoning rests on Evidence that is incomplete, contested, or uncertain, that condition SHALL be disclosed to the Investor. A subordinate specification SHALL NOT present a conclusion with greater confidence than its underlying Evidence and Reasoning support.

**PP-008 — Provenance Is Always Attributable** *(6.9).* Every piece of content Atlas presents to the Investor SHALL be attributable to its origin — Atlas-originated, Investor-originated, or drawn from an external source. A subordinate specification SHALL NOT present Atlas-originated content in a way that could reasonably be mistaken for the Investor's own reasoning, or vice versa.

**PP-009 — Decision Quality Is Evaluated Independently of Outcome** *(6.1).* No subordinate specification SHALL design a capability that evaluates, scores, or characterizes a Decision's quality by reference to its outcome alone. Decision Quality SHALL be evaluated with reference to the Reasoning that produced the Decision, assessed as of the time it was made.

## 8. Responsibilities

### 8.1 Responsibilities of Atlas

Atlas SHALL:

- direct the Investor's Attention toward what is relevant to the Investor's investment objectives, active Reasoning, a prospective Decision, or a recorded Decision — this responsibility SHALL NOT be conditioned on a Decision already being pending or recorded (PP-001);
- make Evidence available for the Investor's examination, together with its source and reliability where known (PP-002, PP-007);
- make the Reasoning behind a Decision explicit, recorded, and inspectable at a later time (PP-002, PP-006);
- disclose Uncertainty wherever it materially bears on a Decision's Reasoning (PP-007);
- support the Investor's Learning by preserving the relationship between prior Reasoning and what subsequently became known (PP-006);
- attribute every piece of Atlas-originated content to its origin (PP-008).

Atlas SHALL NOT:

- commit the Investor's capital, or take any action with that effect, without an identifiable act of Investor Judgment (PP-003, PP-005);
- present a conclusion with a degree of confidence unsupported by its underlying Evidence and Reasoning (PP-007);
- conceal, minimize, or obscure Uncertainty material to a Decision (PP-007);
- present Atlas-originated content in a manner that obscures its origin (PP-008);
- discard or silently alter previously recorded Reasoning (PP-006);
- evaluate or characterize Decision Quality by reference to outcome alone (PP-009).

### 8.2 Responsibilities of the Investor

The Investor retains ownership of, and accountability for, every Decision, including a Decision reached with Atlas's assistance (PP-005). The exercise of Investor Judgment is what constitutes a Decision; Atlas's contribution to that Decision, however extensive, does not transfer ownership of it.

The Investor is responsible for engaging with the Reasoning Atlas makes available, rather than accepting a conclusion without examining the Evidence and Reasoning behind it. Atlas's role in disclosing Uncertainty and surfacing Evidence does not relieve the Investor of the responsibility to weigh them. An Investor who accepts Atlas-originated content without independent scrutiny remains accountable for the Decision that follows, in the same manner as for a Decision reached by any other means.

## 9. Relationship to Subordinate Specifications

This Doctrine is the sole source of product philosophy, product principles, and the responsibilities of Atlas and the Investor. Every other product document is subordinate to it.

**APS Product Specifications** define the specific product capabilities, workflows, and behaviors through which the principles and responsibilities stated here are realized. An APS specification SHALL demonstrate how it satisfies the applicable Product Principles, cited by identifier (PP-XXX), and the responsibilities of Section 8; it SHALL NOT introduce a capability that no reading of this Doctrine supports.

**UX Specifications** define the interaction, screen, and workspace-level design through which an APS specification is expressed to the Investor. A UX specification SHALL be consistent with the philosophy and principles of this Doctrine as expressed through its governing APS specification; it SHALL NOT independently establish product philosophy, principle, or responsibility.

**Visual Design Artifacts** express the visual and interaction detail of an approved UX specification. A visual design artifact carries no authority beyond what its governing UX and APS specifications establish.

**Product Implementations** realize an approved specification in working software. An implementation detail — including any technical constraint, platform limitation, or engineering convenience — SHALL NOT be treated as grounds for revising this Doctrine, an APS specification, or a UX specification. Where an implementation cannot satisfy an upstream specification, the specification is either satisfied by different technical means or is formally reconsidered through the governing amendment process of the document it belongs to; it is never silently narrowed by what was easiest to build.

Where any subordinate document is silent on a matter this Doctrine addresses, this Doctrine's statement governs directly, without requiring restatement in the subordinate document.

## 10. Explicit Non-Goals

This Doctrine does not, and future amendments to it SHALL NOT, address:

- specific screens, pages, or workspace layouts;
- interaction design, navigation structure, or component behavior;
- visual design, including typography, color, spacing, or motion;
- the choice of artificial intelligence model, technique, or provider;
- algorithms, data structures, or system architecture;
- product roadmap, release sequencing, or feature prioritization;
- business model, pricing, or commercial terms.

A proposed amendment to this Doctrine that would introduce content from this list SHALL be rejected on that basis alone, regardless of the merit of the underlying product idea. Such content belongs in a subordinate specification, governed by, and consistent with, this Doctrine.

## 11. Governance

### 11.1 Interpretation

Every term defined in Section 5 carries the meaning stated there wherever it is used in a document that derives from this Doctrine. Where a term used in this Doctrine is not defined in Section 5, it carries its ordinary meaning, constrained by the philosophy of Section 6 and the principles of Section 7.

Where a subordinate document's authors are uncertain whether a proposed product decision is consistent with this Doctrine, the test is Section 1's own test, applied to the decision under review: would the statement, or the decision it authorizes, remain true and correct if Atlas's interface, technology, or implementation changed completely? If not, the decision does not belong at this Doctrine's level, and its consistency with this Doctrine is instead judged by whether it serves the philosophy and principles this Doctrine states, not by whether it resembles this Doctrine's own content.

### 11.2 Amendment and Evolution

This Doctrine SHALL be amended only when a genuine deficiency is demonstrated — a philosophy, principle, definition, or responsibility that proves incomplete, internally inconsistent, or insufficient to govern a class of product decisions subordinate documents genuinely require guidance on. This Doctrine SHALL NOT be amended to accommodate the convenience of a single subordinate specification, a single implementation constraint, or a single product deadline.

An amendment SHALL state explicitly what changed and why. An amendment SHALL NOT silently redefine a term, principle, or responsibility already stated; where a prior statement is superseded, the amendment SHALL say so, and the superseded statement SHALL remain recoverable in this document's revision history rather than erased.

A change to this Doctrine is a higher-order change: because every subordinate document derives from it, an amendment SHALL be reviewed for its consequences across the full body of subordinate specifications before it is adopted, and subordinate documents affected by the amendment SHALL be reviewed for continued consistency following it.

### 11.3 Traceability

Every Product Principle traces explicitly, by the citation carried in its own statement, to the philosophy subsection of Section 6 it derives from; every responsibility stated in Section 8 traces, by identifier, to one or more Product Principles. Every provision of a subordinate specification SHALL be traceable, directly or through the specification's own governing document, and by citation of the relevant Product Principle identifier, to a principle or responsibility stated here. A product capability with no such traceable basis has no standing under this Doctrine, regardless of its apparent usefulness.

### 11.4 Status Discipline

This document carries the status **Draft, v0.4** as stated at its head. A Draft status means this Doctrine is a candidate governing document, published for review, and not yet the final, binding authority described in Section 2. Promotion to **Final** status requires deliberate review and adoption; it SHALL NOT occur by default, by disuse of the amendment process, or by subordinate documents simply proceeding as though this Doctrine were already Final.

Once this Doctrine reaches Final status, that status governs until an amendment, adopted under Section 11.2, states otherwise. A Final status does not mean every question this Doctrine could address has been settled; it means this Doctrine, within the scope stated in Section 1, is the current governing authority for the Atlas Product Architecture.
