import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Inline, Label, Link, Stack, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";

const ACCENT_LINK_STYLE = { color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" } as const;

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

/** Visual Fidelity Pass -- "What Atlas Found" / "Watchlist Updates"
 * reuse the exact same real `/api/daily-brief` Change Intelligence
 * entries Daily Brief already renders (fetched independently, the
 * same "each page fetches the same real endpoint for itself" pattern
 * Portfolio/Daily Brief already use with `/api/alpha-portfolio*`) --
 * never a second, Discovery-specific computation of the same fact.
 * `MAX_FOUND_ENTRIES` is a display cap only, matching the approved
 * screen's own five-item list. */
interface DailyBriefEntryLite {
  caseId: string;
  ticker: string | null;
  headline: string;
  changeSummary: string;
}
interface DailyBriefViewLite {
  entries: DailyBriefEntryLite[];
}
type DailyBriefFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; brief: DailyBriefViewLite };

interface WatchlistEntryLite {
  ticker: string;
  caseId: string;
}
type WatchlistFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryLite[] };

const MAX_FOUND_ENTRIES = 5;

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

type SendStatus = { kind: "idle" } | { kind: "sending" } | { kind: "unavailable" };

/**
 * Discovery Intelligence v1 — the first real conversational layer.
 * `submitQuestion` now calls the real `POST /api/discovery/chat`
 * endpoint (`atlas/ai/api/router.py`), sending the full current
 * session so follow-up questions carry context, and the investor's own
 * selected UI language so Atlas replies in it. The backend itself
 * degrades cleanly with no live provider configured — its response
 * `mode` (`"generated" | "not_configured" | "provider_error"`) is what
 * this page renders, never a client-side fabrication:
 * `"not_configured"`/`"provider_error"` are rendered as an honest Atlas
 * transcript message (still true, still calm, just not model-written);
 * a genuine network failure (`"unavailable"`) is a distinct, small
 * inline notice, never added to the transcript as something Atlas
 * supposedly said. No new Core object, no direct frontend-to-provider
 * call — this page only ever talks to Atlas's own API.
 */
