/**
 * Product Sprint 12 (Decision Workflow Consolidation) -- extracted from
 * `InvestmentCasePage.tsx` (its own original docstring, preserved here):
 * per the governing (unimplemented) Decision-Implementation-Design.md,
 * `userId` "has no future semantic role" and is retained only as legacy
 * compatibility metadata -- never shown to the investor. This fixed,
 * documented placeholder is used until Atlas Alpha has a real identity
 * system; it is not real user data, and no authentication is added.
 *
 * Moved to its own module so both `InvestmentCasePage.tsx` and the new
 * `StartDecisionSection.tsx` (Deliverable 3 -- Start Decision) can reuse
 * the exact same constant without a circular import between the two.
 */
export const ALPHA_PLACEHOLDER_USER_ID = "00000000-0000-0000-0000-000000000001";
