import {
  KNOWLEDGE_DOMAIN_GROUP_KEY,
  KNOWLEDGE_DOMAIN_KEY,
  MISSING_KNOWLEDGE_REASON_KEY,
  type KnowledgeDomain,
  type KnowledgeDomainGroup,
  type MissingKnowledgeReason,
} from "../status/statusTone";
import type { Translate } from "../changeIntelligence/describeChange";

export function knowledgeDomainLabel(domain: KnowledgeDomain, t: Translate): string {
  return t(KNOWLEDGE_DOMAIN_KEY[domain]);
}

export function knowledgeDomainGroupLabel(group: KnowledgeDomainGroup, t: Translate): string {
  return t(KNOWLEDGE_DOMAIN_GROUP_KEY[group]);
}

export function missingKnowledgeReasonSentence(reason: MissingKnowledgeReason, t: Translate): string {
  return t(MISSING_KNOWLEDGE_REASON_KEY[reason]);
}
