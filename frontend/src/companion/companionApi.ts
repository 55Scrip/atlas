/**
 * Thin typed client for the existing `POST /api/discovery/chat` endpoint
 * (`atlas/ai/api/router.py` / `atlas/ai/api/schemas.py`). Companion is the
 * first frontend consumer since Discovery's own embedded chat UI was
 * removed -- the endpoint, its system prompt, and its one supported tool
 * were deliberately left untouched for this purpose. This module adds no
 * logic of its own beyond the wire-format mapping (camelCase, via the
 * backend's own `CamelModel`); every field name below mirrors
 * `DiscoveryChatRequest`/`DiscoveryChatResponse` exactly.
 */

export type CompanionRole = "user" | "atlas";

export interface CompanionChatMessage {
  role: CompanionRole;
  content: string;
}

export type CompanionOutcome = "opened" | "created" | "unresolved" | "failed";

export interface CompanionToolResult {
  tool: "create_or_open_investment_case";
  outcome: CompanionOutcome;
  ticker: string;
  caseId: string | null;
}

export type CompanionChatMode = "generated" | "not_configured" | "provider_error" | "tool_call";

export interface CompanionChatResult {
  message: string | null;
  mode: CompanionChatMode;
  toolResult: CompanionToolResult | null;
}

export async function sendCompanionChat(
  messages: CompanionChatMessage[],
  language: "sv" | "en",
  caseId: string | null,
): Promise<CompanionChatResult> {
  const response = await fetch("/api/discovery/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      language,
      caseId: caseId ?? undefined,
    }),
  });
  if (!response.ok) {
    throw new Error(`Backend responded with ${response.status}`);
  }
  return (await response.json()) as CompanionChatResult;
}
