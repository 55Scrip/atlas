ATLAS — UX-005: INVESTMENT WORKSPACE SCREEN SPECIFICATION
Version: 1.0
Status: Implementation Specification
Depends on:
• UX-003 – The Atlas Working Session
• UX-004 – Investment Workspace Philosophy

Purpose

This document defines the complete Investment Workspace interface for Atlas.

It translates the philosophy established in UX-004 into a fully implementable screen specification.

The Investment Workspace is where an investor understands one Investment Case deeply enough to decide whether the current investment judgment should change.

This specification defines:

• layout
• information hierarchy
• interaction
• component behavior
• responsive behavior
• accessibility
• animation
• implementation states

────────────────────────────────────────
1. PRODUCT ROLE
────────────────────────────────────────

The Dashboard answers:

"What deserves my attention?"

The Investment Workspace answers:

"What should I conclude and decide?"

The Workspace is not a new page.

It is a focused workspace temporarily opened above the Dashboard.

Opening a Workspace should feel like lifting a document from a desk.

Closing it should feel like putting the document back.

Dashboard context must always be preserved.

────────────────────────────────────────
2. PRIMARY OBJECTIVE
────────────────────────────────────────

Within approximately thirty seconds the investor should understand:

• Why this Case was opened
• Atlas' current assessment
• What changed
• Whether anything requires action

Within approximately three minutes the investor should understand:

• the thesis
• key drivers
• valuation
• portfolio implications

Within a longer session the investor should be able to inspect:

• evidence
• assumptions
• valuation model
• historical reasoning
• previous decisions

Understanding must always precede action.

────────────────────────────────────────
3. OVERALL STRUCTURE
────────────────────────────────────────

Investment Workspace

1. Sticky Header

2. Atlas Conclusion

3. What Changed

4. Key Drivers

5. Investment Thesis

6. Evidence & Assumptions

7. Valuation

8. Portfolio Context

9. Your Decision

10. Case History

11. Completion

This order should remain consistent across all Investment Cases.

────────────────────────────────────────
4. STICKY HEADER
────────────────────────────────────────

Required:

Company Name

Ticker

Case Type

Atlas Assessment

Last Reviewed

Close Button

Example

Danaher

DHR

Watchlist Case

Atlas Assessment

Starter Position Supported

Last reviewed

Today

The header remains visible while scrolling.

The Dashboard must remain visible behind the Workspace.

────────────────────────────────────────
5. ATLAS CONCLUSION
────────────────────────────────────────

The Conclusion is the most prominent section.

Purpose

Immediately communicate Atlas' current understanding.

Structure

Headline

Supporting Explanation

Confidence

Action Requirement

Example

Danaher's competitive advantages remain intact.

The recent decline has improved expected return enough to justify initiating a position.

Confidence

Moderate

Action

Review Recommended

Possible States

Action Supported

No Action Required

Evidence Mixed

Thesis Weakened

Thesis Broken

────────────────────────────────────────
6. WHAT CHANGED
────────────────────────────────────────

Purpose

Explain why Atlas opened the Case.

Not a news feed.

Each change includes

Title

Date

Why it matters

Impact

Links

Example

Entry Range Reached

Price declined 8.4%.

Why it matters

Expected return increased while the investment thesis remained unchanged.

Impact

Valuation Improved

If nothing changed

No Material Change

The investment thesis remains intact.

No decision changes are currently required.

────────────────────────────────────────
7. KEY DRIVERS
────────────────────────────────────────

Display

Three to five primary drivers.

Each driver contains

Name

Status

Short explanation

Optional supporting metric

Possible States

Strengthening

Stable

Weakening

Broken

Uncertain

Collapsed view

Only summary.

Expanded view

Supporting evidence

Historical trend

Linked assumptions

────────────────────────────────────────
8. INVESTMENT THESIS
────────────────────────────────────────

Purpose

Describe why the company can create long-term value.

Display

Primary Thesis

Supporting Themes

Current Status

Dependencies

Contradictions

Possible States

Intact

Strengthening

Partially Weakened

Under Review

Broken

Expanded View

Historical thesis

Previous revisions

Counter thesis

Linked assumptions

────────────────────────────────────────
9. EVIDENCE & ASSUMPTIONS
────────────────────────────────────────

Evidence

Observed facts supporting or challenging the thesis.

Assumptions

Conditions that must remain true.

Default Summary

5 Assumptions

3 Holding

1 Weakening

1 Unresolved

Expanded View

Evidence

Sources

Contradictions

Historical development

Assumption States

Holding

Strengthening

Weakening

Broken

Unresolved

Contradictory evidence should remain visible.

Atlas must not force artificial certainty.

────────────────────────────────────────
10. VALUATION
────────────────────────────────────────

Purpose

Connect business quality with current price.

Hero Summary

Strong business at an attractive price.

Supporting Summary

Expected return has improved because price declined while the investment thesis remained intact.

Display

Current Price

Fair Value Range

Expected Return

Upside

Downside

Time Horizon

Scenario Cards

Downside

Base

Upside

Expanded View

Sensitivity

Model assumptions

DCF

Comparable multiples

Historical valuation

Avoid presenting valuation as false precision.

────────────────────────────────────────
11. PORTFOLIO CONTEXT
────────────────────────────────────────

Purpose

Answer

"Is this the correct investment for THIS portfolio?"

Display

Position Size

Target Allocation

Conviction

Portfolio Theme

Sector Exposure

Risk Contribution

Concentration

Capital Competition

Alternatives

Example

