import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";

interface HoldingLite {
  ticker: string;
  caseId: string | null;
}

interface PortfolioView {
  exists: boolean;
  holdings: HoldingLite[];
}

type PortfolioStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; view: PortfolioView };

interface ConversationMessage {
  id: string;
  role: "user" | "atlas";
  text: string;
}

const SUGGESTED_PROMPT_KEYS: TranslationKey[] = [
  "discovery.suggestions.aiStocks",
  "discovery.suggestions.compare",
  "discovery.suggestions.strengthenPortfolio",
  "discovery.suggestions.reviewIdea",
  "discovery.suggestions.marketTrend",
];

type ReviewCompanyStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "not-in-portfolio"; ticker: string }
  | { kind: "error"; message: string };

let nextMessageId = 0;

/**
 * Discovery v1 (Implementation Sprint 1) — a truthful Alpha shell for
 * "what would you like to explore," not a screener and not a
 * conversational AI. Confirmed by direct repository investigation
 * before writing this file: no real candidate-generation service is
 * reachable via any mounted API route (`atlas/capabilities/discovery/`
 * is CLI-only and only re-merges data the caller already assembled —
 * it does no market screening), and no conversational AI backend
 * exists anywhere in this app (`atlas/ai/interfaces.py`'s
 * `DiscoveryService` is an unimplemented `Protocol` stub). This page
 * therefore never fabricates a reply to what the investor asks — every
 * submitted question gets the same honest, bounded acknowledgment, and
 * every fact this page states (portfolio existing, a ticker being a
 * real holding, a Case already being linked) is read from the same
 * `/api/alpha-portfolio` and `/api/cases` endpoints every other page
 * already uses. No new backend behavior, no new Core object — the
 * conversation itself lives only in this component's own React state
 * for the current session, per this sprint's explicit "in-memory is
 * acceptable" allowance.
 */
