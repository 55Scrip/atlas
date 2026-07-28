UX-007P — Portfolio Workspace Final Polish

Status: Final Polish Pass
Owner: Atlas Product
Applies to: Existing Portfolio Workspace implementation after UX-007A
Depends on:
- UX-000 — The Atlas Experience
- UX-007A — Portfolio Workspace Wireframe Specification

**Correction Notice (Phase 6A, governed by the Atlas UX Source Correction Plan's own Section 3 documentary-truthfulness principles and Section 18 bullet 13 — 2026-07-28):** This document's `Applies to` line and `Depends on` list previously cited `UX-006 — Portfolio Workspace Philosophy` and `UX-007 — Portfolio Workspace Screen Specification` as settled prior/governing sources. Neither exists anywhere in the committed repository. This document's own polish-pass content is self-contained and does not require UX-006's or UX-007's content to be understood or implemented. Neither is available as current governing authority. This repository cannot verify whether either historically influenced this document's own approach — that question is neither confirmed nor denied by this correction; the unsupported active attribution is removed without deciding it. Prior text (`Applies to` line): "Applies to: Existing Portfolio Workspace implementation after UX-007 and UX-007A". Prior text (`Depends on` list): "- UX-006 — Portfolio Workspace Philosophy" and "- UX-007 — Portfolio Workspace Screen Specification". `UX-000` and `UX-007A` remain accurate, existing dependencies and are unaffected.

Purpose:
Refine the existing Portfolio Workspace implementation without changing its established information architecture, section order, reasoning model, or interaction pattern.

This is a focused polish task.

Do not add new features.
Do not add new sections.
Do not introduce a new navigation model.
Do not redesign the Workspace shell.
Do not remove any major analytical capability.

Preserve the current implementation’s successful qualities:

- Portfolio Workspace opens above the Dashboard.
- Dashboard context remains visible underneath.
- The Workspace uses internal scrolling.
- The header remains pinned.
- Atlas Portfolio Conclusion appears first.
- What Changed follows directly after the conclusion.
- Portfolio Health uses a six-card grid.
- Deeper sections use progressive disclosure.
- Collapsed sections include meaningful one-line summaries.
- Hidden Concentration remains a dedicated Atlas Insight.
- Risk Dependencies distinguish exposure from confidence.
- Scenario Analysis uses calibrated language.
- Capital Allocation compares competing uses of capital.
- Portfolio Evolution describes the portfolio as an investment system.
- The Workspace ends with a portfolio-level decision state.
- Position-level actions open related Investment Workspaces.
- The Portfolio Workspace does not execute trades.

Implement only the refinements below.


1. REFINE THE ATLAS PORTFOLIO CONCLUSION

The current conclusion contains the correct information but is somewhat text-heavy.

Improve its scan hierarchy without materially changing the content.

Structure the conclusion into four distinct informational layers:

1. Primary portfolio conclusion
2. Primary issue
3. Portfolio-level implication
4. Current decision state

Recommended content structure:

ATLAS PORTFOLIO CONCLUSION

The portfolio remains structurally sound across seven of eight positions.

Primary issue
One core assumption has broken in LVMH and requires review.

Portfolio implication
Enterprise AI remains the portfolio’s largest shared dependency, representing approximately 46% of underlying exposure.

Decision state
Two capital-allocation decisions currently deserve attention: the LVMH review and a possible Danaher initiation.

[Portfolio Review Recommended]

Reviewed today · 8 holdings · 5 watchlist

Why this conclusion? ▾

Requirements:

- Preserve the conclusion-first model.
- Keep the full section above What Changed.
- Do not turn the four layers into four separate cards.
- Use typography and spacing to establish hierarchy.
- Keep the conclusion calm and document-like.
- Avoid excessive labels if hierarchy can be communicated visually.
- The primary conclusion must remain the most prominent sentence.
- The section should remain concise enough to understand quickly.


2. REDUCE THE INITIAL WHAT CHANGED HEIGHT

The current What Changed section shows five full items and occupies too much of the first viewport.

In the default first-viewport state, show the three most decision-relevant changes:

1. LVMH core assumption broken
2. Danaher entry range reached
3. Alphabet conviction increased

Below them, add:

View 2 additional changes ▾

Expanding this control reveals:

- Constellation Software above base case
- Brookfield FRE grew 28% — Add signal maintained

Requirements:

- Preserve all five changes.
- Do not permanently remove information.
- Keep the three highest-priority changes visible by default.
- Ensure Portfolio Health becomes visible earlier in the first viewport.
- The expand interaction must not move the user to another page.
- Expanded or collapsed state must be remembered during the current session.


3. STANDARDIZE COLLAPSED SECTION SUMMARIES

The collapsed summaries are conceptually strong but need a more consistent and scannable format.

Each collapsed section must use:

SECTION TITLE
Primary summary line
Optional secondary signal line

Avoid long prose paragraphs inside collapsed states.

Use compact decision-relevant phrasing.

Apply the following summary patterns:


PORTFOLIO DRIVERS

Primary drivers: Enterprise AI · Semiconductor Capex · Interest Rates

Highest influence: Enterprise AI — Very High and strengthening


STRENGTHS

5 portfolio strengths identified

Durable moats · High business quality · Strong free cash flow · Attractive expected return · Long horizons


WEAKNESSES — LVMH REVIEW PENDING

4 portfolio weaknesses identified

AI concentration · Broken LVMH assumption · Limited inflation protection · Geographic concentration


DIVERSIFICATION

Six diversification dimensions assessed

Primary concern: AI theme concentration is not visible in sector labels alone


HIDDEN CONCENTRATION — ATLAS INSIGHT

Five holdings share one underlying dependency

Enterprise AI capital expenditure represents approximately 46% of underlying exposure


RISK DEPENDENCIES

Primary dependencies: Enterprise AI spending · Chinese luxury demand

Most certain resilience source: Insurance float quality


SCENARIO ANALYSIS

Highest exposure: AI investment slowdown · Recession

Most resilient: Persistent inflation · Strong equity markets


CAPITAL ALLOCATION

Priority decisions: Review LVMH · Evaluate Danaher initiation

Reducing LVMH to 3–4% could fund Danaher without new cash


PORTFOLIO EVOLUTION

2026 portfolio changes: AI exposure increased · LVMH assumption broken · Danaher entered range

Portfolio quality remained broadly stable


Requirements:

- Maintain one consistent typographic pattern across all collapsed sections.
- The summary should be readable without opening the section.
- The summary must not contain all supporting detail.
- Use separators such as middle dots where appropriate.
- Do not introduce cards around every collapsed summary.
- Preserve the flat reasoning-document appearance.


4. TIGHTEN RISK DEPENDENCY ROWS

The current Risk Dependency rows require too much horizontal eye movement between:

- dependency name,
- exposure,
- confidence,
- expansion control.

Refine each row into a tighter two-level structure.

Recommended row:

Enterprise AI Spending
High exposure · High confidence                                        ▾

Chinese Luxury Demand
Moderate exposure · Moderate confidence                                ▾

Interest Rate Environment
Low–Moderate exposure · High confidence                                ▾

Semiconductor Capex Cycle
High exposure · High confidence                                        ▾

Insurance Float Quality
Low exposure · Very High confidence                                    ▾

Requirements:

- Keep Exposure and Confidence as distinct concepts.
- Do not merge them into one score.
- Preserve their labels in expanded detail.
- Reduce the visual distance between the dependency and its current state.
- Keep the expansion affordance aligned consistently at the right edge.
- Maintain keyboard and screen-reader clarity.
- Do not rely only on color to distinguish levels.


5. IMPROVE SCENARIO CARD INFORMATION DENSITY

The current scenario cards contain only:

- scenario name,
- exposure state.

They use more vertical space than their information content justifies.

Keep the card format, but add one short consequence line to each card.

Recommended content:


AI Investment Slowdown

Materially Exposed

Five positions affected through shared enterprise AI dependency


Recession

Moderately Exposed

Business quality provides partial resilience, but cyclical growth would weaken


Persistent High Interest Rates

Moderately Exposed

Long-duration growth holdings face continued valuation pressure


China Demand Weakness Persists

Moderately Exposed

LVMH remains the primary source of portfolio impact


Persistent Inflation

Likely Resilient

Pricing power and strong balance sheets provide partial protection


Strong Equity Markets

Likely Resilient

Portfolio quality remains strong, though expected returns may compress


Requirements:

- Keep consequence text to one concise line or two short wrapped lines.
- Do not add probability percentages.
- Do not add predicted portfolio-loss percentages.
- Do not make the cards materially taller than they currently are.
- Preserve the calibrated state labels:
  - Likely Resilient
  - Moderately Exposed
  - Materially Exposed
  - Highly Dependent
- Clicking a card continues to reveal deeper scenario reasoning.


6. CLARIFY THE FINAL DECISION HIERARCHY

The current final Portfolio Decision Required card is strong, but its two actions are too similar in visual weight.

Create a clear hierarchy.

Primary action:

Review LVMH →

Secondary action:

Compare Capital Alternatives →

Use “Compare Capital Alternatives” instead of “Compare Danaher vs LVMH” in the button label.

The deeper comparison may still focus on Danaher versus LVMH.

Reasoning order:

1. Review the broken LVMH assumption.
2. Determine whether the position still deserves its current allocation.
3. Then compare the best alternative use of released capital.

Recommended final card:

PORTFOLIO DECISION REQUIRED

One portfolio-level decision remains unresolved.

LVMH contains a broken core assumption and may no longer justify its current 7.1% allocation.

Reducing the position to 3–4% and initiating Danaher is currently the most clearly supported reallocation, but the LVMH review must be completed first.

[Review LVMH →]   [Compare Capital Alternatives →]

Requirements:

- The primary button must have clearly greater visual weight.
- The secondary action must remain available but less prominent.
- Do not add a trade or execute action.
- Do not imply that the reallocation is final before the review is completed.


7. CLARIFY THE COMPLETION ACTION

The current “Record Portfolio Review Complete” control appears disabled or too low-contrast.

Use one of the following explicit states.


STATE A — UNRESOLVED DECISION EXISTS

The completion control remains disabled.

Label:

Record Portfolio Review Complete

Supporting explanation:

Complete the unresolved LVMH review before recording this portfolio review as complete.

Requirements:

- The disabled state must look intentionally unavailable.
- The reason must be visible.
- Do not leave the user guessing why it cannot be selected.


STATE B — NO UNRESOLVED DECISION EXISTS

The completion control becomes active.

Label:

Record Portfolio Review Complete

Supporting explanation:

This records the review and returns you to the preserved Dashboard state.

Requirements:

- The active state must have sufficient contrast.
- It should feel like completion, not transaction execution.
- It should remain visually secondary to any genuine decision action.

For the current prototype, use STATE A because a portfolio-level decision remains unresolved.


8. REDUCE RELATED WORKSPACE CLUTTER

The current Related Investment Workspaces section displays too many equally weighted buttons.

Show only the two most relevant secondary Workspaces directly:

- Open Danaher
- Open Alphabet

Then add:

View 2 other related Workspaces ▾

Expanding reveals:

- Open Brookfield Asset Management
- Open Microsoft

Requirements:

- Keep Review LVMH inside the primary decision card, not in the secondary Workspace list.
- Preserve all related Workspace links.
- Reduce the menu-like feeling at the bottom.
- Maintain state preservation when a related Investment Workspace opens.
- Closing the Investment Workspace must return the user to the same Portfolio Workspace scroll position and expanded state.


9. PRESERVE THE EXISTING SECTION ORDER

Do not change the established sequence:

1. Atlas Portfolio Conclusion
2. What Changed
3. Portfolio Health
4. Portfolio Drivers
5. Strengths
6. Weaknesses
7. Diversification
8. Hidden Concentration
9. Risk Dependencies
10. Scenario Analysis
11. Capital Allocation
12. Portfolio Evolution
13. Final Decision State
14. Related Investment Workspaces
15. Review Completion

Do not introduce tabs.
Do not introduce a sidebar.
Do not create separate portfolio pages.
Do not move the final decision state higher in the Workspace.


10. PRESERVE THE CURRENT VISUAL CHARACTER

Continue using the established Atlas dark visual language.

Preserve:

- restrained amber for meaningful review states,
- restrained green for positive or resilient states,
- muted red only for genuine deterioration or material exposure,
- low-noise section boundaries,
- wide Workspace layout,
- substantial internal whitespace,
- subtle elevation,
- thin dividers,
- quiet interaction affordances.

Do not:

- increase visual saturation,
- add bright warning banners,
- add decorative illustrations,
- add large pie charts,
- add radial gauges,
- add performance-celebration graphics,
- make every section a boxed card,
- use animation to attract attention.


11. PRESERVE ATLAS EXPERIENCE PRINCIPLES

The polished result must remain consistent with UX-000.

The Workspace must feel:

- calm,
- focused,
- conclusion-first,
- memory-aware,
- deliberate,
- non-transactional,
- respectful of uncertainty,
- complete when the work is done.

The user should be able to scan the collapsed Workspace and understand:

- the portfolio is structurally sound,
- LVMH requires review,
- AI is the primary shared dependency,
- Danaher is the strongest current capital-allocation opportunity,
- one portfolio-level decision remains unresolved.

The user should not need to open every section to understand the current state.


12. REQUIRED POLISH FRAMES

Update or create the following Figma frames:

1. Portfolio Workspace — Refined First Viewport
2. Portfolio Workspace — Three Visible Changes
3. Portfolio Workspace — What Changed Expanded
4. Portfolio Workspace — All Sections Collapsed with Standardized Summaries
5. Portfolio Workspace — Tightened Risk Dependency Rows
6. Portfolio Workspace — Refined Scenario Cards
7. Portfolio Workspace — Final Decision Required
8. Portfolio Workspace — Completion Disabled with Explanation
9. Portfolio Workspace — Related Workspaces Collapsed
10. Portfolio Workspace — Related Workspaces Expanded
11. Portfolio Workspace — Investment Workspace Opened from Portfolio Context
12. Portfolio Workspace — Returned to Preserved State


13. REQUIRED PROTOTYPE INTERACTIONS

The prototype must support:

- expand Why This Conclusion,
- expand and collapse the two additional What Changed items,
- scan all standardized collapsed summaries,
- expand Risk Dependencies,
- open a scenario card,
- select Review LVMH as the primary decision path,
- select Compare Capital Alternatives as the secondary path,
- see why Record Portfolio Review Complete is unavailable,
- expand the additional Related Investment Workspaces,
- open a related Investment Workspace,
- return to the exact preserved Portfolio Workspace position.


14. VALIDATION CHECKLIST

Before completing this polish pass, verify:

- The conclusion is faster to scan.
- The primary issue is distinct from the overall portfolio conclusion.
- Portfolio Health appears earlier in the initial experience.
- Only three What Changed items appear by default.
- All collapsed summaries use a consistent pattern.
- No collapsed summary becomes a paragraph.
- Risk Dependency states are easier to associate with their names.
- Scenario cards contain one useful consequence line.
- Review LVMH is visibly the primary action.
- Compare Capital Alternatives is visibly secondary.
- Completion is disabled for a clearly stated reason.
- Only two related Workspaces appear initially.
- The remaining related Workspaces remain accessible.
- No section order changed.
- No new feature or navigation model was introduced.
- The Portfolio Workspace remains calm and non-transactional.
- The Dashboard remains visible underneath.
- Portfolio and Investment Workspace state preservation still works.


15. COMPLETION STANDARD

This polish task is complete when:

- the first viewport communicates conclusion, primary issue, decision state, and three material changes without excessive height;
- the entire collapsed Workspace can be scanned as a coherent portfolio summary;
- risk and scenario information is easier to interpret;
- the final decision path has one clear primary action;
- review completion has an explicit available or unavailable state;
- related Workspaces no longer resemble an undifferentiated menu;
- no structural redesign was required;
- the Portfolio Workspace is ready to be considered wireframe-complete.

Do not perform additional conceptual expansion after completing these refinements.

After this pass, preserve the Portfolio Workspace design as the established reference implementation for future Atlas Workspaces.