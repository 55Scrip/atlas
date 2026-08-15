/**
 * Sprint 23 (Security Identity Evidence): a thin typed client over the
 * new `POST .../verify` and `GET .../verification` endpoints layered
 * on top of Sprint 20/22's own confirmation lifecycle. Verification is
 * always an explicit action -- nothing here is ever called
 * automatically by the confirmation flow in `securityConfirmationApi`.
 *
 * `fetchSecurityVerification` treats a 404 as "no verification attempt
 * recorded yet" (returns `null`), the same not-found-is-not-an-error
 * convention `fetchSecurityConfirmation` already established.
 */

export type SecurityVerificationStatus =
  | "verified"
  | "not_verified"
  | "provider_unavailable"
  | "ambiguous"
  | "unsupported";

export interface SecurityIdentityEvidenceView {
  id: string;
  confirmationId: string;
  provider: string;
  status: SecurityVerificationStatus;
  providerIdentifier: string | null;
  verifiedTicker: string | null;
  verifiedName: string | null;
  exchange: string | null;
  verifiedAt: string;
}

export async function fetchSecurityVerification(
  decisionId: string,
  signal?: AbortSignal,
): Promise<SecurityIdentityEvidenceView | null> {
  const response = await fetch(`/api/decisions/${decisionId}/security-confirmation/verification`, {
    signal: signal ?? null,
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as SecurityIdentityEvidenceView;
}

export async function verifySecuritySelection(decisionId: string): Promise<SecurityIdentityEvidenceView> {
  const response = await fetch(`/api/decisions/${decisionId}/security-confirmation/verify`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as SecurityIdentityEvidenceView;
}
