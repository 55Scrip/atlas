/**
 * Single source of truth mapping Foundation Component props to their
 * canonical UX-012D token names (frontend/src/tokens/tokens.css). Every
 * component imports from here rather than writing its own var(--...)
 * string, so a token reference exists in exactly one place.
 *
 * Only tokens with an actual canonical name in UX-012D §3 are represented
 * — the key sets below are deliberately short because most categories
 * (color primitives, radius, spacing beyond inter-section) have no
 * resolved value yet. Do not add a key here without a corresponding
 * token already declared in tokens.css.
 */

export const textColorToken = {
  primary: "var(--color-text-primary)",
  secondary: "var(--color-text-secondary)",
  tertiary: "var(--color-text-tertiary)",
} as const;
export type TextColorToken = keyof typeof textColorToken;

export const surfaceToken = {
  background: "var(--surface-background)",
  primary: "var(--surface-primary)",
  elevated: "var(--surface-elevated)",
  panel: "var(--surface-panel)",
} as const;
export type SurfaceToken = keyof typeof surfaceToken;

export const borderToken = {
  hairline: { color: "var(--color-border-hairline)", width: "var(--width-border-hairline)" },
  standard: { color: "var(--color-border-standard)", width: "var(--width-border-standard)" },
} as const;
export type BorderToken = keyof typeof borderToken;

/**
 * `space.inter-section` is the only canonical spacing token in UX-012D
 * (its own §4 naming-convention worked example) — the other five
 * conceptually-named levels (workspace margins, intra-section, card
 * padding, row spacing, metadata spacing) have never been given a literal
 * token identifier, per UX-012D §4's own rule that a conceptual
 * description does not authorize an inferred token. This map therefore
 * has exactly one entry; it is not a stand-in for a full spacing scale.
 * Its value currently resolves to 0 (frontend/src/tokens/tokens.css) —
 * no numeric value for it exists anywhere in the governing corpus.
 */
export const spaceToken = {
  "inter-section": "var(--space-inter-section)",
} as const;
export type SpaceToken = keyof typeof spaceToken;
