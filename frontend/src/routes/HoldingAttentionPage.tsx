import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams, Link as RouterLink } from "react-router-dom";
import { Button, Container, Heading, Inline, Label, Stack, StatusText, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  CONVICTION_LEVEL_KEY,
  CONVICTION_TONE,
  DECISION_SUPPORT_STATEMENT_KEY,
  type ConvictionLevel,
  type DecisionSupportLevel,
} from "../status/statusTone";
import type { PortfolioAction } from "../portfolio/derivePortfolioActions";
import { describePortfolioAction } from "../portfolio/describePortfolioAction";

/** Portfolio Workspace v1 -- the per-holding "attention detail" screen
 * matching the approved `portfolio-attention-expanded` /
 * `portfolio-decision-record` frames (found to be pixel-identical
 * copies of the same screen in the source file; treated here as one
 * screen, not two). Reuses the existing `/api/alpha-portfolio/cockpit`
 * endpoint client-side-filtered by ticker rather than adding a new
 * per-holding backend endpoint -- the same data this page's Holdings
 * table row already reads.
 *
 * "Dismiss from Attention" has no backend action anywhere in this
 * codebase (grepped `portfolio_cockpit`/`portfolio_status` routers --
 * only one real GET endpoint exists) and is rendered disabled rather
 * than wired to a fake no-op, per this sprint's "use placeholder logic
 * where backend functionality is not yet available" instruction read
 * together with "avoid speculative functionality."
 */

type CockpitAttentionReason =
  | "high_financial_risk"
  | "high_valuation_risk"
  | "low_conviction"
  | "contradicting_evidence"
  | "insufficient_evidence";

interface CockpitHoldingDetail {
  ticker: string;
  caseId: string;
  weightPercent: number;
  valueAbsolute: number | null;
  conviction: { level: ConvictionLevel };
  decisionSupport: { level: DecisionSupportLevel };
  attention: { reasons: CockpitAttentionReason[] };
}

interface PortfolioCockpitResponse {
  exists: boolean;
  holdings: CockpitHoldingDetail[];
}

type Status =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "not-found" }
  | { kind: "loaded"; holding: CockpitHoldingDetail };

/** Concentration is derived client-side from the same real weight
 * already fetched -- not a fabricated fact, and consistent with the
 * `high_concentration` `KeyFindingKind` threshold already established
 * elsewhere on this page (`PortfolioPage.tsx`). */
const CONCENTRATION_THRESHOLD_PERCENT = 15;

const ATTENTION_REASON_KEY: Record<CockpitAttentionReason, TranslationKey> = {
  high_financial_risk: "portfolio.attention.reason.high_financial_risk",
  high_valuation_risk: "portfolio.attention.reason.high_valuation_risk",
  low_conviction: "portfolio.attention.reason.low_conviction",
  contradicting_evidence: "portfolio.attention.reason.contradicting_evidence",
  insufficient_evidence: "portfolio.attention.reason.insufficient_evidence",
};

export function HoldingAttentionPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  /** UX Refinement Sprint (F-03): the `PortfolioAction` that put this
   * ticker into "Needs Your Attention", passed through route state by
   * `NeedsYourAttentionRow` -- the actual reason the user was sent here,
   * as opposed to this page's own narrower cockpit-derived risk-narrative
   * reasons below (a genuinely different, real backend vocabulary; see
   * `derivePortfolioActions.ts`'s own module docstring). Absent on a
   * direct URL visit/refresh, in which case nothing is guessed. */
  const originatingAction = (location.state as { action?: PortfolioAction } | null)?.action;
  const [status, setStatus] = useState<Status>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio/cockpit", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioCockpitResponse>;
      })
      .then((report) => {
        const holding = report.holdings.find((h) => h.ticker === ticker);
        setStatus(holding ? { kind: "loaded", holding } : { kind: "not-found" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [ticker]);

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {status.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("portfolio.loadError", { message: t("common.unknownError") })}
          </Text>
        )}
        {status.kind === "not-found" && (
          <Stack gap="inter-section">
            <Text color="tertiary" role="alert">
              {t("portfolio.holdingDetail.notFound")}
            </Text>
            <RouterLink to="/portfolio">{t("portfolio.holdingDetail.backToPortfolio")}</RouterLink>
          </Stack>
        )}
        {status.kind === "loaded" && (
          <HoldingAttentionDetail
            holding={status.holding}
            originatingAction={originatingAction}
            navigate={navigate}
            t={t}
          />
        )}
      </Stack>
    </Container>
  );
}

