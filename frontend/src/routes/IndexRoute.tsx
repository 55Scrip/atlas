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
 * right destination: `/welcome` if not, `/portfolio` if so. Replaces
 * `PlatformStatusPage` at `/` — that bootstrap smoke test was never a
 * product screen and now lives at `/platform-status`.
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

  return <Navigate to={status.exists ? "/portfolio" : "/welcome"} replace />;
}