export function DiscoveryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatus>({ kind: "loading" });
  const [showInfo, setShowInfo] = useState(false);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [reviewTicker, setReviewTicker] = useState("");
  const [reviewStatus, setReviewStatus] = useState<ReviewCompanyStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioView>;
      })
      .then((view) => setPortfolioStatus({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  function submitQuestion(text: string) {
    const trimmed = text.trim();
    if (trimmed === "") return;
    const userMessage: ConversationMessage = {
      id: `msg-${nextMessageId++}`,
      role: "user",
      text: trimmed,
    };
    const atlasReply: ConversationMessage = {
      id: `msg-${nextMessageId++}`,
      role: "atlas",
      text: t("discovery.response.bounded"),
    };
    setMessages((current) => [...current, userMessage, atlasReply]);
    setInputValue("");
  }

  function submitReviewCompany() {
    const ticker = reviewTicker.trim();
    if (ticker === "" || portfolioStatus.kind !== "loaded") return;

    const holding = portfolioStatus.view.holdings.find(
      (h) => h.ticker.toLowerCase() === ticker.toLowerCase(),
    );

    if (!holding) {
      setReviewStatus({ kind: "not-in-portfolio", ticker });
      return;
    }

    if (holding.caseId) {
      navigate(`/investment-case/${holding.caseId}`, { state: { origin: "discovery" } });
      return;
    }

    setReviewStatus({ kind: "submitting" });
    fetch("/api/cases", { method: "POST" })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<{ caseId: string }>;
      })
      .then((created) =>
        fetch(`/api/alpha-portfolio/holdings/${encodeURIComponent(holding.ticker)}/case-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidateCaseId: created.caseId }),
        }).then((linkResponse) => {
          if (!linkResponse.ok) throw new Error(`Backend responded with ${linkResponse.status}`);
          return linkResponse.json() as Promise<{ caseId: string }>;
        }),
      )
      .then((linked) => {
        navigate(`/investment-case/${linked.caseId}`, { state: { origin: "discovery" } });
      })
      .catch((error: unknown) => {
        setReviewStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  const reviewButtonLabel =
    portfolioStatus.kind === "loaded" &&
    portfolioStatus.view.holdings.some(
      (h) => h.ticker.toLowerCase() === reviewTicker.trim().toLowerCase() && h.caseId,
    )
      ? t("discovery.reviewCompany.openCase")
      : t("discovery.reviewCompany.createCase");

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("discovery.title")}</Heading>

        <Divider />

        {/* Primary prompt — the page's one dominant element. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <div>
              <Heading level={2}>{t("discovery.prompt.heading")}</Heading>{" "}
              <Button
                variant="tertiary"
                aria-label={t("discovery.info.ariaLabel")}
                aria-expanded={showInfo}
                onClick={() => setShowInfo((current) => !current)}
              >
                (i)
              </Button>
            </div>
            <Text color="secondary">{t("discovery.prompt.supporting")}</Text>

            {showInfo && (
              <Stack gap="inter-section">
                <Text color="secondary">{t("discovery.info.body")}</Text>
                {/* No Discovery FAQ exists yet — rendered as inert text,
                    matching the app's established "explicitly deferred"
                    pattern, never a link to a page that doesn't exist. */}
                <Text color="tertiary">{t("discovery.info.learnMore")}</Text>
              </Stack>
            )}

            {portfolioStatus.kind === "loaded" && portfolioStatus.view.exists && (
              <Text color="tertiary">{t("discovery.portfolioContext.available")}</Text>
            )}

            <Divider tone="hairline" />

            {messages.length > 0 && (
              <Stack gap="inter-section">
                {messages.map((message) => (
                  <Text key={message.id} color={message.role === "atlas" ? "secondary" : "primary"}>
                    {message.text}
                  </Text>
                ))}
              </Stack>
            )}

            <Text as="label">
              <textarea
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                placeholder={t("discovery.input.placeholder")}
                rows={3}
                style={{ width: "100%" }}
              />
            </Text>
            <div>
              <Button variant="primary" onClick={() => submitQuestion(inputValue)}>
                {t("discovery.input.submit")}
              </Button>
            </div>

            <div>
              {SUGGESTED_PROMPT_KEYS.map((key) => (
                <Button key={key} variant="tertiary" onClick={() => setInputValue(t(key))}>
                  {t(key)}
                </Button>
              ))}
            </div>
          </Stack>
        </Surface>

        <Divider />

        {/* Review a company — the only bounded, non-conversational path
            to a real Investment Case from this page. No entity
            recognition: the ticker is matched by exact, case-insensitive
            string equality against the investor's own real holdings,
            never parsed out of the conversation above. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("discovery.reviewCompany.heading")}</Heading>
            <Text as="label">
              {t("form.ticker")}
              <br />
              <input
                value={reviewTicker}
                onChange={(event) => {
                  setReviewTicker(event.target.value);
                  setReviewStatus({ kind: "idle" });
                }}
              />
            </Text>
            {reviewStatus.kind === "not-in-portfolio" && (
              <Stack gap="inter-section">
                <Text color="tertiary">
                  {t("discovery.reviewCompany.notInPortfolio", { ticker: reviewStatus.ticker })}
                </Text>
                <RouterLink to="/portfolio">{t("dashboard.portfolioStatus.goToPortfolio")}</RouterLink>
              </Stack>
            )}
            {reviewStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("discovery.reviewCompany.error", { message: reviewStatus.message })}
              </Text>
            )}
            <div>
              <Button
                variant="tertiary"
                onClick={submitReviewCompany}
                disabled={reviewStatus.kind === "submitting" || reviewTicker.trim() === ""}
              >
                {reviewStatus.kind === "submitting" ? t("common.submitting") : reviewButtonLabel}
              </Button>
            </div>
          </Stack>
        </Surface>

        <Divider />

        {/* Opportunities — no candidate generator exists in this Alpha;
            an honest, calm disclosure rather than a fabricated list or
            a silently missing section. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("discovery.opportunities.heading")}</Heading>
            <Text color="secondary">{t("discovery.opportunities.notYet")}</Text>
          </Stack>
        </Surface>
      </Stack>
    </Container>
  );
}