Portfolio Fit

Favorable

A starter position increases Life Science exposure without creating excessive concentration.

Possible States

Favorable

Neutral

Capacity Limited

Concentration Risk

Watchlist Only

────────────────────────────────────────
12. YOUR DECISION
────────────────────────────────────────

This section belongs entirely to the investor.

Atlas Assessment must never become the user's decision automatically.

Display

Atlas Assessment

↓

Your Decision

Possible Decisions

Maintain Position

Increase Position

Reduce Position

Exit Position

Start Position

Wait

Monitor

Update Thesis

Review Complete

Decision Reason

Optional.

Prompt

Why is this the right decision?

Optional

Review Again If...

────────────────────────────────────────
13. DECISION STATES
────────────────────────────────────────

Empty

No decision recorded.

Draft

Decision selected.

Not yet recorded.

Recorded

Decision

Timestamp

Reason

Review Trigger

Historical

Expandable history.

Deferred

Waiting for additional evidence.

Review Complete

No changes required.

Decision Differs From Atlas

Visible but never treated as an error.

────────────────────────────────────────
14. NO ACTION REQUIRED
────────────────────────────────────────

A dedicated completion state.

Example

The investment thesis remains intact.

No decision changes are currently required.

Primary Button

Review Complete

Never use

Submit

Execute

Confirm

────────────────────────────────────────
15. PROGRESSIVE DISCLOSURE
────────────────────────────────────────

Default reading time

≈30 seconds

↓

Intermediate review

≈3 minutes

↓

Deep investigation

≈30 minutes

Users should never be forced into deeper analysis.

────────────────────────────────────────
16. COLLAPSE BEHAVIOR
────────────────────────────────────────

Atlas Conclusion

Always expanded.

All other sections

Collapsible.

Workspace remembers

Expanded sections

Scroll position

Selected scenario

Draft notes

────────────────────────────────────────
17. CASE HISTORY
────────────────────────────────────────

Available at bottom.

Contains

Previous Conclusions

Previous Decisions

Historical Thesis

Historical Assumptions

Historical Valuation

Historical Confidence

Historical Evidence

────────────────────────────────────────
18. COMPARE MODE
────────────────────────────────────────

Possible comparisons

Previous Review

Alternative Company

Benchmark

Index

Display

Side-by-side

Primary Case always remains dominant.

────────────────────────────────────────
19. WORKSPACE STATES
────────────────────────────────────────

Normal

Loading

Updating

Uncertain

Conflicting

Critical

Archived

Watchlist

Owned Holding

Exited Position

────────────────────────────────────────
20. OVERLAY BEHAVIOR
────────────────────────────────────────

Opening

Highlight Dashboard item

↓

Background dims

↓

Workspace expands upward

↓

Focus moves into Workspace

Closing

Workspace contracts

↓

Dashboard restored

↓

Original item highlighted

Dashboard state must remain identical.

────────────────────────────────────────
21. CONTEXT PRESERVATION
────────────────────────────────────────

Preserve

Dashboard scroll

Expanded Dashboard sections

Filters

Workspace scroll

Expanded Workspace sections

Draft decision

Draft notes

Comparison mode

────────────────────────────────────────
22. RESPONSIVE DESIGN
────────────────────────────────────────

Desktop

Large centered workspace.

Laptop

Reduced margins.

Tablet

Nearly full width.

Cards stack vertically.

Mobile

Full screen.

Same information hierarchy.

No horizontal scrolling.

────────────────────────────────────────
23. ACCESSIBILITY
────────────────────────────────────────

Keyboard navigation

Visible focus

Semantic headings

Screen reader labels

Reduced motion

Color independent states

Accessible contrast

Focus restored after closing

Escape closes Workspace

Tab navigation

Focus trapped inside Workspace

────────────────────────────────────────
24. ANIMATION
────────────────────────────────────────

Calm

Purposeful

Predictable

Approximate duration

220–350 ms

Avoid

Flashy motion

Large zoom effects

Trading-terminal feeling

────────────────────────────────────────
25. FIGMA COMPONENTS
────────────────────────────────────────

Investment Workspace

Workspace Header

Atlas Conclusion

Section Header

What Changed Item

Key Driver

Evidence Card

Assumption Card

Valuation Card

Scenario Card

Portfolio Context

Decision Card

Completion Panel

Timeline

Comparison Panel

────────────────────────────────────────
26. PROTOTYPE SCENARIOS
────────────────────────────────────────

Scenario 1

Watchlist Opportunity

Scenario 2

No Action Required

Scenario 3

Starter Position

Scenario 4

Exit Position

Scenario 5

Broken Thesis

Scenario 6

Mixed Evidence

Scenario 7

Interrupted Session

Scenario 8

Compare Mode

Scenario 9

Mobile Review

────────────────────────────────────────
27. ACCEPTANCE CRITERIA
────────────────────────────────────────

The Workspace is complete when a user can:

• understand why the Case opened
• understand Atlas' assessment
• understand what changed
• inspect deeper reasoning
• understand valuation
• understand portfolio implications
• record a decision
• complete a review without unnecessary action
• return to the Dashboard without losing context

The interface must feel calm.

It must support long-term investing.

It must never resemble a trading terminal.

────────────────────────────────────────
FINAL PRINCIPLE
────────────────────────────────────────

The Investment Workspace exists to make one investment judgment clearer.

It does not exist to display everything Atlas knows.

Every component, interaction, and visual decision should help the investor understand the current Investment Case, make a deliberate decision, and confidently return to the Dashboard.