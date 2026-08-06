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
  "portfolio.cashLabel": "Cash: {{percent}}%",
  "portfolio.unallocated":
    "Unallocated: {{percent}}% — this portfolio does not yet account for 100% of holdings; Atlas does not invent the remainder.",
  "portfolio.concentration": "Concentration: {{value}}",
  "portfolio.concentrationLevel.low": "Low",
  "portfolio.concentrationLevel.moderate": "Moderate",
  "portfolio.concentrationLevel.elevated": "Elevated",
  "portfolio.concentrationLevel.high": "High",

  // ---------- dashboard ----------
  "dashboard.title": "Dashboard",
  "dashboard.portfolioStatus.heading": "Portfolio Status",
  "dashboard.portfolioStatus.loadError": "Could not load portfolio status: {{message}}",
  "dashboard.portfolioStatus.notEstablished": "No portfolio established yet.",
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
  "investmentCase.returnToPortfolio": "← Return to Portfolio",
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
  "investmentCase.outcome.quantityLabel": "Quantity",
  "investmentCase.outcome.executionPriceLabel": "Execution price",
  "investmentCase.outcome.feesLabel": "Fees (optional)",
  "investmentCase.outcome.executedAtLabel": "Executed date (optional — defaults to now)",
  "investmentCase.outcome.recordError": "Could not record this outcome: {{message}}",
  "investmentCase.outcome.validation.tradeRequiredFields":
    "Security, quantity, and execution price are required for a trade.",
} as const;

export type TranslationKey = keyof typeof en;
