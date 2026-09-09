import { Navigate } from "react-router-dom";
import { Text } from "../foundation";
import { useTranslation } from "../i18n";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";

type Status =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "resolved"; exists: boolean };

/**
 * First-run router (Alpha Sprint 1A). Determines whether an Alpha
 * portfolio has already been established and sends the investor to the
 * right destination: `/welcome` if not, Daily Brief if so. Replaces
 * `PlatformStatusPage` at `/` — that bootstrap smoke test was never a
 * product screen and now lives at `/platform-status`.
 *
 * Final Pre-Alpha Convergence: an established portfolio now opens Daily
 * Brief, not Portfolio. Daily Brief is the start surface — it answers
 * "what deserves my attention today," which is the question someone
 * opening Atlas is actually asking. Portfolio answers "what is the
 * current state of what I own," which is where they go next, and it
 * stays one click away in primary navigation. The first-run branch is
 * unchanged: with no portfolio there is nothing to brief on, so
 * `/welcome` still comes first.
 */
export function IndexRoute() {
  const { t } = useTranslation();
  const portfolioResource = useAlphaPortfolio();
  const status: Status =
    portfolioResource.kind === "loaded"
      ? { kind: "resolved", exists: (portfolioResource.data as { exists: boolean }).exists }
      : portfolioResource;

  if (status.kind === "loading") {
    return (
      <Text role="status" aria-live="polite">
        {t("common.loading")}
      </Text>
    );
  }

  if (status.kind === "error") {
    return (
      <Text color="tertiary" role="alert">
        {t("indexRoute.error", { message: status.message })}
      </Text>
    );
  }

  return <Navigate to={status.exists ? "/daily-brief" : "/welcome"} replace />;
}
