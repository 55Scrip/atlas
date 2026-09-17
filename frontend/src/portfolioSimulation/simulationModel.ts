/**
 * Portfolio Editing & Simulation Layer v1 -- the hypothetical portfolio.
 *
 * Atlas's Portfolio is not only a record of what the investor owns; it
 * is also where they ask "what if I reduced META?". Those are different
 * questions and must not share a state: exploring a change is not
 * making one, and nothing explored here may ever read as evidence that
 * the investor acted.
 *
 * The model is deliberately a pure transformation:
 *
 *     applyPortfolioEdits(base, edits) -> HypotheticalPortfolio
 *
 * `base` is never mutated, `edits` are absolute target values keyed by
 * holding identity, and the result is recomputed from scratch on every
 * call. That buys three things this sprint needs: edits compose in any
 * order without drift, reset is `{}` rather than an inverse operation,
 * and a future Portfolio Assessment can call this with any edit set and
 * compare the result against the base without reconstructing anything
 * from the UI.
 *
 * ECONOMIC MODEL, and why it is this one
 *
 * The audit that decided it, against the real 25-holding portfolio:
 *
 * - `quantity` and `price` are `null` for **all 25 holdings**. Atlas
 *   holds no share counts, so a "+1 share" control would be inventing
 *   one. The editable unit is therefore the position's absolute value,
 *   which is present and trusted for every holding.
 * - `weightPercent` sums to 99.9997% and `cash_*` is unset, so the
 *   portfolio is fully invested with no unallocated residual.
 * - Cash/unallocated capital is nonetheless a real, first-class,
 *   investor-settable Atlas concept (`cash_weight_percent` /
 *   `cash_value_absolute` on the persisted state, editable in
 *   Portfolio's own form, rendered in Allocation and Pulse). It is
 *   present-but-unset here, which is different from absent.
 *
 * So freed capital goes to **simulated unallocated capital**, using
 * that existing representation rather than a new one. Total portfolio
 * value is conserved: reducing a position moves value from the holding
 * to unallocated, and no other holding's value is touched. Weights are
 * then value / total (holdings + unallocated), which keeps the whole
 * allocation summing to 100% and -- importantly -- means reducing META
 * does not silently inflate every other holding's weight.
 *
 * An increase draws from unallocated capital and is capped by what is
 * available, because a simulation that quietly spends money the
 * investor does not have is not a useful answer. With a fully-invested
 * portfolio that means funding an increase by first reducing something,
 * which is exactly the reallocation question this layer exists for.
 */

/** A holding's identity for editing purposes.
 *
 * `caseId` first: it is the stronger identity and is present for every
 * real holding. Ticker alone would collide across share classes and
 * venues, which is precisely the kind of silent mis-edit this key
 * exists to prevent. The ticker fallback keeps a case-less holding
 * editable rather than excluding it. */
export function holdingKey(holding: { caseId: string | null; ticker: string }): string {
  return holding.caseId ? `case:${holding.caseId}` : `ticker:${holding.ticker}`;
}

export interface SimulationBaseHolding {
  ticker: string;
  caseId: string | null;
  /** The persisted position value. Trusted: present for all 25 real
   * holdings. This, not a share count, is what an edit changes. */
  valueAbsolute: number;
  currency: string | null;
}

export interface PortfolioSimulationBase {
  holdings: SimulationBaseHolding[];
  /** Persisted unallocated capital, or 0 when the investor has not set
   * any. Never derived from a weight residual -- Atlas does not treat
   * "weights don't quite reach 100" as cash, and neither does this. */
  unallocatedValue: number;
}

/** One position's absolute target value. Absolute rather than a delta
 * so that repeated edits to the same holding replace rather than
 * accumulate, which is what makes the result order-independent and
 * reset exact. */
export type PortfolioEdits = Readonly<Record<string, number>>;

export interface HypotheticalHolding {
  key: string;
  ticker: string;
  caseId: string | null;
  currency: string | null;
  baseValue: number;
  baseWeightPercent: number;
  hypotheticalValue: number;
  hypotheticalWeightPercent: number;
  deltaValue: number;
  deltaWeightPercent: number;
  /** The investor has taken this position to zero in the simulation.
   * The holding is still here -- nothing is deleted, and restoring it
   * is one click -- it simply holds nothing. */
  isRemoved: boolean;
  isChanged: boolean;
}

export interface HypotheticalPortfolio {
  holdings: HypotheticalHolding[];
  /** Conserved: always equals the base total. Value moves between
   * positions and unallocated capital; it never appears or vanishes. */
  totalValue: number;
  baseUnallocatedValue: number;
  unallocatedValue: number;
  unallocatedWeightPercent: number;
  changedCount: number;
  isDirty: boolean;
}

/**
 * Snap a value that is within rounding dust of zero to exactly zero.
 *
 * Found in live verification, not in the unit tests: a base of 114,154
 * gives a step of 11,415.4, which is not exactly representable in
 * binary, so ten reductions land on ~1e-11 rather than 0. The position
 * displayed as "$0" but was not `=== 0`, so it did not count as removed
 * and its `−10%` control stayed enabled. The earlier tests missed it
 * because their fixture's 400,000 divides into a step that is exact.
 *
 * The tolerance is relative to the position's own size, because
 * absolute dust scales with the number: a hundredth of one percent of
 * the base is far below any currency's smallest unit and far above the
 * accumulated error of ten subtractions.
 */
