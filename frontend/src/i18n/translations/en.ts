/**
 * Canonical English translation dictionary. Every other language's
 * dictionary is typed against this one's key set (`TranslationKey`), so a
 * missing or extra key fails the build — see `sv.ts`.
 *
 * Keys are namespaced by screen/section (`welcome.*`, `portfolio.*`,
 * `investmentCase.evidence.*`, ...) with a `common.*` and `form.*`
 * namespace for strings repeated verbatim across screens (button labels,
 * field labels). This is presentation-layer copy only — see
 * `atlas/alpha/portfolio/models.py` and friends for the internal,
 * English-only domain vocabulary this deliberately does not touch.
 *
 * Interpolation: a value may contain `{{name}}` placeholders, filled in
 * by `t(key, { name: value })`.
 */
export const en = {
  // ---------- common ----------
  "common.loading": "Loading…",
  "common.saving": "Saving…",
  "common.submit": "Submit",
  "common.submitting": "Submitting…",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.deleting": "Deleting…",
  "common.addAnother": "Add another",
  "common.unknownError": "Unknown error",
  "common.invalidInput": "Invalid input.",

  // ---------- shared form field labels ----------
  "form.ticker": "Ticker",
  "form.weightPercent": "Weight %",
  "form.valueOptional": "Value (optional)",
  "form.cashPercent": "Cash %",
  "form.cashValueOptional": "Cash value (optional)",
  "form.preferencesOptional": "Preferences (optional)",
  "form.removeButton": "Remove",

  // ---------- application shell ----------
  "shell.header.brand": "Atlas",
  "shell.header.languageAriaLabel": "Choose language",
  "shell.nav.ariaLabel": "Primary",
  "shell.nav.dashboard": "Dashboard",
  "shell.nav.portfolio": "Portfolio",
  "shell.notFound.title": "Page not found",
  "shell.notFound.body": "There is no route at this address.",
  "shell.error.title": "Something went wrong",

  // ---------- index route ----------
  "indexRoute.error": "Could not reach Atlas: {{message}}",

  // ---------- welcome ----------
  "welcome.title": "Welcome to Atlas",
  "welcome.choice.prompt": "How would you like to begin?",
  "welcome.choice.haveExisting": "I have an existing portfolio",
  "welcome.choice.startFromScratch": "Start from scratch",
  "welcome.continueButton": "Continue to Portfolio",
  "welcome.backButton": "Back",
  "welcome.import.heading": "Your existing portfolio",
  "welcome.import.instructions":
    "Enter each holding as a percentage of your portfolio. Exact values are optional.",
  "welcome.import.addHoldingButton": "+ Add holding",
  "welcome.import.errors.noHoldings": "Enter at least one holding.",
  "welcome.import.errors.missingPercentage": "Every holding needs a percentage.",
  "welcome.import.errors.invalidValueFor": '"{{value}}" is not a valid value for {{ticker}}.',
  "welcome.import.errors.duplicateTickers": "Duplicate ticker(s): {{tickers}}.",
  "welcome.import.errors.invalidCashPercent": '"{{value}}" is not a valid cash percentage.',
  "welcome.import.errors.invalidCashValue": '"{{value}}" is not a valid cash value.',
  "welcome.import.errors.cashBothOrNeither":
    "Enter both cash % and cash value, or leave both blank.",
  "welcome.import.errors.saveFailed": "Could not save this portfolio: {{message}}",
  "welcome.scratch.heading": "Starting from scratch",
  "welcome.scratch.objectiveLabel": "Investment objective",
  "welcome.scratch.horizonLabel": "Investment horizon",
  "welcome.scratch.errors.required": "Objective and horizon are both required.",
  "welcome.scratch.errors.saveFailed": "Could not save: {{message}}",

  // ---------- portfolio ----------
  "portfolio.title": "Portfolio",
  "portfolio.loadError": "Could not load your portfolio: {{message}}",
  "portfolio.notEstablished": "No portfolio has been established yet.",
  "portfolio.setupLink": "Set up your portfolio",
  "portfolio.empty.title": "Your portfolio is empty.",
  "portfolio.empty.objective": "Objective: {{value}}",
  "portfolio.empty.horizon": "Horizon: {{value}}",
  "portfolio.empty.explanation":
    "There is nothing to show here yet — Atlas does not fabricate holdings or opportunities. As you open Investment Cases and record decisions, they will appear here.",
  "portfolio.openNewCase": "Open a new Investment Case",
  "portfolio.awaitingBanner.title": "Trade recorded. Allocation requires reconciliation.",
  "portfolio.awaitingBanner.body":
    "One or more holdings were traded while Atlas only knew percentages, so their allocation was left untouched rather than invented. Update the affected holding below, or replace the entire allocation.",
  "portfolio.replaceAllocationButton": "Replace entire allocation",
  "portfolio.replaceForm.heading": "Replace entire allocation",
  "portfolio.replaceForm.saveButton": "Save allocation",
  "portfolio.replaceForm.errors.invalidPercentage": "Every holding needs a valid percentage.",
  "portfolio.holdings.heading": "Holdings",
  "portfolio.holdings.percentOnly":
    "Showing percentages only — no absolute portfolio value was entered.",
  "portfolio.holdings.totalValue": "Total value: {{value}}",
  "portfolio.holdings.updatedAutomatically": "Updated automatically",
  "portfolio.holdings.awaitingReconciliation": "Awaiting reconciliation",
  "portfolio.holdings.newWeightLabel": "New weight %",
  "portfolio.holdings.updateButton": "Update this holding",
  "portfolio.holdings.updating": "Updating…",
  "portfolio.holdings.openCaseButton": "Open Investment Case",
  "portfolio.holdings.opening": "Opening…",
  "portfolio.holdings.openCaseError": "Could not open an Investment Case.",
  "portfolio.holdings.errors.invalidPercentage": "Enter a valid percentage.",
  // ---------- portfolio cockpit (ATLAS-028) ----------
  "portfolio.cockpit.conviction.label": "Conviction",
  "portfolio.cockpit.conviction.very_high": "Very high",
  "portfolio.cockpit.conviction.high": "High",
  "portfolio.cockpit.conviction.moderate": "Moderate",
  "portfolio.cockpit.conviction.low": "Low",
  "portfolio.cockpit.conviction.insufficient_evidence": "Insufficient evidence",
  "portfolio.cockpit.valuation.label": "Valuation",
  "portfolio.cockpit.valuation.not_evaluated": "Not evaluated",
  "portfolio.cockpit.valuation.insufficient_input": "Insufficient input",
  "portfolio.cockpit.valuation.undervalued": "Undervalued",
  "portfolio.cockpit.valuation.fairly_valued": "Fairly valued",
  "portfolio.cockpit.valuation.expensive": "Expensive",
  "portfolio.cockpit.risk.label": "Risk",
  "portfolio.cockpit.risk.status.not_evaluated": "Not evaluated",
  "portfolio.cockpit.risk.status.insufficient_input": "Insufficient input",
  "portfolio.cockpit.risk.status.low": "Low",
  "portfolio.cockpit.risk.status.moderate": "Moderate",
  "portfolio.cockpit.risk.status.high": "High",
  "portfolio.cockpit.risk.category.business_risk": "Business",
  "portfolio.cockpit.risk.category.financial_risk": "Financial",
  "portfolio.cockpit.risk.category.valuation_risk": "Valuation",
  "portfolio.cockpit.risk.category.thesis_risk": "Thesis",
  "portfolio.cockpit.business.growthLabel": "Growth",
  "portfolio.cockpit.business.capitalAllocationLabel": "Capital allocation",
  "portfolio.cockpit.business.not_evaluated": "Not evaluated",
  "portfolio.cockpit.business.insufficient_input": "Insufficient input",
  "portfolio.cockpit.business.weak": "Weak",
  "portfolio.cockpit.business.moderate": "Moderate",
  "portfolio.cockpit.business.strong": "Strong",
  "portfolio.cockpit.evidenceLabel": "Evidence",
  "portfolio.cockpit.thesisStale": "Thesis not reviewed in a long time",
  "portfolio.cockpit.review.label": "Review",
  "portfolio.cockpit.review.none": "—",
  "portfolio.cockpit.review.standard_review": "Standard review",
  "portfolio.cockpit.review.evidence_review": "Evidence review",
  "portfolio.cockpit.review.priority_review": "Priority review",
  "portfolio.cockpit.viewCaseButton": "View Investment Case",
  "portfolio.cockpit.unresolved": "Investment Case could not be resolved",

  "portfolio.cashLabel": "Cash: {{percent}}%",
  "portfolio.unallocated":
    "Unallocated: {{percent}}% — this portfolio does not yet account for 100% of holdings; Atlas does not invent the remainder.",
  "portfolio.concentration": "Concentration: {{value}}",
  "portfolio.concentrationLevel.low": "Low",
  "portfolio.concentrationLevel.moderate": "Moderate",
  "portfolio.concentrationLevel.elevated": "Elevated",
  "portfolio.concentrationLevel.high": "High",

  // ---------- portfolio intelligence (ATLAS-015) ----------
  "portfolio.summary.heading": "Portfolio Summary",
  "portfolio.summary.holdings": "Holdings",
  "portfolio.summary.largestPosition": "Largest position",
  "portfolio.summary.noLargestPosition": "—",
  "portfolio.summary.investmentCases": "Investment Cases",
  "portfolio.summary.openDecisions": "Open Decisions",
  "portfolio.summary.pendingOutcomes": "Pending Outcomes",
  "portfolio.summary.pendingExecutions": "Pending Executions",
  "portfolio.summary.concentration": "Concentration",
  "portfolio.summary.unallocated": "Unallocated",
  "portfolio.needsAttention.heading": "Needs Attention",
  "portfolio.needsAttention.empty": "Nothing needs attention right now.",
  "portfolio.needsAttention.missingCase": "{{ticker}} — no Investment Case yet",
  "portfolio.needsAttention.decisionWithoutOutcome": "{{ticker}} — a Decision has no Outcome reported",
  "portfolio.needsAttention.outcomeWithoutExecution": "{{ticker}} — an Outcome has no execution confirmed",
  "portfolio.needsAttention.awaitingReconciliation": "{{ticker}} — awaiting reconciliation after a trade",
  "portfolio.needsAttention.veryOldCase": "{{ticker}} — Investment Case is {{days}} days old",
  "portfolio.needsAttention.observationWithoutDecision": "{{ticker}} — an Observation has no Decision",
  "portfolio.reviewQueue.heading": "Review Queue",
  "portfolio.reviewQueue.empty": "Nothing queued for review.",
  "portfolio.reviewQueue.item": "Review {{ticker}}",
  "portfolio.reviewQueue.reasonCount": "{{count}} items",
  "portfolio.health.heading": "Portfolio Health",
  "portfolio.health.coverage": "{{withCase}} of {{total}} holdings have an Investment Case",
  "portfolio.health.freshness": "Most recent decision: {{date}}",
  "portfolio.health.noDecisions": "No decisions recorded yet",
  "portfolio.health.outstandingItems": "Outstanding workflow items",
  "portfolio.health.completeness": "Portfolio completeness",
  "portfolio.health.unknownInstruments": "Unknown instruments",
  "portfolio.health.noUnknownInstruments": "None detected",

  // ---------- portfolio intelligence (ATLAS-016) ----------
  "portfolio.intelligence.confidence.not_applicable": "Insufficient evidence",
  "portfolio.intelligence.confidence.none": "No evidence recorded",
  "portfolio.intelligence.confidence.partial": "Partial evidence",
  "portfolio.intelligence.confidence.full": "Full evidence coverage",

  "portfolio.intelligence.keyFindings.heading": "Key Findings",
  "portfolio.intelligence.keyFindings.empty": "No key findings right now.",
  "portfolio.intelligence.keyFindings.high_concentration":
    "High concentration in your largest position ({{tickers}})",
  "portfolio.intelligence.keyFindings.elevated_concentration":
    "Elevated concentration in your largest position ({{tickers}})",
  "portfolio.intelligence.keyFindings.large_unallocated": "A meaningful part of the portfolio is unallocated",
  "portfolio.intelligence.keyFindings.multiple_missing_cases":
    "{{count}} holdings have no Investment Case yet ({{tickers}})",
  "portfolio.intelligence.keyFindings.multiple_stale_cases":
    "{{count}} Investment Cases have not been reviewed in a long time ({{tickers}})",
  "portfolio.intelligence.keyFindings.multiple_evidence_gaps":
    "{{count}} holdings have evidence gaps in their Investment Case ({{tickers}})",

  "portfolio.intelligence.consider.heading": "Consider",
  "portfolio.intelligence.consider.empty": "Nothing to consider right now.",
  "portfolio.intelligence.consider.disclaimer":
    "These are review suggestions, not investment recommendations — Atlas never tells you to buy or sell.",
  "portfolio.intelligence.consider.open_investment_case.title": "Consider opening an Investment Case",
  "portfolio.intelligence.consider.open_investment_case.reason": "{{ticker}} has no Investment Case yet.",
  "portfolio.intelligence.consider.gather_evidence.title": "Consider gathering more evidence",
  "portfolio.intelligence.consider.gather_evidence.reason":
    "{{ticker}}'s Investment Case has {{count}} evidence gap(s).",
  "portfolio.intelligence.consider.review_thesis.title": "Consider reviewing the thesis",
  "portfolio.intelligence.consider.review_thesis.reason":
    "{{ticker}}'s Investment Case is {{days}} days old.",
  "portfolio.intelligence.consider.update_case.title": "Consider updating the Investment Case",
  "portfolio.intelligence.consider.update_case.reason":
    "{{ticker}} has {{count}} pending workflow item(s).",
  "portfolio.intelligence.consider.review_concentration.title": "Consider reviewing this position's size",
  "portfolio.intelligence.consider.review_concentration.reason":
    "{{ticker}} is {{weight}}% of the portfolio.",

  "portfolio.intelligence.riskSignals.heading": "Risk Signals",
  "portfolio.intelligence.riskSignals.empty": "No risk signals right now.",
  "portfolio.intelligence.riskSignals.high_concentration": "{{ticker}} — high concentration",
  "portfolio.intelligence.riskSignals.missing_case": "{{ticker}} — no Investment Case",
  "portfolio.intelligence.riskSignals.missing_evidence": "{{ticker}} — missing evidence",
  "portfolio.intelligence.riskSignals.awaiting_reconciliation": "{{ticker}} — awaiting reconciliation",
  "portfolio.intelligence.riskSignals.stale_review": "{{ticker}} — not reviewed in {{days}} days",

  "portfolio.intelligence.missingEvidence.heading": "Missing Evidence",
  "portfolio.intelligence.missingEvidence.empty": "No evidence gaps detected.",
  "portfolio.intelligence.missingEvidence.no_evidence_recorded":
    "{{ticker}} — no evidence recorded for this Investment Case",
  "portfolio.intelligence.missingEvidence.observation_without_evidence":
    "{{ticker}} — an Observation has no linked Evidence",
  "portfolio.intelligence.missingEvidence.decision_without_linked_observation":
    "{{ticker}} — a Decision has no linked Observation",

  "portfolio.intelligence.portfolioFit.heading": "Portfolio Fit",
  "portfolio.intelligence.portfolioFit.notYetAvailable": "Not yet available.",

  // ---------- dashboard ----------
  "dashboard.title": "Dashboard",
  "dashboard.portfolioStatus.heading": "Portfolio Status",
  "dashboard.portfolioStatus.loadError": "Could not load portfolio status: {{message}}",
  "dashboard.portfolioStatus.notEstablished": "No portfolio established yet.",
  "dashboard.portfolioStatus.setupCta": "Set up portfolio →",
  "dashboard.portfolioStatus.holdingSingular": "holding",
  "dashboard.portfolioStatus.holdingPlural": "holdings",
  "dashboard.portfolioStatus.summary": "{{count}} {{holdingWord}}",
  "dashboard.portfolioStatus.cashSuffix": " — {{percent}}% cash",
  "dashboard.portfolioStatus.goToPortfolio": "Go to Portfolio →",
  "dashboard.monitoring.heading": "Active Monitoring Conditions",
  "dashboard.notYetImplemented": "Not yet implemented.",
  "dashboard.recentDecisions.heading": "Recent Decisions",
  "dashboard.recentDecisions.loadError": "Could not load recent decisions: {{message}}",
  "dashboard.recentDecisions.empty": "No decisions recorded yet.",
  "dashboard.outcomes.heading": "Outcomes",
  "dashboard.outcomes.loadError": "Could not load outcomes: {{message}}",
  "dashboard.outcomes.empty": "No outcomes recorded yet.",
  "dashboard.tradeExecutions.heading": "Trade Executions",
  "dashboard.tradeExecutions.loadError": "Could not load trade executions: {{message}}",
  "dashboard.tradeExecutions.empty": "No trades recorded yet.",
  "dashboard.signals.heading": "Signals",
  "dashboard.workspaces.heading": "Workspaces",
  "dashboard.workspaces.empty": "No active Workspaces yet.",

  // ---------- investment case: shell ----------
  "investmentCase.heading": "Investment Case",
  "investmentCase.returnTo.dashboard": "← Back to Dashboard",
  "investmentCase.returnTo.history": "← Back to History",
  "investmentCase.returnTo.portfolio": "← Back to Portfolio",
  "investmentCase.returnTo.dailyBrief": "← Back to Daily Brief",
  "investmentCase.returnTo.discovery": "← Back to Discovery",
  "investmentCase.noCaseSelected": "No case selected.",
  "investmentCase.loadError": "Could not load this case: {{message}}",
  "investmentCase.subject": "Subject: Case {{caseId}}",
  "investmentCase.status.heading": "Status",
  "investmentCase.status.placeholder":
    "Reserved for draft, historical, and monitoring status indicators in a future commit.",
  "investmentCase.primaryWorkArea.heading": "Primary Work Area",
  "investmentCase.timeline.heading": "Timeline",
  "investmentCase.timeline.placeholder":
    "Reserved for this Decision's own Decision Timeline in a future commit.",
  "investmentCase.footer.heading": "Footer",

  // ---------- investment case: canonical analysis (ATLAS-029) ----------
  "investmentCase.analysis.conviction.heading": "Conviction",
  "investmentCase.analysis.conviction.reasonsHeading": "Why",
  "investmentCase.analysis.confidence.heading": "Confidence",
  "investmentCase.analysis.confidence.explanation": "How well the recorded Observations for this Case are backed by Evidence.",
  "investmentCase.analysis.thesis.heading": "Current Thesis",
  "investmentCase.analysis.thesis.investorDecisionReason": "Investor's stated reason (most recent Decision)",
  "investmentCase.analysis.thesis.investorObservation": "Investor's most recent Observation",
  "investmentCase.analysis.thesis.none": "No thesis recorded yet — no Decision or Observation has been made for this Case.",
  "investmentCase.analysis.thesis.stale": "This thesis has not been reviewed in a long time.",
  "investmentCase.analysis.business.heading": "Business Analysis",
  "investmentCase.analysis.business.category.business_model": "Business Model",
  "investmentCase.analysis.business.category.competitive_position": "Competitive Position",
  "investmentCase.analysis.business.category.management": "Management",
  "investmentCase.analysis.business.category.capital_allocation": "Capital Allocation",
  "investmentCase.analysis.business.category.growth": "Growth",
  "investmentCase.analysis.business.category.durability": "Durability",
  "investmentCase.analysis.business.supportingLabel": "Supporting",
  "investmentCase.analysis.business.contradictingLabel": "Contradicting",
  "investmentCase.analysis.business.missingLabel": "Missing",
  "investmentCase.analysis.valuation.heading": "Valuation",
  "investmentCase.analysis.valuation.method.fcf_yield_relative": "FCF Yield (Relative)",
  "investmentCase.analysis.valuation.currentYieldLabel": "Current FCF Yield",
  "investmentCase.analysis.valuation.scenarioHeading": "Scenario Analysis",
  "investmentCase.analysis.valuation.scenarioNote": "Not yet available — forward assumptions have not been supplied.",
  "investmentCase.analysis.risk.heading": "Risk",
  "investmentCase.analysis.risk.subheading": "Every category shown independently — never combined into one score.",
  "investmentCase.analysis.evidence.heading": "Evidence",
  "investmentCase.analysis.evidence.supportingCount": "{{count}} Observation(s) with supporting Evidence",
  "investmentCase.analysis.evidence.challengingCount": "{{count}} Observation(s) with challenging Evidence",
  "investmentCase.analysis.evidence.coverageLabel": "Coverage",
  "investmentCase.analysis.evidence.noneRecorded": "No Evidence recorded for this Case yet.",
  "investmentCase.analysis.recommendation.heading": "Recommendation",
  "investmentCase.analysis.recommendation.withheld": "Withheld",
  "investmentCase.analysis.recommendation.reasonLabel": "Reason",
  "investmentCase.analysis.recommendation.reason.engine_not_implemented": "The recommendation engine has not been built yet.",
  "investmentCase.analysis.recommendation.reason.evidence_insufficient": "The required evaluation coverage is not yet sufficient.",
  "investmentCase.analysis.decisionHistory.heading": "Decision History",
  "investmentCase.analysis.decisionHistory.empty": "No Decisions recorded yet.",
  "investmentCase.analysis.observations.heading": "Investor Observations",
  "investmentCase.analysis.observations.empty": "No Observations recorded yet — analysis does not require any.",
  "investmentCase.analysis.outcomes.heading": "Outcomes",
  "investmentCase.analysis.outcomes.empty": "No Outcomes recorded yet.",

  // ---------- investment case: observations ----------
  "investmentCase.observations.heading": "Observations",
  "investmentCase.observations.loading": "Loading observations…",
  "investmentCase.observations.loadError": "Could not load observations: {{message}}",
  "investmentCase.observations.empty": "No observations recorded yet.",
  "investmentCase.observations.addButton": "Add Observation",
  "investmentCase.observations.recorded": "Observation recorded: {{subject}}",
  "investmentCase.observations.subjectLabel": "Subject",
  "investmentCase.observations.statementLabel": "Statement",
  "investmentCase.observations.recordError": "Could not record this observation: {{message}}",

  // ---------- investment case: evidence ----------
  "investmentCase.evidence.heading": "Evidence",
  "investmentCase.evidence.loading": "Loading evidence…",
  "investmentCase.evidence.loadError": "Could not load evidence: {{message}}",
  "investmentCase.evidence.empty": "No evidence recorded yet.",
  "investmentCase.evidence.addButton": "+ Add Evidence",
  "investmentCase.evidence.recorded": "Evidence recorded: {{statement}}",
  "investmentCase.evidence.summaryLabel": "Summary",
  "investmentCase.evidence.sourceLabel": "Source",
  "investmentCase.evidence.directionLabel": "Direction",
  "investmentCase.evidence.directionSupports": "Supports",
  "investmentCase.evidence.directionChallenges": "Challenges",
  "investmentCase.evidence.recordError": "Could not record this evidence: {{message}}",
  "investmentCase.evidence.deleteError": "Could not delete this evidence.",

  // ---------- investment case: knowledge reference ----------
  "investmentCase.knowledgeReference.heading": "Knowledge References",
  "investmentCase.knowledgeReference.loading": "Loading knowledge references…",
  "investmentCase.knowledgeReference.loadError":
    "Could not load knowledge references: {{message}}",
  "investmentCase.knowledgeReference.empty": "No knowledge references recorded yet.",
  "investmentCase.knowledgeReference.addButton": "+ Add Knowledge Reference",
  "investmentCase.knowledgeReference.itemLabel": "Knowledge Reference {{id}}",
  "investmentCase.knowledgeReference.recorded": "Knowledge reference recorded: {{id}}",
  "investmentCase.knowledgeReference.prompt":
    "Record a Knowledge Reference for this Observation.",
  "investmentCase.knowledgeReference.recordError":
    "Could not record this knowledge reference: {{message}}",
  "investmentCase.knowledgeReference.deleteError": "Could not delete this knowledge reference.",

  // ---------- investment case: reasoning trace ----------
  "investmentCase.reasoningTrace.heading": "Reasoning Trace",
  "investmentCase.reasoningTrace.loading": "Loading reasoning trace…",
  "investmentCase.reasoningTrace.loadError": "Could not load reasoning trace: {{message}}",
  "investmentCase.reasoningTrace.empty": "No reasoning trace recorded yet.",
  "investmentCase.reasoningTrace.addButton": "+ Create Reasoning Trace",
  "investmentCase.reasoningTrace.itemLabel": "Reasoning Trace {{id}}",
  "investmentCase.reasoningTrace.recorded": "Reasoning trace recorded: {{id}}",
  "investmentCase.reasoningTrace.prompt": "Record a Reasoning Trace supported by this Observation.",
  "investmentCase.reasoningTrace.recordError":
    "Could not record this reasoning trace: {{message}}",
  "investmentCase.reasoningTrace.deleteError": "Could not delete this reasoning trace.",

  // ---------- investment case: judgment ----------
  "investmentCase.judgment.heading": "Judgment",
  "investmentCase.judgment.loading": "Loading judgment…",
  "investmentCase.judgment.loadError": "Could not load judgment: {{message}}",
  "investmentCase.judgment.empty": "No judgment recorded yet.",
  "investmentCase.judgment.addButton": "+ Create Judgment",
  "investmentCase.judgment.recorded": "Judgment recorded: {{characterization}}",
  "investmentCase.judgment.characterizationLabel": "Characterization",
  "investmentCase.judgment.recordError": "Could not record this judgment: {{message}}",
  "investmentCase.judgment.deleteError": "Could not delete this judgment.",

  // ---------- investment case: decision ----------
  "investmentCase.decision.heading": "Decision",
  "investmentCase.decision.loading": "Loading decision…",
  "investmentCase.decision.loadError": "Could not load decision: {{message}}",
  "investmentCase.decision.empty": "No decision recorded yet.",
  "investmentCase.decision.addButton": "+ Record Decision",
  "investmentCase.decision.recorded": "Decision recorded: {{decisionType}} — {{subject}}",
  "investmentCase.decision.typeLabel": "Decision Type",
  "investmentCase.decision.typeBuy": "Buy",
  "investmentCase.decision.typeSell": "Sell",
  "investmentCase.decision.typeHold": "Hold",
  "investmentCase.decision.typeWatch": "Watch",
  "investmentCase.decision.typePass": "Pass",
  "investmentCase.decision.subjectLabel": "Subject",
  "investmentCase.decision.reasonLabel": "Reason",
  "investmentCase.decision.confidenceLabel": "Confidence (0-100)",
  "investmentCase.decision.confidencePrefix": "Confidence: {{value}}",
  "investmentCase.decision.recordError": "Could not record this decision: {{message}}",

  // ---------- investment case: outcome ----------
  "investmentCase.outcome.heading": "Outcome",
  "investmentCase.outcome.loading": "Loading outcome…",
  "investmentCase.outcome.loadError": "Could not load outcome: {{message}}",
  "investmentCase.outcome.empty": "No outcome recorded yet.",
  "investmentCase.outcome.needsDecisionFirst":
    "No decision recorded yet — record a Decision first.",
  "investmentCase.outcome.addButton": "+ Record Outcome",
  "investmentCase.outcome.recorded": "Outcome recorded: {{statement}}",
  "investmentCase.outcome.updatingPortfolio": "Updating portfolio…",
  "investmentCase.outcome.updatedAutomatically": "Portfolio updated automatically.",
  "investmentCase.outcome.awaitingReconciliation":
    "Trade recorded. Allocation requires reconciliation on the Portfolio page.",
  "investmentCase.outcome.applyTradeError":
    "Outcome was recorded, but the portfolio could not be updated: {{message}}",
  "investmentCase.outcome.decisionLabel": "Decision",
  "investmentCase.outcome.decisionPlaceholder": "Select a decision…",
  "investmentCase.outcome.statementLabel": "Statement",
  "investmentCase.outcome.noteLabel": "Note (optional)",
  "investmentCase.outcome.externalTradeCheckbox":
    "This was an external trade — record the execution",
  "investmentCase.outcome.securityLabel": "Security",
  "investmentCase.outcome.typeLabel": "Type",
  "investmentCase.outcome.transactionTypeAdd": "Add",
  "investmentCase.outcome.transactionTypeExit": "Exit (removes the holding)",
  "investmentCase.outcome.quantityLabel": "Quantity",
  "investmentCase.outcome.executionPriceLabel": "Execution price",
  "investmentCase.outcome.feesLabel": "Fees (optional)",
  "investmentCase.outcome.executedAtLabel": "Executed date (optional — defaults to now)",
  "investmentCase.outcome.recordError": "Could not record this outcome: {{message}}",
  "investmentCase.outcome.validation.tradeRequiredFields":
    "Security, quantity, and execution price are required for a trade.",

  // ---------- investment case v2: header ----------
  "investmentCase.header.inPortfolio": "In your portfolio",
  "investmentCase.header.notLinked": "Not yet linked to a portfolio holding",
  "investmentCase.header.currentAllocation": "Current allocation: {{percent}}%",
  "investmentCase.header.caseIdLabel": "Case ID: {{caseId}}",
  "investmentCase.header.untitled": "Investment Case",

  // ---------- investment case v2: Atlas Assessment ----------
  "investmentCase.assessment.heading": "Atlas Assessment",
  "investmentCase.assessment.notLinkedYet":
    "This case is not yet linked to a portfolio holding. Atlas has no company or portfolio state to assess.",
  "investmentCase.assessment.noAnalysisYet":
    "Atlas has not yet completed enough analysis to recommend a portfolio change.",
  "investmentCase.assessment.heldNoAssessment":
    "This position is currently recorded in your portfolio. No Atlas-generated company assessment is available yet.",
  "investmentCase.assessment.decisionRecorded": "A decision has been recorded for this case.",
  "investmentCase.assessment.outcomeRecorded":
    "A completed external transaction has been recorded.",
  "investmentCase.assessment.explanation":
    "Atlas does not yet generate company-specific analysis (valuation, conviction, business quality). What you see below reflects only your recorded portfolio state and decision history.",

  // ---------- investment case v2: why now ----------
  "investmentCase.whyNow.heading": "Why now?",
  "investmentCase.whyNow.awaitingReconciliation": "Allocation awaiting reconciliation",
  "investmentCase.whyNow.decisionRecorded": "A decision has been recorded",
  "investmentCase.whyNow.outcomeRecorded": "An outcome has been recorded",
  "investmentCase.whyNow.none": "No specific trigger is currently available.",

  // ---------- investment case v2: key decision info cards ----------
  "investmentCase.cards.currentAllocation": "Current allocation",
  "investmentCase.cards.cashAllocation": "Cash allocation",
  "investmentCase.cards.portfolioMode": "Portfolio mode",
  "investmentCase.cards.portfolioModePercentOnly": "Percentage only",
  "investmentCase.cards.portfolioModeAbsolute": "Absolute values available",
  "investmentCase.cards.decisionStatus": "Decision status",
  "investmentCase.cards.outcomeStatus": "Outcome status",
  "investmentCase.cards.recordedValue": "Recorded",
  "investmentCase.cards.notRecordedValue": "Not yet recorded",
  "investmentCase.cards.reconciliationStatus": "Reconciliation status",
  "investmentCase.cards.lastActivity": "Last recorded activity",
  "investmentCase.cards.supportingRecords": "Supporting records",

  // ---------- investment case v2: portfolio impact ----------
  "investmentCase.portfolioImpact.heading": "Portfolio impact",
  "investmentCase.portfolioImpact.notHeld": "This company is not currently held in your portfolio.",
  "investmentCase.portfolioImpact.percentOnlyNote":
    "Portfolio impact can only be expressed in percentages — no absolute portfolio value has been entered.",
  "investmentCase.portfolioImpact.awaitingReconciliation":
    "The latest trade against this holding requires reconciliation on the Portfolio page.",

  // ---------- investment case v2: what Atlas knows ----------
  "investmentCase.whatAtlasKnows.heading": "What Atlas knows",
  "investmentCase.whatAtlasKnows.observationsCount": "Recorded observations: {{count}}",
  "investmentCase.whatAtlasKnows.supportingEvidenceCount": "Supporting evidence: {{count}}",
  "investmentCase.whatAtlasKnows.challengingEvidenceCount": "Evidence that gives pause: {{count}}",
  "investmentCase.whatAtlasKnows.judgmentAvailable": "Recorded judgment: available",
  "investmentCase.whatAtlasKnows.judgmentNotAvailable": "Recorded judgment: not available",
  "investmentCase.whatAtlasKnows.decisionLabel": "Investor decision: {{type}}",
  "investmentCase.whatAtlasKnows.decisionNone": "Investor decision: not yet recorded",
  "investmentCase.whatAtlasKnows.outcomeYes": "Outcome: recorded",
  "investmentCase.whatAtlasKnows.outcomeNone": "Outcome: not recorded",
  "investmentCase.whatAtlasKnows.latestObservation": "Latest recorded observation",

  // ---------- investment case v2: what remains uncertain ----------
  "investmentCase.uncertain.heading": "What remains uncertain",
  "investmentCase.uncertain.noValuation": "No valuation analysis is currently available.",
  "investmentCase.uncertain.noMarketData":
    "Atlas has not yet received market data for this company.",
  "investmentCase.uncertain.noEvidence": "No company-specific evidence has been recorded.",
  "investmentCase.uncertain.percentOnly": "Portfolio impact can only be expressed in percentages.",
  "investmentCase.uncertain.awaitingReconciliation":
    "The latest allocation requires reconciliation.",

  // ---------- investment case v2: more details ----------
  "investmentCase.moreDetails.heading": "More details",
  "investmentCase.moreDetails.subheading": "Underlying record",

  // ---------- investment case v2: decision actions ----------
  "investmentCase.actions.heading": "What would you like to do?",
  "investmentCase.actions.addToPosition": "Add to Position",
  "investmentCase.actions.trimPosition": "Trim Position",
  "investmentCase.actions.removePosition": "Remove Position",
  "investmentCase.actions.leaveAsIs": "Leave as is",
  "investmentCase.actions.notLinkedNote":
    "Decision actions become available once this case is linked to a portfolio holding.",
  "investmentCase.actions.deferredWatchlist": "Watchlist actions are not yet available in Alpha.",
  "investmentCase.actions.deferredDiscovery": "Discovery actions are not yet available in Alpha.",
  "investmentCase.actions.reasonLabel": "Reason",
  "investmentCase.actions.confidenceLabel": "Your confidence (0-100)",
  "investmentCase.actions.submit": "Record decision",
  "investmentCase.actions.decisionRecordedNote":
    "Decision recorded. Atlas never executes trades — report the completed transaction below once it happens externally, or close this if nothing has happened yet.",
  "investmentCase.actions.leaveAsIsRecordedNote": "Recorded — no portfolio change.",
  "investmentCase.actions.reportTransaction": "Report completed transaction",
  "investmentCase.actions.close": "Close",
  "investmentCase.actions.openHistory": "Open History →",
  "investmentCase.actions.recordError": "Could not record this decision: {{message}}",

  // ---------- investment case v2: continuity footer ----------
  "investmentCase.continuity.line1":
    "Atlas will use recorded portfolio changes and case history in future reviews.",
  "investmentCase.continuity.line2":
    "Report completed purchases or sales to keep the current portfolio state accurate.",

  // ---------- investment case: case intelligence (ATLAS-017) ----------
  "investmentCase.intelligence.confidence.heading": "Confidence",
  "investmentCase.intelligence.confidence.explanation":
    "How well supported the current understanding is — not a prediction of future returns.",
  "investmentCase.intelligence.conviction.heading": "Conviction",
  "investmentCase.intelligence.conviction.available": "Available.",
  "investmentCase.intelligence.conviction.unavailable":
    "Unavailable — Atlas does not compute a conviction score.",

  "investmentCase.intelligence.evidence.heading": "Evidence",
  "investmentCase.intelligence.evidence.supportingCount": "Supporting evidence: {{count}}",
  "investmentCase.intelligence.evidence.challengingCount": "Contradicting evidence: {{count}}",
  "investmentCase.intelligence.evidence.contradictingHeading": "Contradicting evidence, by observation:",
  "investmentCase.intelligence.evidence.contradictingItem": "{{status}} ({{count}} contradicting)",

  "investmentCase.intelligence.epistemicStatus.supported": "supported",
  "investmentCase.intelligence.epistemicStatus.challenged": "challenged",
  "investmentCase.intelligence.epistemicStatus.contradicted": "contradicted",
  "investmentCase.intelligence.epistemicStatus.assumed": "assumed (no evidence yet)",

  "investmentCase.intelligence.keyRisks.heading": "Key Risks",
  "investmentCase.intelligence.keyRisks.empty": "No key risks identified right now.",
  "investmentCase.intelligence.keyRisks.contradictingEvidence": "Evidence contradicts the current thesis.",
  "investmentCase.intelligence.keyRisks.highConcentration": "High concentration in this position.",
  "investmentCase.intelligence.keyRisks.awaitingReconciliation": "Awaiting reconciliation after a trade.",

  "investmentCase.intelligence.missingEvidence.heading": "Missing Evidence",
  "investmentCase.intelligence.missingEvidence.empty": "No evidence gaps detected.",
  "investmentCase.intelligence.missingEvidence.noEvidenceRecorded":
    "No evidence recorded for this Investment Case.",
  "investmentCase.intelligence.missingEvidence.observationWithoutEvidence":
    "An Observation has no linked evidence.",
  "investmentCase.intelligence.missingEvidence.decisionWithoutLinkedObservation":
    "A Decision has no linked Observation.",

  "investmentCase.intelligence.openQuestions.heading": "Open questions",
  "investmentCase.intelligence.openQuestions.noEvidenceRecordedForCase":
    "What evidence supports or challenges this thesis?",
  "investmentCase.intelligence.openQuestions.observationWithoutEvidence":
    "Does this observation have supporting or challenging evidence?",
  "investmentCase.intelligence.openQuestions.decisionWithoutLinkedObservation":
    "What observation prompted this decision?",
  "investmentCase.intelligence.openQuestions.businessDurabilityNotAssessable":
    "Atlas has no business-fact data to assess durability from.",
  "investmentCase.intelligence.openQuestions.valuationThesisNotDocumented":
    "No valuation thesis has been documented.",
  "investmentCase.intelligence.openQuestions.portfolioFactorNotAssessable":
    "A portfolio-wide factor is not yet assessable.",

  "investmentCase.intelligence.portfolioContext.heading": "Portfolio Context",
  "investmentCase.intelligence.portfolioContext.notHeld": "Not currently a portfolio holding.",
  "investmentCase.intelligence.portfolioContext.noFacts": "No notable portfolio-context facts right now.",
  "investmentCase.intelligence.portfolioContext.largestHolding": "This is the portfolio's largest position.",
  "investmentCase.intelligence.portfolioContext.recentlyIncreased": "Most recently increased.",
  "investmentCase.intelligence.portfolioContext.recentlyTrimmed": "Most recently trimmed.",
  "investmentCase.intelligence.portfolioContext.highConcentration": "High concentration in the portfolio.",
  "investmentCase.intelligence.portfolioContext.pendingWorkflow": "Pending workflow items for this case.",
  "investmentCase.intelligence.portfolioContext.evidenceIncomplete": "Evidence coverage is incomplete.",

  "investmentCase.intelligence.observationTimeline.heading": "Observation Timeline",
  "investmentCase.intelligence.observationTimeline.empty": "No observations recorded yet.",
  "investmentCase.intelligence.observationTimeline.evidenceCount": "{{count}} evidence item(s)",

  // ---------- sprint 4: navigation ----------
  "shell.nav.history": "History",

  // ---------- daily brief implementation sprint 1: navigation ----------
  "shell.nav.dailyBrief": "Daily Brief",
  "shell.nav.discovery": "Discovery",

  // ---------- sprint 4: relative time ----------
  "relativeTime.today": "today",
  "relativeTime.oneDayAgo": "1 day ago",
  "relativeTime.daysAgo": "{{count}} days ago",
  "relativeTime.oneWeekAgo": "1 week ago",
  "relativeTime.weeksAgo": "{{count}} weeks ago",
  "relativeTime.oneMonthAgo": "1 month ago",
  "relativeTime.monthsAgo": "{{count}} months ago",

  // ---------- sprint 4: history page ----------
  "history.title": "History",
  "history.loadError": "Could not load history: {{message}}",
  "history.empty": "History begins after your first investment decision.",
  "history.empty.portfolioLink": "Open Portfolio →",
  "history.noneMatchFilter": "No activity matches this filter.",
  "history.filter.all": "All",
  "history.filter.open": "Open",
  "history.filter.completed": "Completed",
  "history.sort.newest": "Newest first",
  "history.sort.oldest": "Oldest first",
  "history.status.open": "Open",
  "history.status.completed": "Completed",
  "history.row.kindDecision": "Decision recorded",
  "history.row.kindOutcome": "Outcome reported",
  "history.row.kindTrade": "Trade executed",

  // ---------- sprint 4: dashboard sections ----------
  "dashboard.needsAttention.heading": "Needs Attention",
  "dashboard.needsAttention.empty": "Nothing needs your attention right now.",
  "dashboard.needsAttention.outcomeMissing": "{{security}}: outcome not yet reported",
  "dashboard.needsAttention.tradeMissing": "{{security}}: trade not yet reported",
  "dashboard.needsAttention.reconciliationNeeded": "{{security}}: allocation awaiting reconciliation",
  "dashboard.recentActivity.heading": "Recent Activity",
  "dashboard.recentActivity.empty": "No activity recorded yet.",
  "dashboard.continueWorking.heading": "Continue Working",
  "dashboard.continueWorking.empty": "No recent case activity yet.",
  "dashboard.viewHistoryLink": "View History →",

  // ---------- sprint 4: investment case last activity / timeline / outstanding work ----------
  "investmentCase.lastActivity.heading": "Last activity",
  "investmentCase.lastActivity.noneYet": "No activity recorded for this case yet.",
  "investmentCase.lastActivity.lastDecision": "Last decision: {{type}} recorded {{relativeTime}}.",
  "investmentCase.lastActivity.lastOutcome": "Last outcome: reported {{relativeTime}}.",
  "investmentCase.lastActivity.lastTrade": "Last trade: {{type}} {{detail}}, {{relativeTime}}.",
  "investmentCase.lastActivity.reconciliationOk": "Portfolio allocation is up to date.",
  "investmentCase.lastActivity.reconciliationNeeded": "Allocation is awaiting reconciliation.",
  "investmentCase.timeline.empty": "No timeline events yet.",
  "investmentCase.timeline.currentStatus": "Current status",
  "investmentCase.outstandingWork.heading": "Outstanding work",
  "investmentCase.outstandingWork.none": "Nothing outstanding for this case.",
  "investmentCase.outstandingWork.outcomeMissing": "Outcome not yet reported.",
  "investmentCase.outstandingWork.tradeMissing": "Trade not yet reported.",

  // ---------- sprint 4: navigation continuity (origin badges) ----------
  "investmentCase.origin.dashboard": "Opened from Dashboard",
  "investmentCase.origin.portfolio": "Opened from Portfolio",
  "investmentCase.origin.history": "Returned from History",
  "investmentCase.origin.dailyBrief": "Opened from Daily Brief",
  "investmentCase.origin.discovery": "Opened from Discovery",

  // ---------- daily brief implementation sprint 1 ----------
  "dailyBrief.title": "Daily Brief",
  "dailyBrief.verdict.nothingUrgent": "Nothing important requires your attention today.",
  "dailyBrief.verdict.oneItem": "One item requires your attention today.",
  "dailyBrief.verdict.items": "{{count}} items require your attention today.",
  "dailyBrief.priority.heading": "Priority",
  "dailyBrief.recentDecisions.heading": "Recent Decisions",
  "dailyBrief.recentDecisions.empty": "No decisions recorded yet.",
  "dailyBrief.monitoring.heading": "Monitoring",
  "dailyBrief.monitoring.body":
    "Atlas continues monitoring your recorded portfolio decisions and investment cases.",
  "dailyBrief.footer.reminder":
    "Keep Atlas updated when your portfolio changes so future reviews remain accurate.",

  // ---------- discovery v1 implementation sprint ----------
  "discovery.title": "Discovery",
  "discovery.prompt.heading": "How can I help you?",
  "discovery.prompt.supporting":
    "Ask about companies, sectors, market events, your portfolio or any investment idea.",
  "discovery.info.ariaLabel": "More information",
  "discovery.info.body":
    "Here you can discuss anything from a specific quarterly report or company to broader market trends, macroeconomics and portfolio strategy.",
  "discovery.info.learnMore": "Learn more about how Atlas Discovery works →",
  "discovery.portfolioContext.available": "Your portfolio is available as context for future Discovery analysis.",
  "discovery.input.placeholder": "Ask Atlas anything about investing…",
  "discovery.input.submit": "Send",
  "discovery.suggestions.aiStocks": "Are AI stocks attractive after the recent decline?",
  "discovery.suggestions.compare": "Compare two companies",
  "discovery.suggestions.strengthenPortfolio": "What would strengthen my portfolio?",
  "discovery.suggestions.reviewIdea": "Review an investment idea",
  "discovery.suggestions.marketTrend": "Help me think through a market trend",
  "discovery.response.bounded":
    "Discovery's live analysis engine is not connected in this Alpha yet. You can still open or create an Investment Case for a company you want to review.",
  "discovery.response.providerError":
    "Atlas couldn't generate a response just now. You can try asking again.",
  "discovery.chat.sending": "Thinking…",
  "discovery.chat.unavailable": "Atlas couldn't be reached. Check your connection and try again.",
  "discovery.reviewCompany.heading": "Review a company",
  "discovery.reviewCompany.createCase": "Create Investment Case →",
  "discovery.reviewCompany.openCase": "Open Investment Case →",
  "discovery.reviewCompany.notInPortfolio":
    "{{ticker}} is not in your current portfolio yet. Atlas cannot create a linked Investment Case for a company you don't hold.",
  "discovery.reviewCompany.error": "Could not create the Investment Case: {{message}}",
  "discovery.opportunities.heading": "Opportunities",
  "discovery.opportunities.notYet": "Atlas has not generated any market opportunities in this Alpha yet.",
  "discovery.tool.caseOpened": "Opening your existing Investment Case for {{ticker}}.",
  "discovery.tool.caseCreated": "Creating and opening an Investment Case for {{ticker}}.",
  "discovery.tool.tickerUnresolved":
    "{{ticker}} isn't in your current portfolio, so Atlas can't open a linked Investment Case for it yet. You can confirm the exact ticker, or use \"Review a company\" below once it's in your portfolio.",
  "discovery.tool.caseFailed":
    "Atlas couldn't create the Investment Case for {{ticker}} just now. You can try again, or use \"Review a company\" below.",

  // ---------- portfolio import v1.4 ----------
  "portfolioImport.title": "Import Portfolio",
  "portfolioImport.paste.heading": "Import your portfolio",
  "portfolioImport.paste.instructions": "Paste your holdings below.",
  "portfolioImport.paste.placeholder": "AMD 40\nNVDA 30\nASML 20",
  "portfolioImport.paste.reviewNote": "You will review everything before Atlas updates your portfolio.",
  "portfolioImport.paste.continueButton": "Review Portfolio",
  "portfolioImport.review.heading": "Review Portfolio",
  "portfolioImport.review.holdingsFound": "{{count}} holdings found",
  "portfolioImport.review.weightPercentLabel": "Weight %",
  "portfolioImport.review.resolved": "Resolved",
  "portfolioImport.review.needsConfirmation": "Needs confirmation",
  "portfolioImport.review.statsResolved": "{{count}} resolved automatically",
  "portfolioImport.review.statsNeedsConfirmation": "{{count}} require confirmation",
  "portfolioImport.review.statsUnsupported": "{{count}} recognized non-equity instruments",
  "portfolioImport.review.recognizedUnsupported": "Recognized instrument — needs confirmation before import",
  "portfolioImport.review.unsupportedManualWarning":
    "Entering a ticker will import this as an ordinary equity, even though Atlas recognizes it as: {{instrumentType}}. Only continue if that's what you intend.",
  "portfolioImport.instrumentType.equity": "Equity",
  "portfolioImport.instrumentType.fund": "Fund",
  "portfolioImport.instrumentType.etp": "Exchange-traded product",
  "portfolioImport.instrumentType.private": "Private company",
  "portfolioImport.instrumentType.other": "Other instrument",
  "portfolioImport.review.manualTickerPlaceholder": "Enter ticker",
  "portfolioImport.review.confirmationRequired": "{{count}} rows need a ticker before you can import",
  "portfolioImport.review.errorsHeading": "Could not import {{count}} rows",
  "portfolioImport.review.lineError": "Line {{line}} — {{error}}",
  "portfolioImport.review.noHoldingsFound": "No holdings found in the pasted text.",
  "portfolioImport.review.replaceWarning": "This will replace the holdings currently shown in Atlas.",
  "portfolioImport.review.backButton": "Back to edit",
  "portfolioImport.review.submitError": "Could not import your portfolio: {{message}}",
  "portfolioImport.error.missingName": "Missing name",
  "portfolioImport.error.missingValue": "Missing value",
  "portfolioImport.error.invalidValue": "Value is not a number",
  "portfolioImport.error.nonPositiveValue": "Value must be greater than zero",
  "portfolioImport.error.duplicateTicker": "Duplicate ticker: {{ticker}}",
  "portfolioImport.error.tooManyColumns": "Too many columns",
} as const;

export type TranslationKey = keyof typeof en;
