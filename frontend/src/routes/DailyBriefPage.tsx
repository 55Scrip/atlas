import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation } from "../i18n";

interface ChangeFindingView {
  id: string;
  category: string;
  direction: "positive" | "negative" | "neutral";
  previousState: string;
  currentState: string;
}

interface DailyBriefEntryView {
  caseId: string;
  ticker: string | null;
  headline: string;
  changeSummary: string;
  whyItMatters: string;
  thesisImpact: string;
  changes: ChangeFindingView[];
}

interface DailyBriefView {
  generatedAt: string;
  summary: string;
  entries: DailyBriefEntryView[];
}

type DailyBriefStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; brief: DailyBriefView };

/**
 * Daily Brief v1 -- a pure distribution layer over Investment Case
 * Change Intelligence: "what changed today that deserves the
 * investor's attention." Every fact rendered here is a direct read of
 * the single `GET /daily-brief` response, itself assembled from each
 * Portfolio holding's / Watchlist entry's already-computed
 * `ChangeIntelligence` (see `atlas/analysis_engine/daily_brief.py`) --
 * nothing here is computed, scored, or ranked by this page.
 *
 * Replaces this route's earlier "Implementation Sprint 1" content
 * (investor-activity/outstanding-work derived, built before Investment
 * Case Intelligence or Change Intelligence existed) -- that content
 * was always a "differently-shaped... presentation of facts that
 * already exist elsewhere" (Dashboard, History), by its own prior
 * docstring, so nothing unique is lost; the route and nav entry are
 * unchanged.
 */
export function DailyBriefPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [status, setStatus] = useState<DailyBriefStatus>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/daily-brief", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DailyBriefView>;
      })
      .then((brief) => setStatus({ kind: "loaded", brief }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("dailyBrief.title")}</Heading>

        <Divider />

        {/* Summary -- one sentence, sourced solely from the backend's
            own entry count. No severity language, no invented framing. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            {status.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {status.kind === "error" && <Text color="secondary">{status.message}</Text>}
            {status.kind === "loaded" && <Text>{status.brief.summary}</Text>}
          </Stack>
        </Surface>

        {status.kind === "loaded" && status.brief.entries.length > 0 && (
          <>
            <Divider />
            <Stack gap="inter-section">
              {status.brief.entries.map((entry) => (
                <Surface tier="primary" key={entry.caseId}>
                  <Stack gap="intra-section">
                    <Heading level={2}>{entry.ticker ?? t("dailyBrief.entry.unknownCompany")}</Heading>
                    <Text as="p">{entry.headline}</Text>
                    {entry.changeSummary.split("\n").map((line, index) => (
                      <Text as="p" color="secondary" key={index}>
                        {line}
                      </Text>
                    ))}
                    <Text as="p" color="tertiary">
                      {entry.whyItMatters}
                    </Text>
                    <Button
                      variant="tertiary"
                      onClick={() =>
                        navigate(`/investment-case/${entry.caseId}`, { state: { origin: "daily-brief" } })
                      }
                    >
                      {t("dailyBrief.entry.openInvestmentCase")}
                    </Button>
                  </Stack>
                </Surface>
              ))}
            </Stack>
          </>
        )}
      </Stack>
    </Container>
  );
}
