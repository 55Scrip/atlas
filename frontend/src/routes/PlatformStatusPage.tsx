import { useEffect, useState } from "react";

interface CaseResponse {
  caseId: string;
  recordedAt: string;
}

type Status =
  | { kind: "loading" }
  | { kind: "success"; data: CaseResponse }
  | { kind: "error"; message: string };

/**
 * Platform bootstrap proof (Sprint 1, Commit 1): confirms the full stack —
 * Browser -> Frontend -> API -> atlas/core -> SQLite -> Response -> Browser
 * — is wired and working. Not a product screen.
 */
export function PlatformStatusPage() {
  const [status, setStatus] = useState<Status>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/cases", { method: "POST", signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<CaseResponse>;
      })
      .then((data) => setStatus({ kind: "success", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, []);

  return (
    <div>
      <h1>Atlas Platform Bootstrap</h1>
      <p>Browser → Frontend → API → atlas/core → SQLite → Response → Browser</p>
      {status.kind === "loading" && <p>Calling atlas/core...</p>}
      {status.kind === "error" && <p>Error: {status.message}</p>}
      {status.kind === "success" && (
        <dl>
          <dt>Case ID</dt>
          <dd>{status.data.caseId}</dd>
          <dt>Recorded At</dt>
          <dd>{status.data.recordedAt}</dd>
        </dl>
      )}
    </div>
  );
}