function snapToZero(value: number, baseValue: number): number {
  return Math.abs(value) < Math.abs(baseValue) * 1e-9 ? 0 : value;
}

function weightOf(value: number, total: number): number {
  return total > 0 ? (value / total) * 100 : 0;
}

/**
 * The whole simulation, as one pure function.
 *
 * Clamping happens here rather than in the edit callers so that every
 * path -- a button, a typed value, a future Assessment calling this
 * directly -- gets the same guarantees: no position below zero, and no
 * increase beyond the capital actually available to fund it.
 */
export function applyPortfolioEdits(
  base: PortfolioSimulationBase,
  edits: PortfolioEdits,
): HypotheticalPortfolio {
  const baseHoldingsValue = base.holdings.reduce((sum, h) => sum + h.valueAbsolute, 0);
  const totalValue = baseHoldingsValue + base.unallocatedValue;

  // First pass: the requested value for each holding, floored at zero.
  // A position can be taken to nothing; it can never go short.
  const requested = base.holdings.map((holding) => {
    const key = holdingKey(holding);
    const edited = edits[key];
    const value =
      edited === undefined
        ? holding.valueAbsolute
        : snapToZero(Math.max(0, edited), holding.valueAbsolute);
    return { holding, key, value };
  });

  // Second pass: increases are funded from unallocated capital, so the
  // whole set of increases is capped by what reductions plus existing
  // unallocated actually make available. Scaling the overspend back
  // proportionally keeps the result deterministic regardless of the
  // order the edits were made in -- the alternative, honouring edits
  // first-come, would make two identical edit sets disagree.
  const requestedTotal = requested.reduce((sum, r) => sum + r.value, 0);
  const overspend = requestedTotal - totalValue;
  let resolved = requested;
  if (overspend > 0) {
    const increases = requested.filter((r) => r.value > r.holding.valueAbsolute);
    const headroom = increases.reduce((sum, r) => sum + (r.value - r.holding.valueAbsolute), 0);
    const scale = headroom > 0 ? Math.max(0, (headroom - overspend) / headroom) : 0;
    resolved = requested.map((r) =>
      r.value > r.holding.valueAbsolute
        ? { ...r, value: r.holding.valueAbsolute + (r.value - r.holding.valueAbsolute) * scale }
        : r,
    );
  }

  const holdingsValue = resolved.reduce((sum, r) => sum + r.value, 0);
  // Conservation, stated as arithmetic: whatever the positions do not
  // hold, unallocated capital does.
  const unallocatedValue = totalValue - holdingsValue;

  const holdings: HypotheticalHolding[] = resolved.map(({ holding, key, value }) => {
    const baseWeightPercent = weightOf(holding.valueAbsolute, totalValue);
    const hypotheticalWeightPercent = weightOf(value, totalValue);
    return {
      key,
      ticker: holding.ticker,
      caseId: holding.caseId,
      currency: holding.currency,
      baseValue: holding.valueAbsolute,
      baseWeightPercent,
      hypotheticalValue: value,
      hypotheticalWeightPercent,
      deltaValue: value - holding.valueAbsolute,
      deltaWeightPercent: hypotheticalWeightPercent - baseWeightPercent,
      isRemoved: value === 0 && holding.valueAbsolute > 0,
      isChanged: value !== holding.valueAbsolute,
    };
  });

  const changedCount = holdings.filter((h) => h.isChanged).length;
  return {
    holdings,
    totalValue,
    baseUnallocatedValue: base.unallocatedValue,
    unallocatedValue,
    unallocatedWeightPercent: weightOf(unallocatedValue, totalValue),
    changedCount,
    isDirty: changedCount > 0,
  };
}

/** Capital available to fund an increase, in the current hypothetical
 * state. Exposed so a control can disable itself at the cap rather than
 * letting the model silently clamp an edit the investor asked for. */
export function availableCapital(hypothetical: HypotheticalPortfolio): number {
  return Math.max(0, hypothetical.unallocatedValue);
}

/**
 * The step a `−` / `+` control moves a position by: a tenth of its
 * *persisted* value, so the step is stable no matter how many times it
 * has already been pressed, and so ten presses take a position to zero
 * exactly.
 *
 * Deliberately not "one share": `quantity` is null for every holding in
 * the real portfolio, so a share-denominated control would be inventing
 * a unit Atlas does not have. The step is stated in the control's own
 * accessible name for the same reason.
 */
export function editStep(baseValue: number): number {
  return baseValue / 10;
}

/** Set one position's target value. Returns a new edit set; the input
 * is never mutated. An edit that lands back on the persisted value
 * removes itself, so "reduce then restore" leaves no residue and the
 * portfolio reports itself clean. */
export function setPosition(edits: PortfolioEdits, key: string, value: number, baseValue: number): PortfolioEdits {
  const next = { ...edits };
  const clamped = Math.max(0, value);
  if (clamped === baseValue) delete next[key];
  else next[key] = clamped;
  return next;
}

/** Drop one position's edit, restoring it to its persisted value. */
export function resetPosition(edits: PortfolioEdits, key: string): PortfolioEdits {
  const next = { ...edits };
  delete next[key];
  return next;
}

/** Drop every edit. The hypothetical portfolio then equals the
 * persisted one exactly -- not approximately, because the base was
 * never mutated to begin with. */
export function resetSimulation(): PortfolioEdits {
  return {};
}
