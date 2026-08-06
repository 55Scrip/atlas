import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { Text } from "../foundation";
import { useTranslation } from "../i18n";

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
  const [status, setStatus] = useState<Status>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<{ exists: boolean }>;
      })
      .then((body) => setStatus({ kind: "resolved", exists: body.exists }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });

    return () => controller.abort();
  }, []);

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
