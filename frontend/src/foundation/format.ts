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

/**
 * Atlas displays an amount in the currency it is actually denominated in,
 * or in no currency at all.
 *
 * This used to be a single `Intl.NumberFormat("en-US", {currency: "USD"})`
 * with no currency parameter, so every amount in the product rendered with
 * a `$`. The live portfolio is denominated in SEK, which meant the most
 * prominent number on the Portfolio page -- 2,543,747 SEK -- read as
 * `$2,543,747`. The figures were right and the unit was wrong, which in an
 * investment tool is worse than showing nothing.
 *
 * `currency` is required rather than defaulted on purpose: a default is how
 * the wrong label got there, and making it required means the compiler, not
 * a reviewer, finds a call site that does not know its own denomination.
 * `null` is the honest value for "not established" and renders the grouped
 * number with no symbol -- never a guessed one. Nothing here converts: the
 * number passed in is the number rendered.
 */
const UNSYMBOLED_FORMATTER = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

const CURRENCY_FORMATTERS = new Map<string, Intl.NumberFormat>();

function currencyFormatter(code: string): Intl.NumberFormat | null {
  const cached = CURRENCY_FORMATTERS.get(code);
  if (cached) {
    return cached;
  }
  try {
    const formatter = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: code,
      maximumFractionDigits: 0,
    });
    CURRENCY_FORMATTERS.set(code, formatter);
    return formatter;
  } catch {
    // Intl throws RangeError on a code it does not recognise. An
    // unrecognised code is "not established", not an excuse to label the
    // amount with something else.
    return null;
  }
}

export function formatCurrency(value: number, currency: string | null | undefined): string {
  const code = currency?.trim().toUpperCase();
  const formatter = code ? currencyFormatter(code) : null;
  return (formatter ?? UNSYMBOLED_FORMATTER).format(value);
}

export function formatPercentPoints(value: number, fractionDigits = 1): string {
  return `${value.toFixed(fractionDigits)}%`;
}