function HoldingAttentionDetail({
  holding,
  originatingAction,
  navigate,
  t,
}: {
  holding: CockpitHoldingDetail;
  originatingAction: PortfolioAction | undefined;
  navigate: ReturnType<typeof useNavigate>;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const isConcentrated = holding.weightPercent > CONCENTRATION_THRESHOLD_PERCENT;
  const attentionLines: string[] = [];
  if (isConcentrated) {
    attentionLines.push(t("portfolio.attention.reason.concentration", { percent: holding.weightPercent }));
  }
  for (const reason of holding.attention.reasons) {
    attentionLines.push(t(ATTENTION_REASON_KEY[reason]));
  }

  /** UX Refinement Sprint (F-03): the exact reason that put this ticker
   * into Portfolio's "Needs Your Attention" -- reuses `describePortfolioAction`
   * verbatim (no new derivation) so this text can never drift from what
   * the investor already read on Portfolio. */
  const originatingReason = originatingAction ? describePortfolioAction(originatingAction, t).reason : null;

  return (
    <Stack gap="inter-section">
      <Stack gap="metadata">
        <Text color="tertiary" as="span">
          {t("portfolio.holdingDetail.breadcrumb", { ticker: holding.ticker })}
        </Text>
        <Heading level={2}>{holding.ticker}</Heading>
        <Text color="secondary">{t("portfolio.holdingDetail.subheading")}</Text>
        <RouterLink to={`/company/${encodeURIComponent(holding.ticker)}`}>
          {t("portfolio.holdingDetail.openCompanyWorkspace")}
        </RouterLink>
      </Stack>

      {originatingReason && (
        <Surface tier="primary" bordered>
          <Stack gap="metadata">
            <Label>{t("portfolio.holdingDetail.whyAttentionHeading")}</Label>
            <Text as="p">{originatingReason}</Text>
          </Stack>
        </Surface>
      )}

      <Surface tier="primary">
        <Inline gap="inter-section" wrap style={{ justifyContent: "space-between" }}>
          <Text as="span" style={{ fontWeight: 600 }}>
            {holding.ticker}
          </Text>
          <Stack gap="metadata">
            <Label>{t("portfolio.holdingDetail.currentMarketValue")}</Label>
            <Text as="span">{holding.valueAbsolute !== null ? holding.valueAbsolute : "—"}</Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.holdingDetail.portfolioWeight")}</Label>
            <Text as="span">{holding.weightPercent}%</Text>
          </Stack>
        </Inline>
      </Surface>

      <Surface tier="primary" bordered>
        <Stack gap="metadata">
          <Label>{t("portfolio.holdingDetail.attentionHeading")}</Label>
          {attentionLines.length === 0 && (
            <Text color="secondary">{t("portfolio.holdingDetail.noAttentionReasons")}</Text>
          )}
          {attentionLines.map((line, index) => (
            <Text key={index} as="p" color="secondary">
              {line}
            </Text>
          ))}
        </Stack>
      </Surface>

      <Stack gap="metadata">
        <Label>{t("portfolio.holdingDetail.analysisContextHeading")}</Label>
        <Surface tier="primary">
          <Stack gap="row">
            <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
              <Text as="span" style={{ fontWeight: 600 }}>
                {t("portfolio.holdingDetail.decisionSupportLabel")}
              </Text>
              <Text as="span" color="secondary">
                {t(DECISION_SUPPORT_STATEMENT_KEY[holding.decisionSupport.level])}
              </Text>
            </Inline>
            <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
              <Text as="span" style={{ fontWeight: 600 }}>
                {t("portfolio.holdingDetail.convictionLabel")}
              </Text>
              <StatusText
                label={t(CONVICTION_LEVEL_KEY[holding.conviction.level])}
                tone={CONVICTION_TONE[holding.conviction.level]}
              />
            </Inline>
            <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
              <Text as="span" style={{ fontWeight: 600 }}>
                {t("portfolio.holdingDetail.riskFactorsLabel")}
              </Text>
              <Text as="span" color="secondary">
                {holding.attention.reasons.length > 0
                  ? holding.attention.reasons.map((r) => t(ATTENTION_REASON_KEY[r])).join(" ")
                  : t("portfolio.holdingDetail.noRiskFactors")}
              </Text>
            </Inline>
          </Stack>
        </Surface>
      </Stack>

      <Surface tier="primary">
        <Text color="tertiary" as="p">
          {t("portfolio.holdingDetail.contextNote")}
        </Text>
      </Surface>

      <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
        <RouterLink to="/portfolio">{t("portfolio.holdingDetail.backToPortfolio")}</RouterLink>
        <Inline gap="row" wrap>
          <Button variant="tertiary" disabled title={t("portfolio.holdingDetail.dismissUnavailable")}>
            {t("portfolio.holdingDetail.dismissButton")}
          </Button>
          <Button
            variant="primary"
            onClick={() => navigate(`/investment-case/${holding.caseId}`, { state: { origin: "portfolio" } })}
          >
            {t("portfolio.holdingDetail.recordDecisionButton")}
          </Button>
        </Inline>
      </Inline>
    </Stack>
  );
}
