/**
 * Atlas UX Freeze v1 -- Numerical formatting (Design System, "Numerical
 * Display Rules"): currency values render grouped with a symbol, and
 * percentages render at one consistent decimal place everywhere on the
 * product, never the raw unrounded figure a backend field happens to
 * carry.
 *
 * `formatPercentPoints` is named for its unit on purpose. Atlas has a
 * second, domain-specific percent formatter --
 * `investmentCase/AtlasOutlookSection.tsx`'s `formatPercent` -- which
 * takes a *fraction* (0-1) and applies a +/- return-sign convention.
 * The two are not interchangeable in either direction: passing a
 * fraction here renders "0.1%" for a tenth, and passing percentage
 * points there renders "+920.0%" for 9.2. They are deliberately kept
 * separate rather than merged, since one shared implementation would
 * have to change one of the two call sites' rendered output; only the
 * name collision is resolved.
 */

const CURRENCY_FORMATTER = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatCurrency(value: number): string {
  return CURRENCY_FORMATTER.format(value);
}

export function formatPercentPoints(value: number, fractionDigits = 1): string {
  return `${value.toFixed(fractionDigits)}%`;
}
