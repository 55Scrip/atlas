import type { CSSProperties } from "react";
import { StatusBadge, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { FitBadge } from "../portfolioFit/FitBadge";
import { StanceBadge } from "../stance/StanceBadge";
import {
  ANALYSIS_COVERAGE_LEVEL_KEY,
  ANALYSIS_COVERAGE_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
} from "../status/statusTone";
import type { DiscoveryCandidateView } from "./discoveryCandidatesApi";
import styles from "./DiscoveryCandidateTable.module.css";

/**
 * Convergence Sprint 4C -- the dense, comparative rendering of the
 * Worth-reviewing and Everything-else tiers.
 *
 * Sprint 4B gave Discovery a real universe (22 independent candidates
 * against the live database), which the previous IA could not carry:
 * both lower tiers rendered as one-per-line "ticker, Fit badge, Open
 * Investment Case" rows, so the only comparable signal down the page
 * was Fit, and reading fourteen of them meant reading fourteen
 * separate lines. This is the same table treatment Watchlist already
 * uses for exactly the same job -- scan a column, not a row at a time
 * -- reusing its own cell/header styling conventions and its
 * native keyboard-operable case control while preserving real table
 * semantics for assistive technology.
 *
 * Every column is a closed categorical vocabulary Atlas already
 * computes and already sends on `DiscoveryCandidateView`, rendered
 * through the one shared translation bank in `status/statusTone.ts`,
 * so the same state reads identically here, on Watchlist and on
 * Portfolio. Deliberately absent, because the engine has no such
 * concept: Conviction, Expected Return, Upside, Downside, catalysts,
 * and any aggregate opportunity score. Nothing here is approximated
 * from something adjacent, and no ordering is invented -- rows are
 * rendered in exactly the order `rankCandidates` returned them.
 */
const cellStyle: CSSProperties = {
  padding: "var(--space-metadata) var(--space-row)",
  textAlign: "left",
  borderBottom: "var(--width-border-hairline) solid var(--color-border-hairline)",
  fontFamily: "var(--type-family-metadata)",
  fontSize: "var(--type-body-min-size)",
};

const headerCellStyle: CSSProperties = {
  ...cellStyle,
  color: "var(--color-text-tertiary)",
  fontWeight: 500,
  fontSize: "11px",
  letterSpacing: "0.04em",
  textTransform: "uppercase",
  borderBottom: "var(--width-border-standard) solid var(--color-border-standard)",
};

export function DiscoveryCandidateTable({
  candidates,
  captionKey,
  onOpenCase,
}: {
  /** Already ranked and already tier-assigned by `rankCandidates`;
   * this component only renders, it never reorders or re-filters. */
  candidates: DiscoveryCandidateView[];
  /** Names the table for screen readers -- `Label` renders the visible
   * section heading as a `<p>`, which gives the table below it no
   * accessible name of its own. */
  captionKey: TranslationKey;
  onOpenCase: (ticker: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <div style={{ overflowX: "auto" }}>
      <table aria-label={t(captionKey)} style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={headerCellStyle}>{t("discovery.table.companyHeader")}</th>
            <th style={headerCellStyle}>{t("discovery.table.decisionHeader")}</th>
            <th style={headerCellStyle}>{t("discovery.table.currentViewHeader")}</th>
            <th style={headerCellStyle}>{t("discovery.table.coverageHeader")}</th>
            <th style={headerCellStyle}>{t("discovery.table.fitHeader")}</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <DiscoveryCandidateRow key={candidate.caseId} candidate={candidate} onOpenCase={onOpenCase} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DiscoveryCandidateRow({
  candidate,
  onOpenCase,
}: {
  candidate: DiscoveryCandidateView;
  onOpenCase: (ticker: string) => void;
}) {
  const { t } = useTranslation();

  /* Sprint 4D. The row used to override its native table role with
     `role="button"`. That made it keyboard-operable but stopped assistive
     technology from exposing it as a row. A native button in the
     company cell now owns focus and activation; pointer users can still
     click anywhere on the row. */
  function activate() {
    onOpenCase(candidate.ticker);
  }

  return (
    <tr className={styles.row} onClick={activate}>
      <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)" }}>
        <button
          type="button"
          className={styles.caseButton}
          aria-label={t("discovery.table.rowAriaLabel", { ticker: candidate.ticker })}
          onClick={(event) => {
            event.stopPropagation();
            activate();
          }}
        >
          <Text as="span" style={{ fontWeight: 600 }}>
            {candidate.ticker}
          </Text>
          {candidate.companyName !== null && (
            <>
              {" "}
              <Text as="span" color="tertiary">
                {candidate.companyName}
              </Text>
            </>
          )}
        </button>
      </td>
      <td style={cellStyle}>
        <StatusBadge
          label={t(DECISION_SUPPORT_BADGE_KEY[candidate.decisionSupportLevel])}
          tone={DECISION_SUPPORT_TONE[candidate.decisionSupportLevel]}
        />
      </td>
      {/* A `null` Stance or Fit is a real answer -- the engine could
          not evaluate this company -- never rendered as a middling
          one, and never left as an empty cell the reader has to
          interpret. */}
      <td style={cellStyle}>
        {candidate.stanceLevel !== null ? <StanceBadge level={candidate.stanceLevel} /> : <UnknownCell />}
      </td>
      <td style={cellStyle}>
        <StatusBadge
          label={t(ANALYSIS_COVERAGE_LEVEL_KEY[candidate.analysisCoverageLevel])}
          tone={ANALYSIS_COVERAGE_TONE[candidate.analysisCoverageLevel]}
        />
      </td>
      <td style={cellStyle}>{candidate.fitRating !== null ? <FitBadge rating={candidate.fitRating} /> : <UnknownCell />}</td>
    </tr>
  );
}

/** The same treatment Watchlist's own table uses for a signal the
 * engine could not produce: an em-dash carries it visually, so a
 * column of badges stays scannable, while the real sentence is there
 * for a screen reader. Never a blank cell, and never a neutral value
 * standing in for a missing one. */
function UnknownCell() {
  const { t } = useTranslation();
  return (
    <Text as="span" color="tertiary">
      <span aria-hidden="true">{"\u2014"}</span>
      <span style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>
        {t("discovery.table.notAssessed")}
      </span>
    </Text>
  );
}
