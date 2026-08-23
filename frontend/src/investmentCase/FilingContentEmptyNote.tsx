import { StatusText } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { FilingContentStatus } from "./filingContentStatus";

/**
 * Product Utilization Sprint 1. The one place the two honest "empty"
 * messages for a Filing-Content-Intelligence-family sub-section are
 * worded -- reused by every sub-section in `ManagementIntelligencePanel`/
 * `RegulatoryIntelligencePanel` rather than each writing its own copy,
 * so "not yet acquired" and "not yet discovered" always read identically
 * everywhere they appear.
 */
export function FilingContentEmptyNote({ status, t }: { status: FilingContentStatus; t: Translate }) {
  if (status === "has_evidence") return null;
  const label =
    status === "content_not_yet_acquired"
      ? t("investmentCase.filingContentStatus.contentNotYetAcquired")
      : t("investmentCase.filingContentStatus.noRelevantFilingKnown");
  return <StatusText label={label} tone="neutral" />;
}