export function DiscoveryPage() {
  const { t, language } = useTranslation();
  const navigate = useNavigate();

  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatus>({ kind: "loading" });
  const [dailyBrief, setDailyBrief] = useState<DailyBriefFetchStatus>({ kind: "loading" });
  const [watchlist, setWatchlist] = useState<WatchlistFetchStatus>({ kind: "loading" });
  const [showInfo, setShowInfo] = useState(false);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [sendStatus, setSendStatus] = useState<SendStatus>({ kind: "idle" });
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

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/daily-brief", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DailyBriefViewLite>;
      })
      .then((brief) => setDailyBrief({ kind: "loaded", brief }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDailyBrief({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-watchlist", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<WatchlistEntryLite[]>;
      })
      .then((entries) => setWatchlist({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setWatchlist({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  function openInvestmentCase(caseId: string) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "discovery" } });
  }

  function submitQuestion(text: string) {
    const trimmed = text.trim();
    if (trimmed === "" || sendStatus.kind === "sending") return;

    const userMessage: ConversationMessage = {
      id: `msg-${nextMessageId++}`,
      role: "user",
      text: trimmed,
    };
    const sessionSoFar = [...messages, userMessage];
    setMessages(sessionSoFar);
    setInputValue("");
    setSendStatus({ kind: "sending" });

    fetch("/api/discovery/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: sessionSoFar.map((message) => ({ role: message.role, content: message.text })),
        language,
      }),
    })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<{
          message: string | null;
          mode: "generated" | "not_configured" | "provider_error" | "tool_call";
          toolResult: {
            tool: "create_or_open_investment_case";
            outcome: "opened" | "created" | "unresolved" | "failed";
            ticker: string;
            caseId: string | null;
          } | null;
        }>;
      })
      .then((body) => {
        if (body.mode === "tool_call" && body.toolResult) {
          const { outcome, ticker, caseId } = body.toolResult;
          // The rendered text is always Atlas's own deterministic,
          // translated copy driven by the real backend outcome — never
          // anything the model wrote — so a claim of success can never
          // appear here unless the tool actually succeeded.
          const replyText =
            outcome === "opened"
              ? t("discovery.tool.caseOpened", { ticker })
              : outcome === "created"
                ? t("discovery.tool.caseCreated", { ticker })
                : outcome === "unresolved"
                  ? t("discovery.tool.tickerUnresolved", { ticker })
                  : t("discovery.tool.caseFailed", { ticker });
          setMessages((current) => [
            ...current,
            { id: `msg-${nextMessageId++}`, role: "atlas", text: replyText },
          ]);
          setSendStatus({ kind: "idle" });
          if ((outcome === "opened" || outcome === "created") && caseId) {
            navigate(`/investment-case/${caseId}`, { state: { origin: "discovery" } });
          }
          return;
        }

        const replyText =
          body.mode === "generated" && body.message
            ? body.message
            : body.mode === "provider_error"
              ? t("discovery.response.providerError")
              : t("discovery.response.bounded");
        setMessages((current) => [
          ...current,
          { id: `msg-${nextMessageId++}`, role: "atlas", text: replyText },
        ]);
        setSendStatus({ kind: "idle" });
      })
      .catch(() => {
        setSendStatus({ kind: "unavailable" });
      });
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

  // Visual Fidelity Pass -- "What Atlas Found" / "Watchlist Updates"
  // classify the same real `/api/daily-brief` entries Daily Brief
  // already renders, using the exact same Portfolio-takes-precedence
  // dedup rule Daily Brief's own module doc already establishes.
  const portfolioCaseIds = new Set(
    portfolioStatus.kind === "loaded"
      ? portfolioStatus.view.holdings.flatMap((holding) => (holding.caseId ? [holding.caseId] : []))
      : [],
  );
  const watchlistCaseIds = new Set(watchlist.kind === "loaded" ? watchlist.entries.map((entry) => entry.caseId) : []);
  const briefEntries = dailyBrief.kind === "loaded" ? dailyBrief.brief.entries : [];
  const foundEntries = briefEntries.slice(0, MAX_FOUND_ENTRIES);
  const watchlistEntries = briefEntries.filter(
    (entry) => !portfolioCaseIds.has(entry.caseId) && watchlistCaseIds.has(entry.caseId),
  );

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Text color="secondary">{t("discovery.workingOnBehalf")}</Text>

        <Divider tone="hairline" />

        {/* What Atlas Found -- real Change Intelligence entries, the
            same data Daily Brief already surfaces (see derivation
            above). Never a Discovery-specific recomputation. */}
        <Stack gap="metadata">
          <Label>{t("discovery.whatFound.heading")}</Label>
          {dailyBrief.kind === "loaded" && foundEntries.length === 0 && (
            <Text color="tertiary">{t("discovery.whatFound.empty")}</Text>
          )}
          {foundEntries.map((entry) => (
            <DiscoveryFoundRow key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
          ))}
        </Stack>

        <Divider tone="hairline" />

        {/* Watchlist Updates -- same entries, Watchlist-only slice. */}
        <Stack gap="metadata">
          <Label>{t("discovery.watchlistUpdates.heading")}</Label>
          {dailyBrief.kind === "loaded" && watchlist.kind === "loaded" && watchlistEntries.length === 0 && (
            <Text color="tertiary">{t("discovery.watchlistUpdates.empty")}</Text>
          )}
          {watchlistEntries.map((entry) => (
            <DiscoveryFoundRow key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
          ))}
        </Stack>

        <Divider tone="hairline" />

        {/* Ask Atlas -- Discovery's own real conversational feature
            (`POST /api/discovery/chat`), distinct from the deprecated
            page-local "Discuss with Atlas" placeholder boxes removed
            from Portfolio/Investment Case (Migration Review Decision
            Log #2): this is the page's actual purpose, not a duplicate
            embedded panel, so it stays -- restyled flat and dense like
            the rest of this pass, behavior unchanged. */}
        <Stack gap="metadata">
          <Inline gap="row" align="baseline">
            <Text as="p" style={{ fontWeight: 700, fontSize: "var(--type-size-h4)" }}>
              {t("discovery.prompt.heading")}
            </Text>
            <Button
              variant="tertiary"
              aria-label={t("discovery.info.ariaLabel")}
              aria-expanded={showInfo}
              onClick={() => setShowInfo((current) => !current)}
            >
              (i)
            </Button>
          </Inline>

          {showInfo && (
            <Stack gap="metadata">
              <Text color="secondary">{t("discovery.info.body")}</Text>
              <Text color="tertiary">{t("discovery.info.learnMore")}</Text>
            </Stack>
          )}

          {portfolioStatus.kind === "loaded" && portfolioStatus.view.exists && (
            <Text color="tertiary">{t("discovery.portfolioContext.available")}</Text>
          )}

          {messages.length > 0 && (
            <Stack gap="metadata">
              {messages.map((message) => (
                <Text key={message.id} color={message.role === "atlas" ? "secondary" : "primary"} as="p">
                  {message.text}
                </Text>
              ))}
            </Stack>
          )}

          {sendStatus.kind === "sending" && (
            <Text color="tertiary" role="status" aria-live="polite">
              {t("discovery.chat.sending")}
            </Text>
          )}
          {sendStatus.kind === "unavailable" && (
            <Text color="tertiary" role="alert">
              {t("discovery.chat.unavailable")}
            </Text>
          )}

          <Inline gap="row" align="center">
            <input
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submitQuestion(inputValue);
                }
              }}
              placeholder={t("discovery.input.placeholder")}
              style={{ flex: "1 1 auto" }}
              disabled={sendStatus.kind === "sending"}
            />
            <Button
              variant="primary"
              aria-label={t("discovery.input.submit")}
              onClick={() => submitQuestion(inputValue)}
              disabled={sendStatus.kind === "sending" || inputValue.trim() === ""}
            >
              {sendStatus.kind === "sending" ? t("common.submitting") : "→"}
            </Button>
          </Inline>

          <Inline gap="metadata" wrap>
            {SUGGESTED_PROMPT_KEYS.map((key) => (
              <Button
                key={key}
                variant="tertiary"
                onClick={() => setInputValue(t(key))}
                disabled={sendStatus.kind === "sending"}
                style={{ borderRadius: "var(--radius-chip)", border: "var(--width-border-hairline) solid var(--color-border-standard)" }}
              >
                {t(key)}
              </Button>
            ))}
          </Inline>
        </Stack>

        <Divider tone="hairline" />

        {/* Review a company -- the only bounded, non-conversational path
            to a real Investment Case from this page. No entity
            recognition: the ticker is matched by exact, case-insensitive
            string equality against the investor's own real holdings,
            never parsed out of the conversation above. */}
        <Stack gap="metadata">
          <Label>{t("discovery.reviewCompany.heading")}</Label>
          <Inline gap="row" align="center">
            <input
              value={reviewTicker}
              placeholder={t("form.ticker")}
              onChange={(event) => {
                setReviewTicker(event.target.value);
                setReviewStatus({ kind: "idle" });
              }}
            />
            <Button
              variant="tertiary"
              onClick={submitReviewCompany}
              disabled={reviewStatus.kind === "submitting" || reviewTicker.trim() === ""}
            >
              {reviewStatus.kind === "submitting" ? t("common.submitting") : reviewButtonLabel}
            </Button>
          </Inline>
          {reviewStatus.kind === "not-in-portfolio" && (
            <Inline gap="row" align="baseline">
              <Text color="tertiary">
                {t("discovery.reviewCompany.notInPortfolio", { ticker: reviewStatus.ticker })}
              </Text>
              <Link
                href="#"
                style={ACCENT_LINK_STYLE}
                onClick={(event) => {
                  event.preventDefault();
                  navigate("/portfolio");
                }}
              >
                {t("dashboard.portfolioStatus.goToPortfolio")}
              </Link>
            </Inline>
          )}
          {reviewStatus.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("discovery.reviewCompany.error", { message: reviewStatus.message })}
            </Text>
          )}
        </Stack>
      </Stack>
    </Container>
  );
}

/** Visual Fidelity Pass -- one dense row per real Change Intelligence
 * entry (ticker + first change line + arrow), shared by "What Atlas
 * Found" and "Watchlist Updates". */
function DiscoveryFoundRow({
  entry,
  onOpen,
  t,
}: {
  entry: DailyBriefEntryLite;
  onOpen: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const firstChangeLine = entry.changeSummary.split("\n")[0] ?? entry.headline;
  return (
    <Link
      href="#"
      style={{ ...ACCENT_LINK_STYLE, color: "var(--color-text-primary)", display: "block" }}
      onClick={(event) => {
        event.preventDefault();
        onOpen();
      }}
    >
      <Inline gap="row" align="baseline" style={{ justifyContent: "space-between" }}>
        <Text as="span">
          <Text as="span" color="secondary">
            {entry.ticker ?? t("dailyBrief.entry.unknownCompany")} —{" "}
          </Text>
          {firstChangeLine}
        </Text>
        <Text as="span" color="tertiary">
          →
        </Text>
      </Inline>
    </Link>
  );
}
