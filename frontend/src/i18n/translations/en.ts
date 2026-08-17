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
  "portfolio.empty.eyebrow": "Getting started",
  "portfolio.empty.heading": "Import your portfolio to get started",
  "portfolio.empty.subheading":
    "Atlas will review your holdings, surface what needs attention, and help you think through decisions at your own pace.",
  "portfolio.empty.importButton": "Import Portfolio",
  "portfolio.empty.trySample": "Try with sample portfolio",
  "portfolio.empty.step.verify.title": "Verify holdings",
  "portfolio.empty.step.verify.body": "Confirm Atlas correctly identified your holdings from your broker import.",
  "portfolio.empty.step.understand.title": "Understand your portfolio",
  "portfolio.empty.step.understand.body": "See how your portfolio is structured across sectors, concentration, and coverage.",
  "portfolio.empty.step.attention.title": "Review what needs attention",
  "portfolio.empty.step.attention.body": "Atlas highlights holdings that may deserve a closer look, with reasoning you can evaluate.",
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
  // ---------- Internal Alpha Fix Sprint 1: Analysis Coverage (IA-003) ----------
  "portfolio.cockpit.analysisCoverage.label": "Analysis Coverage",
  "portfolio.cockpit.analysisCoverage.no_coverage": "No coverage",
  "portfolio.cockpit.analysisCoverage.partial_coverage": "Partial",
  "portfolio.cockpit.analysisCoverage.substantial_coverage": "Substantial",
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
  "portfolio.cockpit.review.none": "—",
  "portfolio.cockpit.review.standard_review": "Standard review",
  "portfolio.cockpit.review.evidence_review": "Evidence review",
  "portfolio.cockpit.review.priority_review": "Priority review",
  "portfolio.cockpit.viewCaseButton": "View Investment Case",
  "portfolio.cockpit.unresolved": "Investment Case could not be resolved",
  "portfolio.holdingsTable.rowAriaLabel": "View Investment Case for {{ticker}}",

  "portfolio.unallocated":
    "Unallocated: {{percent}}% — this portfolio does not yet account for 100% of holdings; Atlas does not invent the remainder.",
  "portfolio.concentration": "Concentration: {{value}}",
  "portfolio.concentrationLevel.low": "Low",
  "portfolio.concentrationLevel.moderate": "Moderate",
  "portfolio.concentrationLevel.elevated": "Elevated",
  "portfolio.concentrationLevel.high": "High",

  // ---------- portfolio header bar (Figma-fidelity rebuild) ----------
  "portfolio.header.holdings": "Holdings",
  "portfolio.header.cash": "Cash",
  "portfolio.header.unallocated": "Unallocated",
  "portfolio.header.expectedReturn": "Expected Return",
  "portfolio.header.actionRequired": "{{count}} Action Required",
  "portfolio.header.notAvailable": "—",
  "portfolio.summary.unknownInstrumentsWarning": "{{count}} holdings could not be fully resolved. Review instruments.",

  // ---------- portfolio pulse (Portfolio Workspace v1) ----------
  "portfolio.pulse.totalValueLabel": "Total Portfolio Value",
  "portfolio.pulse.totalValueUnavailable": "Value not available",
  "portfolio.pulse.holdingsLabel": "Holdings",
  "portfolio.pulse.holdingsCount": "{{count}} assets",
  "portfolio.pulse.coverageLabel": "Atlas Coverage",
  "portfolio.pulse.coverageValue": "{{covered}} of {{total}} covered",
  "portfolio.pulse.attentionPill": "{{count}} need attention",

  // ---------- needs your attention (Portfolio Workspace v1) ----------
  "portfolio.attention.heading": "Needs Your Attention",
  "portfolio.attention.empty": "Nothing needs your attention right now.",
  "portfolio.attention.viewAll": "View all attention items",
  "portfolio.attention.viewFewer": "Show fewer",
  "portfolio.attention.reason.concentration": "Concentration at {{percent}}% — above typical single-holding threshold.",
  "portfolio.attention.reason.coverageExpanded": "Atlas coverage expanded to full research.",
  "portfolio.attention.reason.high_financial_risk": "Financial risk is elevated.",
  "portfolio.attention.reason.high_valuation_risk": "Valuation risk is elevated.",
  "portfolio.attention.reason.low_conviction": "Conviction is low given available evidence.",
  "portfolio.attention.reason.contradicting_evidence": "Recorded evidence contains contradictions.",
  "portfolio.attention.reason.insufficient_evidence": "Evidence is insufficient for a confident assessment.",

  // ---------- portfolio priority strip (Figma-fidelity rebuild) ----------
  "portfolio.priorityStrip.empty": "Nothing needs your attention right now.",
  "portfolio.priorityStrip.reviewTitle": "Review {{ticker}}",
  "portfolio.priorityStrip.completeEvidenceTitle": "Complete evidence for {{ticker}}",
  "portfolio.priorityStrip.concentrationTitle": "Review concentration in {{ticker}}",
  "portfolio.priorityStrip.allocationTitle": "Review portfolio allocation",
  "portfolio.priorityStrip.evidenceReason": "Missing evidence.",
  "portfolio.priorityStrip.allocationReason": "{{percent}}% currently unallocated.",
  "portfolio.priorityStrip.reason.missingCase": "No Investment Case yet.",
  "portfolio.priorityStrip.reason.decisionWithoutOutcome": "Decision has no reported outcome.",
  "portfolio.priorityStrip.reason.outcomeWithoutExecution": "Outcome has no execution confirmed.",
  "portfolio.priorityStrip.reason.awaitingReconciliation": "Awaiting reconciliation after a trade.",
  "portfolio.priorityStrip.reason.veryOldCase": "Investment Case is {{days}} days old.",
  "portfolio.priorityStrip.reason.observationWithoutDecision": "An Observation has no Decision.",
  "portfolio.priorityStrip.reviewButton": "Review",
  "portfolio.priorityStrip.openCaseButton": "Open Case",
  "portfolio.priorityStrip.viewAll": "View all {{count}}",
  "portfolio.priorityStrip.viewFewer": "Show fewer",

  // ---------- holdings table (Portfolio Workspace v1) ----------
  "portfolio.holdingsTable.tickerHeader": "Ticker",
  "portfolio.holdingsTable.valueHeader": "Value",
  "portfolio.holdingsTable.shareHeader": "% Share",
  "portfolio.holdingsTable.coverageHeader": "Coverage",
  "portfolio.holdingsTable.reviewStatusHeader": "Review Status",
  "portfolio.holdingsTable.weightHeader": "Weight",
  "portfolio.holdingsTable.convictionHeader": "Conviction",
  "portfolio.holdingsTable.fitHeader": "Fit",
  "portfolio.holdingsTable.expReturnHeader": "Exp. Return",
  "portfolio.holdingsTable.upsideHeader": "Upside",
  "portfolio.holdingsTable.downsideHeader": "Downside",
  "portfolio.holdingsTable.riskHeader": "Risk",
  "portfolio.holdingsTable.actionHeader": "Action",
  "portfolio.holdingsTable.reconcileToggle": "Reconcile",
  "portfolio.holdingsTable.showingCount": "Showing {{shown}} of {{total}}",
  "portfolio.holdingsTable.viewAll": "View All Holdings ({{count}})",
  "portfolio.holdingsTable.viewFewer": "Show fewer",
  "portfolio.holdingsTable.coverage.substantial_coverage": "Covered",
  "portfolio.holdingsTable.coverage.partial_coverage": "Partial",
  "portfolio.holdingsTable.coverage.no_coverage": "Not Covered",
  "portfolio.holdingsTable.coverage.new": "New",
  "portfolio.holdingsTable.reviewStatus.reviewed": "Reviewed",
  "portfolio.holdingsTable.reviewStatus.needsReview": "Needs Review",
  "portfolio.holdingsTable.reviewStatus.new": "New",

  // ---------- concentration summary + coverage sidebar (Portfolio Workspace v1) ----------
  "portfolio.concentrationSummary.heading": "Concentration Summary",
  "portfolio.concentrationSummary.subheading": "Top {{count}} holdings represent {{percent}}% of total value.",
  "portfolio.coverageActive.title": "Atlas Coverage Active",
  "portfolio.coverageActive.body": "{{covered}} of your {{total}} unique holdings are fully covered.",
  "portfolio.sectorAllocation.heading": "Sector Allocation",
  "portfolio.sectorAllocation.unavailable":
    "Sector data isn't tracked for holdings yet — this panel is intentionally omitted rather than showing invented allocations.",

  // ---------- recent activity (Portfolio Workspace v1) ----------
  "portfolio.recentActivity.heading": "Recent Activity",
  "portfolio.recentActivity.empty": "No recent activity recorded.",

  // ---------- holding attention detail (Portfolio Workspace v1) ----------
  "portfolio.holdingDetail.breadcrumb": "Portfolio / {{ticker}}",
  "portfolio.holdingDetail.subheading": "Focused Holding Analysis",
  "portfolio.holdingDetail.currentMarketValue": "Current Market Value",
  "portfolio.holdingDetail.portfolioWeight": "Portfolio Weight",
  "portfolio.holdingDetail.attentionHeading": "Attention",
  "portfolio.holdingDetail.noAttentionReasons": "This holding is not currently flagged for attention.",
  "portfolio.holdingDetail.analysisContextHeading": "Analysis Context",
  "portfolio.holdingDetail.decisionSupportLabel": "Decision Support",
  "portfolio.holdingDetail.convictionLabel": "Conviction",
  "portfolio.holdingDetail.riskFactorsLabel": "Risk Factors Identified",
  "portfolio.holdingDetail.noRiskFactors": "No specific risk factors identified.",
  "portfolio.holdingDetail.contextNote":
    "Portfolios with similar concentration often consider partial rebalancing. Your situation is unique — this is context, not a recommendation.",
  "portfolio.holdingDetail.backToPortfolio": "Back to Portfolio",
  "portfolio.holdingDetail.dismissButton": "Dismiss from Attention",
  "portfolio.holdingDetail.dismissUnavailable": "Not yet available",
  "portfolio.holdingDetail.recordDecisionButton": "Record a Decision",
  "portfolio.holdingDetail.openCompanyWorkspace": "Open Company Workspace",
  "portfolio.holdingDetail.notFound": "Could not find this holding in your portfolio.",

  // ---------- portfolio intelligence panels (Figma-fidelity rebuild) ----------
  "portfolio.keyFindingsPanel.heading": "Key Findings",
  "portfolio.keyFindingsPanel.empty": "No notable findings right now.",
  "portfolio.riskSignalsPanel.heading": "Risk Signals",
  "portfolio.riskSignalsPanel.empty": "No risk signals right now.",
  "portfolio.riskSignalsPanel.missingEvidenceCount": "{{count}} holding(s) have missing evidence.",
  "portfolio.riskSignals.high_concentration": "{{ticker}} is a concentrated position.",
  "portfolio.riskSignals.missing_case": "{{ticker}} has no Investment Case yet.",
  "portfolio.riskSignals.missing_evidence": "{{ticker}} has missing evidence.",
  "portfolio.riskSignals.awaiting_reconciliation": "{{ticker}} is awaiting reconciliation after a trade.",
  "portfolio.riskSignals.stale_review": "{{ticker}} has not been reviewed in a long time.",

  // ---------- discussion prompts (Workspace Migration Phase 2: the
  // page-local "Today's Discussions" Ask box itself was removed --
  // Decision Log #2 -- these remain only as `deriveDiscussionPrompts.ts`'s
  // own real candidate input for the future Atlas Companion, plus one
  // key still shared with Investment Case's own placeholder note) ----------
  "portfolio.discussions.comingSoonNote":
    "Atlas conversations aren't available yet — this is ready for a future release.",
  "portfolio.discussions.prompt.priorityHolding":
    "{{ticker}} is currently your highest priority holding. Would you like to review it?",
  "portfolio.discussions.prompt.diversification":
    "Your portfolio is spread across {{count}} holdings with low concentration. Would concentrating your highest-conviction ideas improve expected upside?",
  "portfolio.discussions.prompt.concentration":
    "{{ticker}} makes up a large share of your portfolio. Would reducing this position improve diversification?",
  "portfolio.discussions.prompt.unallocated":
    "{{percent}}% of your capital is currently unallocated. Where should this capital be deployed?",
  "portfolio.discussions.prompt.evidenceGaps":
    "{{count}} holdings have gaps in their evidence. Want to review what's missing?",
  "portfolio.discussions.prompt.staleCases":
    "{{count}} Investment Cases haven't been reviewed in a long time. Want to go through them?",
  "portfolio.discussions.prompt.missingCases":
    "{{count}} holdings don't have an Investment Case yet. Want to start one?",

  // ---------- portfolio intelligence (ATLAS-016) ----------
  "portfolio.intelligence.confidence.not_applicable": "Insufficient evidence",
  "portfolio.intelligence.confidence.none": "No evidence recorded",
  "portfolio.intelligence.confidence.partial": "Partial evidence",
  "portfolio.intelligence.confidence.full": "Full evidence coverage",

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
  "investmentCase.returnTo.company": "← Back to Company Workspace",
  "investmentCase.noCaseSelected": "No case selected.",
  "investmentCase.loadError": "Could not load this case: {{message}}",
  "investmentCase.subject": "Subject: Case {{caseId}}",
  "investmentCase.status.heading": "Status",
  "investmentCase.status.healthy": "Healthy",
  "investmentCase.status.needsReview": "Needs Review",
  "investmentCase.status.highPriority": "High Priority",
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
  "investmentCase.atlasView.heading": "Atlas View",
  "investmentCase.atlasView.thesis.heading": "Current Case",
  "investmentCase.atlasView.strengths.heading": "Strengths",
  "investmentCase.atlasView.strengths.empty": "Atlas has not identified a clear strength yet.",
  "investmentCase.atlasView.risks.heading": "Risks",
  "investmentCase.atlasView.risks.empty": "Atlas has not identified a clear risk yet.",
  "investmentCase.atlasView.growth.heading": "Growth",
  "investmentCase.atlasView.growth.recentTrendLabel": "Most recent periods ({{periods}})",
  "investmentCase.atlasView.growth.trend.strong_metric": "consistently increasing",
  "investmentCase.atlasView.growth.trend.weak_metric": "consistently declining",
  "investmentCase.atlasView.growth.trend.mixed_metric": "mixed, with both increases and decreases",
  "investmentCase.atlasView.valuationContext.heading": "Valuation",
  "investmentCase.atlasView.valuationContext.currentYieldLabel": "Current FCF yield",
  "investmentCase.atlasView.valuationContext.scenarioUnavailable": "Atlas does not yet have sufficient scenario-based valuation support to determine whether the current price offers attractive expected return.",
  "investmentCase.atlasView.openQuestions.heading": "Open Questions",
  "investmentCase.atlasView.openQuestions.empty": "No open questions identified for this Case right now.",
  "investmentCase.atlasView.openQuestions.growth_inconclusive": "Is this business actually growing? Atlas does not yet have enough revenue or free cash flow history to say.",
  "investmentCase.atlasView.openQuestions.growth_mixed": "Is recent growth durable, or was it one-off?",
  "investmentCase.atlasView.openQuestions.capital_allocation_inconclusive": "How is capital being allocated? Atlas does not yet have enough buyback, issuance, or debt data.",
  "investmentCase.atlasView.openQuestions.capital_allocation_weak": "Is current capital allocation (dilution or rising leverage) temporary or persistent?",
  "investmentCase.atlasView.openQuestions.valuation_inconclusive": "Is the current price cheap or expensive? Atlas does not yet have enough historical valuation data to say.",
  "investmentCase.atlasView.openQuestions.valuation_expensive_versus_growth": "Does the current price already discount the growth Atlas is seeing?",
  "investmentCase.atlasView.openQuestions.scenario_valuation_unavailable": "Does the current price offer attractive expected return under explicit forward assumptions? Atlas does not yet support scenario-based valuation.",
  "investmentCase.atlasView.highlight.valuation": "Price vs. History",
  "investmentCase.atlasView.notAvailable": "—",
  "investmentCase.atlasView.dimension.businessStrength": "Business Strength",
  "investmentCase.atlasView.dimension.growth": "Growth",
  "investmentCase.atlasView.dimension.valuation": "Valuation",
  "investmentCase.atlasView.dimension.riskLevel": "Risk Level",
  "investmentCase.atlasView.dimension.capitalAllocation": "Capital Allocation",
  "investmentCase.atlasView.dimension.expectedReturn": "Expected Return",
  "investmentCase.atlasView.dimension.portfolioFit": "Portfolio Fit",
  "investmentCase.whatChanged.heading": "What Changed",
  "investmentCase.whatChanged.baseline": "Atlas has established a baseline for this Case. Future analyses will be compared against it.",
  "investmentCase.whatChanged.noChange": "No material change since the previous analysis.",
  "investmentCase.whatChanged.sincePrevious": "Since the previous analysis:",
  "investmentCase.whatChanged.thesisImpact.strengthened": "Overall, the Atlas Thesis has strengthened.",
  "investmentCase.whatChanged.thesisImpact.weakened": "Overall, the Atlas Thesis has weakened, but remains intact.",
  "investmentCase.whatChanged.thesisImpact.mixed": "The case shows mixed signals, but the broader Atlas Thesis remains intact.",
  "investmentCase.whatChanged.thesisImpact.unchanged": "The Atlas Thesis is materially unchanged.",
  "investmentCase.whatChanged.verb.improved": "improved",
  "investmentCase.whatChanged.verb.weakened": "weakened",
  "investmentCase.whatChanged.verb.increased": "increased",
  "investmentCase.whatChanged.verb.decreased": "decreased",
  "investmentCase.whatChanged.verb.moreAttractive": "more attractive",
  "investmentCase.whatChanged.verb.lessAttractive": "less attractive",
  "investmentCase.whatChanged.change.dimensionChanged": "{{dimension}} {{verb}} from {{previous}} to {{current}}.",
  "investmentCase.whatChanged.change.valuationChanged": "Valuation became {{verb}}.",
  "investmentCase.whatChanged.change.coverageGained": "Atlas can now evaluate {{dimension}} after new data became available.",
  "investmentCase.whatChanged.change.coverageLost": "Atlas can no longer evaluate {{dimension}} — prior supporting data is no longer available.",
  "investmentCase.whatChanged.change.strengthAdded": "New strength identified: {{label}}.",
  "investmentCase.whatChanged.change.strengthRemoved": "{{label}} is no longer classified as a strength.",
  "investmentCase.whatChanged.change.riskAdded": "New risk identified: {{label}}.",
  "investmentCase.whatChanged.change.riskRemoved": "{{label}} is no longer classified as a risk.",
  "investmentCase.whatChanged.change.openQuestionAdded": "A new open question has emerged.",
  "investmentCase.whatChanged.change.openQuestionResolved": "A previously open question has been resolved.",
  "investmentCase.analysis.companyOverview.heading": "Company Overview",
  "investmentCase.analysis.companyOverview.exchangeLabel": "Exchange",
  "investmentCase.analysis.companyOverview.sectorLabel": "Sector",
  "investmentCase.analysis.companyOverview.industryLabel": "Industry",
  "investmentCase.analysis.companyOverview.countryLabel": "Country",
  "investmentCase.analysis.companyOverview.fiscalYearEndLabel": "Fiscal year end",
  "investmentCase.analysis.companyOverview.foundedLabel": "Founded",
  "investmentCase.analysis.companyOverview.ceoLabel": "CEO",
  "investmentCase.analysis.companyOverview.employeesLabel": "Employees",
  "investmentCase.analysis.companyOverview.empty": "Not yet identified",
  "investmentCase.analysis.financials.heading": "Financials",
  "investmentCase.analysis.financials.unknownPeriodLabel": "Unknown period",
  "investmentCase.analysis.financials.revenueLabel": "Revenue",
  "investmentCase.analysis.financials.operatingIncomeLabel": "Operating Income",
  "investmentCase.analysis.financials.netIncomeLabel": "Net Income",
  "investmentCase.analysis.financials.epsLabel": "EPS (diluted)",
  "investmentCase.analysis.financials.freeCashFlowLabel": "Free Cash Flow",
  "investmentCase.analysis.financials.capitalExpenditureLabel": "Capital Expenditure",
  "investmentCase.analysis.financials.shareBuybacksLabel": "Share Buybacks",
  "investmentCase.analysis.financials.dividendsLabel": "Dividends",
  "investmentCase.analysis.financials.cashLabel": "Cash & Equivalents",
  "investmentCase.analysis.financials.totalDebtLabel": "Total Debt",
  "investmentCase.analysis.financials.marketSnapshotHeading": "Current Market Data",
  "investmentCase.analysis.financials.sharePriceLabel": "Share Price",
  "investmentCase.analysis.financials.sharesOutstandingLabel": "Shares Outstanding",
  "investmentCase.analysis.financials.marketCapLabel": "Market Cap",
  "investmentCase.analysis.financials.empty": "Not yet available",
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
  "investmentCase.analysis.business.portfolioContextHeading": "Portfolio Context",
  "investmentCase.analysis.business.largestPositionLabel": "Largest position: {{ticker}} ({{percent}}%)",
  "investmentCase.analysis.business.otherCategoriesHeading": "Other Dimensions",
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
  "investmentCase.analysis.evidence.qualityHeading": "Evidence Quality",
  "investmentCase.analysis.evidence.missingEvidenceHeading": "Missing Evidence",
  "investmentCase.analysis.evidence.latestLabel": "Latest",
  "investmentCase.analysis.evidence.viewAll": "View all evidence",
  "investmentCase.analysis.evidence.noneRecorded": "No Evidence recorded for this Case yet.",
  "investmentCase.analysis.valuationScenarios.heading": "Valuation Scenarios",
  "investmentCase.analysis.valuationScenarios.notYet": "Not yet supported",
  "investmentCase.analysis.recommendation.heading": "Decision Support",
  "decisionSupport.badge.entry_supported": "Entry supported",
  "decisionSupport.badge.increase_supported": "Increase supported",
  "decisionSupport.badge.thesis_intact": "Thesis intact",
  "decisionSupport.badge.reduction_supported": "Reduction supported",
  "decisionSupport.badge.exit_supported": "Exit supported",
  "decisionSupport.badge.no_action_supported": "No action supported",
  "decisionSupport.badge.insufficient_evidence": "Insufficient evidence",
  "decisionSupport.statement.entry_supported": "Current evidence supports initiating a position.",
  "decisionSupport.statement.increase_supported": "Current evidence supports increasing exposure.",
  "decisionSupport.statement.thesis_intact": "Current thesis remains intact.",
  "decisionSupport.statement.reduction_supported": "Current evidence supports reducing exposure.",
  "decisionSupport.statement.exit_supported": "Current evidence supports exiting the position.",
  "decisionSupport.statement.no_action_supported": "Current evidence does not support initiating a position in this security.",
  "decisionSupport.statement.insufficient_evidence": "Current evidence is insufficient to support any portfolio action.",
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
  "investmentCase.header.valuationLabel": "Valuation",
  "investmentCase.header.portfolioFitLabel": "Portfolio fit",
  "investmentCase.header.untitled": "Investment Case",

  // ---------- investment case hero (UX-020 / APP-002 / APP-003) ----------
  "investmentCase.hero.srHeading": "Atlas's current view",
  "investmentCase.hero.loading": "Atlas is preparing its current assessment of {{ticker}}…",
  "investmentCase.hero.why.aligned_positive":
    "Business fundamentals remain strong, and today's valuation doesn't stand in the way.",
  "investmentCase.hero.why.aligned_negative":
    "The business has weakened, and valuation offers little reason to look past that.",
  "investmentCase.hero.why.business_strong_valuation_weak":
    "The underlying business remains strong, though today's valuation leaves little margin of safety.",
  "investmentCase.hero.why.business_weak_valuation_strong":
    "Valuation looks attractive here, though the underlying business raises real questions worth resolving first.",
  "investmentCase.hero.why.insufficient":
    "The evidence so far is thinner than usual, so this view should be treated as a starting point rather than a settled one.",
  "investmentCase.hero.closing.changed": "Something has changed since your last review — worth a closer look below.",
  "investmentCase.hero.closing.none": "Nothing has changed since your last visit.",
  "investmentCase.hero.closing.outcomeMissing":
    "One thing worth a moment: a recorded decision here is still waiting on its outcome.",
  "investmentCase.hero.closing.reconciliationNeeded":
    "One thing worth a moment: this position still needs to be reconciled.",
  "investmentCase.hero.closing.thesisStale":
    "One thing worth a moment: the thesis here hasn't been revisited in a while.",
  "investmentCase.hero.closing.openQuestion":
    "One thing worth a moment: there's an open question still worth resolving.",
  "investmentCase.hero.withheld.opening":
    "Atlas doesn't yet have enough evidence to form a clear view on {{ticker}}.",
  "investmentCase.hero.withheld.reason":
    "What's available so far leaves real, unresolved questions that keep Atlas from reaching a confident conclusion either way.",
  "investmentCase.hero.withheld.closing":
    "There's nothing to act on today — this isn't a gap Atlas overlooked, it's an honest reflection of what's currently knowable.",
  "investmentCase.hero.asOf": "Reflects Atlas's analysis as of {{when}}.",
  "investmentCase.hero.riskLabel": "{{category}} risk: {{status}}",
  "investmentCase.hero.supportingDetailsLabel": "Supporting details",

  // ---------- investment case workspace v2: executive summary (Sprint 2) ----------
  "investmentCase.executiveSummary.heading": "Executive Summary",
  "investmentCase.executiveSummary.assessment.conviction.very_high": "Conviction is very high.",
  "investmentCase.executiveSummary.assessment.conviction.high": "Conviction remains high.",
  "investmentCase.executiveSummary.assessment.conviction.moderate": "Conviction is moderate.",
  "investmentCase.executiveSummary.assessment.conviction.low": "Conviction is low.",
  "investmentCase.executiveSummary.assessment.conviction.insufficient_evidence":
    "There isn't yet enough evidence for a conviction view.",
  "investmentCase.executiveSummary.assessment.valuation.undervalued": "Valuation looks attractive.",
  "investmentCase.executiveSummary.assessment.valuation.fairly_valued": "Valuation looks reasonable.",
  "investmentCase.executiveSummary.assessment.valuation.expensive": "Valuation has become demanding.",
  "investmentCase.executiveSummary.assessment.risk": "{{category}} risk is currently {{status}}.",
  "investmentCase.executiveSummary.assessment.thesisStale": "The thesis hasn't been revisited in a while.",
  "investmentCase.executiveSummary.assessment.insufficientOverall":
    "There isn't enough evidence yet for a full assessment.",
  "investmentCase.executiveSummary.priority.heading": "Current Priority",
  "investmentCase.executiveSummary.priority.outcomeMissing": "Complete missing outcome.",
  "investmentCase.executiveSummary.priority.reconciliationNeeded": "Review position.",
  "investmentCase.executiveSummary.priority.thesisStale": "Review thesis.",
  "investmentCase.executiveSummary.priority.openQuestion": "Review evidence.",
  "investmentCase.executiveSummary.priority.none": "Nothing needs attention right now.",
  "investmentCase.executiveSummary.portfolioImpact.heading": "Portfolio Impact",
  "investmentCase.executiveSummary.portfolioImpact.weight": "Portfolio weight: {{percent}}%",
  "investmentCase.executiveSummary.portfolioImpact.largestPosition": "This is your largest position.",
  "investmentCase.executiveSummary.portfolioImpact.cash": "Cash exposure: {{percent}}%",
  "investmentCase.executiveSummary.outstandingIssues.heading": "Outstanding Issues",
  "investmentCase.executiveSummary.outstandingIssues.missingEvidence": "Missing evidence.",
  "investmentCase.executiveSummary.outstandingIssues.thesisStale": "Thesis is stale.",
  "investmentCase.executiveSummary.outstandingIssues.outcomeMissing": "Outcome missing.",
  "investmentCase.executiveSummary.outstandingIssues.tradeMissing": "Trade not yet reported.",
  "investmentCase.executiveSummary.outstandingIssues.reconciliationNeeded": "Needs reconciliation.",
  "investmentCase.executiveSummary.outstandingIssues.moreCount": "+ {{count}} more issue(s)",
  "investmentCase.executiveSummary.discuss.heading": "Discuss this Case",
  "investmentCase.executiveSummary.discuss.valuationVsConviction":
    "Valuation currently looks demanding while conviction remains {{conviction}}. Would you like to discuss whether this changes your thesis?",
  "investmentCase.executiveSummary.discuss.thesisStale":
    "This thesis hasn't been revisited in a while. Would you like to discuss whether anything has changed?",
  "investmentCase.executiveSummary.discuss.evidenceGap":
    "There are gaps in the evidence for this case. Want to talk through what's missing?",
  "investmentCase.executiveSummary.discuss.outstandingWork":
    "There's outstanding work on this case. Want to review it together?",
  "investmentCase.executiveSummary.discuss.generic": "Would you like to discuss this position?",
  "investmentCase.executiveSummary.discuss.button": "Discuss",
  "investmentCase.executiveSummary.discuss.askButton": "Ask",
  "investmentCase.executiveSummary.askPlaceholder": "Ask Atlas anything about this case…",

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
  "investmentCase.actions.recordDecisionTrigger": "Record a decision",
  "investmentCase.actions.outcomeAwaitingNudge": "{{count}} decision(s) awaiting an outcome",
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

  // ---------- History v1: analytical timeline ----------
  // A read-only presentation layer over persisted Investment Case
  // snapshots -- see atlas/analysis_engine/investment_case_history.py.
  // Reuses investmentCase.whatChanged.*/investmentCase.atlasView.*/
  // dailyBrief.entry.* wording directly rather than restating it.
  "history.scope.all": "All",
  "history.scope.decisions": "Decisions & Trades",
  "history.scope.investmentCases": "Investment Case Changes",
  "history.analytical.emptyOnly": "No analytical history yet.",
  "history.analytical.baseline": "Baseline established",
  "history.analytical.baselineDescription": "Atlas created its first structured Investment Case for {{company}}.",
  "history.analytical.headline.strengthened": "Thesis strengthened",
  "history.analytical.headline.weakened": "Thesis weakened",
  "history.analytical.headline.mixed": "Mixed signals",
  "history.analytical.headline.unchanged": "No material change",
  "history.analytical.viewDetails": "View details",
  "history.analytical.hideDetails": "Hide details",
  "history.analytical.detail.thesisHeading": "Atlas Thesis at this point",
  "history.analytical.detail.noThesis": "No Atlas Thesis recorded at this point.",
  "history.analytical.detail.strengthsHeading": "Strengths",
  "history.analytical.detail.risksHeading": "Risks",
  "history.analytical.detail.growthHeading": "Growth",
  "history.analytical.detail.valuationHeading": "Valuation",
  "history.analytical.detail.openQuestionsHeading": "Open Questions",
  "history.analytical.detail.empty": "None recorded at this point.",

  // ---------- Visual Fidelity Pass: History ----------
  "history.summary": "You've recorded {{count}} investment decisions across {{companies}} companies since {{since}}.",
  "history.timeline.heading": "Decision Timeline",
  "history.timeline.viewFull": "View full timeline",
  "history.reviews.heading": "Decision Reviews",
  "history.reviews.subheading": "Recent decisions worth reflecting on",
  "history.reviews.originalThesis": "Original Thesis",
  "history.reviews.outcome": "Outcome",
  "history.reviews.observedProperties.heading": "Observed in your decision history",
  "history.reviews.observedProperties.scope.singleCompany": "Company-specific",
  "history.reviews.observedProperties.scope.portfolioWide": "Portfolio-wide",
  "history.reviews.observedProperties.dateRange": "{{from}} – {{to}}",
  "history.reviews.observedProperties.smallSample": "Small recorded sample.",
  "history.reviews.observedProperties.limitation": "Based only on recorded Decisions. Outcomes and performance are not considered.",

  // ---------- Sprint 21: Explicit Security Confirmation ----------
  "history.reviews.securityConfirmation.recordedAs": "Recorded as",
  "history.reviews.securityConfirmation.loadError": "Couldn't load security confirmation.",
  "history.reviews.securityConfirmation.confirmedSelection": "Confirmed selection",
  "history.reviews.securityConfirmation.confirmedByYou": "Confirmed by you.",
  "history.reviews.securityConfirmation.findSecurity": "Find security",
  "history.reviews.securityConfirmation.discoveryError": "Couldn't search for this security.",
  "history.reviews.securityConfirmation.possibleMatch": "Possible match",
  "history.reviews.securityConfirmation.noCandidateFound": "No candidate found.",
  "history.reviews.securityConfirmation.confirmThisSecurity": "Confirm this security",
  "history.reviews.securityConfirmation.notThisSecurity": "Not this security",
  "history.reviews.securityConfirmation.confirmError": "Couldn't save your confirmation. Try again.",
  "history.reviews.securityConfirmation.changeSelection": "Change selection",
  "history.reviews.securityConfirmation.removeConfirmation": "Remove confirmation",
  "history.reviews.securityConfirmation.revokeError": "Couldn't remove your confirmation. Try again.",
  "history.reviews.securityConfirmation.changeSelectionNote": "Your previous confirmation stays in Atlas's history.",
  "history.reviews.securityConfirmation.verificationLabel": "External verification",
  "history.reviews.securityConfirmation.verify": "Verify with external provider",
  "history.reviews.securityConfirmation.verifyAgain": "Verify again",
  "history.reviews.securityConfirmation.verifying": "Verification pending…",
  "history.reviews.securityConfirmation.verifyError": "Unable to verify right now. Try again.",
  "history.reviews.securityConfirmation.verificationVerified": "Verified using external provider",
  "history.reviews.securityConfirmation.verificationNotVerified": "Not confirmed by external provider",
  "history.reviews.securityConfirmation.verificationUnavailable": "Verification unavailable",
  "history.reviews.securityConfirmation.verificationAmbiguous": "External provider found multiple possible matches",
  "history.reviews.securityConfirmation.verificationUnsupported": "Verification isn't available for this confirmation",

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
  "investmentCase.origin.companion": "Opened from Atlas Companion",
  "investmentCase.origin.company": "Opened from Company Workspace",

  // ---------- investment case figma-fidelity rebuild: key metrics / strength-concern-priority ----------
  "investmentCase.keyMetrics.heading": "Key Metrics",
  "investmentCase.keyMetrics.recommendationLabel": "Recommendation",
  "investmentCase.keyMetrics.convictionLabel": "Analysis Depth",
  "investmentCase.keyMetrics.valuationSupportLabel": "Downside Support",
  "investmentCase.valuationSupport.present": "Downside support present",
  "investmentCase.valuationSupport.absent": "Downside support absent",
  "investmentCase.valuationSupport.unresolved": "Valuation conclusion unresolved",
  "investmentCase.valuationSupport.cardHeading": "Valuation Support",
  "investmentCase.valuationSupport.gap.missingCapitalDeploymentValuationSupport":
    "Atlas hasn't yet made the separate judgment of whether today's price supports committing new capital.",
  "investmentCase.valuationSupport.gap.noDurableGrowthBasis":
    "There's no period of real growth yet for Atlas to build a valuation range from.",
  "investmentCase.valuationSupport.gap.insufficientHistoricalValuationData":
    "There isn't enough price history yet to complete this check.",
  "investmentCase.valuationSupport.gap.scenarioEnvelopeInconclusive":
    "The valuation range includes both a gain and a loss, depending on which scenario is used.",
  "investmentCase.valuationSupport.gap.conflictingValuationProofs":
    "Two real valuation checks point in different directions, and Atlas doesn't pick a side.",
  "investmentCase.valuationSupport.gap.noSufficientValuationProof":
    "Atlas doesn't yet have a reliable way to evaluate this company's valuation.",
  "investmentCase.limitingFactors.heading": "What limits this conclusion?",
  "investmentCase.limitingFactors.valuationGapTitle": "Valuation",
  "investmentCase.hero.limitedByPrefix": "Limited by:",
  "investmentCase.withheld.missing.businessEvaluation": "Atlas hasn't yet completed its business analysis for this company.",
  "investmentCase.withheld.missing.valuation": "Atlas hasn't yet completed a valuation analysis for this company.",
  "investmentCase.withheld.missing.portfolioIntelligence":
    "Atlas hasn't yet completed a portfolio-fit analysis for this company.",
  "investmentCase.withheld.missing.reasoning": "Atlas hasn't yet completed its reasoning synthesis for this company.",
  "investmentCase.keyMetrics.currentPriceLabel": "Current Price",
  "investmentCase.keyMetrics.expectedReturnLabel": "Expected Return",
  "investmentCase.keyMetrics.upsideDownsideLabel": "Upside / Downside",
  "investmentCase.keyMetrics.notYetAvailable": "Not yet available",
  "investmentCase.keyMetrics.expectedReturnCaption": "Long-term, growth-and-reversion range -- not a price target.",

  // ---------- Recommendation / Decision Intelligence Sprint 1: Outlook<->Recommendation alignment ----------
  "investmentCase.outlookAlignment.corroborates": "Atlas's independently-computed long-term Outlook also implies weak prospective returns, consistent with this recommendation.",
  "investmentCase.outlookAlignment.diverges": "Atlas's independently-computed long-term Outlook implies stronger prospective returns than this recommendation reflects -- a genuine tension worth weighing, not a contradiction.",
  "investmentCase.outlookAlignment.mixed": "Atlas's independently-computed long-term Outlook is mixed and does not clearly corroborate or diverge from this recommendation.",
  "investmentCase.outlookAlignment.unavailable": "Long-term Outlook is not yet available for comparison against this recommendation.",

  "investmentCase.strengthConcernPriority.strengthLabel": "Biggest Strength",
  "investmentCase.strengthConcernPriority.concernLabel": "Biggest Concern",
  "investmentCase.strengthConcernPriority.priorityLabel": "Current Priority",
  "investmentCase.strengthConcernPriority.noStrength": "No strength has clear evidence support yet.",
  "investmentCase.strengthConcernPriority.noConcern": "No concern has clear evidence support yet.",
  "investmentCase.currentPriority.none": "Nothing is currently outstanding for this case.",
  "investmentCase.concern.thesis_risk": "The thesis itself carries an identified risk worth watching.",

  // ---------- investment case figma-fidelity rebuild: atlas outlook ----------
  "investmentCase.outlook.heading": "Atlas Outlook",
  "investmentCase.outlook.notYetComputed": "Not yet computed",
  "investmentCase.outlook.shortTerm.heading": "Short-Term",
  "investmentCase.outlook.longTerm.heading": "Long-Term",
  "investmentCase.outlook.expectedReturnLabel": "Valuation-Implied Return Range",
  "investmentCase.outlook.convictionLabel": "Conviction",
  "investmentCase.outlook.bullCaseLabel": "Valuation Bull",
  "investmentCase.outlook.baseCaseLabel": "Valuation Base",
  "investmentCase.outlook.bearCaseLabel": "Valuation Bear",
  "investmentCase.outlook.momentumLabel": "Momentum",
  "investmentCase.outlook.keyDriversLabel": "Key Drivers",
  "investmentCase.outlook.whatChangedLabel": "What Changed",
  "investmentCase.outlook.noDrivers": "No key drivers identified yet.",
  "investmentCase.outlook.noChanges": "Nothing has changed recently.",

  // ---------- outlook intelligence sprint 1: real expected return / scenarios / momentum / drivers ----------
  "investmentCase.outlook.returnBasisNote": "{{basis}}, over {{low}}–{{high}} months.",
  "investmentCase.outlook.basis.cumulative": "Cumulative return",
  "investmentCase.outlook.basis.annualized": "Annualized return",
  "investmentCase.outlook.gap.noHistoricalValuationRange":
    "Not enough historical valuation data to build a range yet.",
  "investmentCase.outlook.gap.valuationNotConclusive": "No current valuation to project from yet.",
  "investmentCase.outlook.gap.noDurableGrowthTrajectory":
    "No real, recent, durable growth trajectory Atlas can responsibly project forward yet — never fabricated here.",
  "investmentCase.outlook.momentum.strengthening": "Strengthening",
  "investmentCase.outlook.momentum.stable": "Stable",
  "investmentCase.outlook.momentum.mixed": "Mixed",
  "investmentCase.outlook.momentum.weakening": "Weakening",
  "investmentCase.outlook.rerangeAssumptionNote":
    "Assumes free cash flow stays at its current level and only the market's own valuation multiple changes — not a forecast of business performance.",
  "investmentCase.outlook.scenarioAssumptionNote": "Assumes the market re-rates to a {{targetYield}} FCF yield.",
  "investmentCase.outlook.scenariosCaption":
    "Valuation scenarios only — based on {{count}} historical FCF-yield observation(s), including any unusual periods.",
  "investmentCase.outlook.growthScenariosCaption":
    "Business-growth scenarios sharing one terminal valuation assumption — growth drawn from {{growthCount}} revenue-corroborated historical observation(s); terminal yield from {{count}} historical FCF-yield observation(s).",
  "investmentCase.outlook.convictionCaption":
    "Reflects case-wide Conviction, capped when this horizon's own data is insufficient — not an independently modeled Outlook Conviction.",
  "investmentCase.outlook.driver.valuationRerating": "Valuation re-rating",
  "investmentCase.outlook.driver.revenueTrend": "Recent revenue trend",
  "investmentCase.outlook.driver.growth": "Growth",
  "investmentCase.outlook.driver.capitalAllocation": "Capital allocation",
  "investmentCase.outlook.driver.financialRisk": "Financial risk",
  "investmentCase.outlook.driver.businessRisk": "Business risk",
  "investmentCase.outlook.driver.valuationRisk": "Valuation risk",
  "investmentCase.outlook.driver.fcfGrowthTrend": "Recent free cash flow trend",
  "investmentCase.outlook.driver.debtTrend": "Debt trend",
  "investmentCase.outlook.driver.marginTrend": "Operating margin trend",

  // ---------- long-term expected return v1 ----------
  "investmentCase.outlook.growthAssumptionNote":
    "Assumes free cash flow compounds at {{growthRate}} annually for {{years}} years, drawn from this company's own realized history, then the market re-rates to a {{targetYield}} FCF yield — not a forecast of future business performance.",
  "investmentCase.outlook.scenarioGrowthAssumptionNote":
    "Assumes {{growthRate}} annual free cash flow growth and a {{targetYield}} terminal FCF yield.",

  // ---------- long-term expected return calibration sprint ----------
  "investmentCase.outlook.growthBullCaseLabel": "Business-Growth Bull",
  "investmentCase.outlook.growthBaseCaseLabel": "Business-Growth Base",
  "investmentCase.outlook.growthBearCaseLabel": "Business-Growth Bear",
  "investmentCase.outlook.expectedReturnLabel.growth": "Expected Return Range",

  // ---------- investment case figma-fidelity rebuild: investment argument ----------
  "investmentCase.argument.heading": "Investment Argument",
  "investmentCase.argument.supportsHeading": "Supports the Case",
  "investmentCase.argument.challengesHeading": "Challenges the Case",
  "investmentCase.argument.supportsEmpty": "Nothing has been classified as a supporting factor yet.",
  "investmentCase.argument.challengesEmpty": "Nothing has been classified as a challenging factor yet.",
  "investmentCase.argument.supports.growth": "Growth trends are strong enough to support the case.",
  "investmentCase.argument.supports.capital_allocation":
    "Capital allocation has been disciplined enough to support the case.",
  "investmentCase.argument.supports.valuation": "Today's valuation supports the case rather than working against it.",
  "investmentCase.argument.challenges.growth": "Weakening growth works against the case.",
  "investmentCase.argument.challenges.capital_allocation":
    "Capital allocation is currently working against shareholders, which works against the case.",
  "investmentCase.argument.challenges.valuation":
    "Today's valuation looks expensive relative to this company's own history, which works against the case.",
  "investmentCase.argument.challenges.business_risk": "An identified business risk works against the case.",
  "investmentCase.argument.challenges.financial_risk": "An identified financial risk works against the case.",
  "investmentCase.argument.challenges.valuation_risk": "An identified valuation risk works against the case.",

  // ---------- investment case figma-fidelity rebuild: atlas reasoning ----------
  "investmentCase.reasoning.heading": "Atlas Reasoning",
  "investmentCase.reasoning.growthLabel": "Growth",
  "investmentCase.reasoning.valuationLabel": "Valuation",
  "investmentCase.reasoning.financialHealthLabel": "Financial Health",
  "investmentCase.reasoning.businessQualityLabel": "Business Quality",
  "investmentCase.reasoning.notYetEvaluated": "Not yet evaluated.",
  "investmentCase.reasoning.growth.strong": "Growth is strong and supports the case.",
  "investmentCase.reasoning.growth.moderate": "Growth is moderate — a real but not decisive factor.",
  "investmentCase.reasoning.growth.weak": "Growth is weak and works against the case.",
  "investmentCase.reasoning.valuation.undervalued": "The business appears undervalued at today's price.",
  "investmentCase.reasoning.valuation.fairly_valued": "The business appears fairly valued at today's price.",
  "investmentCase.reasoning.valuation.expensive": "The business appears expensive at today's price.",
  "investmentCase.reasoning.financialHealth.low":
    "Financial risk is low — the balance sheet is not a near-term concern.",
  "investmentCase.reasoning.financialHealth.moderate":
    "Financial risk is moderate — worth monitoring, not yet a concern.",
  "investmentCase.reasoning.financialHealth.high": "Financial risk is high and warrants attention.",
  "investmentCase.reasoning.businessQuality.strong": "Business quality is strong and supports durability.",
  "investmentCase.reasoning.businessQuality.moderate":
    "Business quality is moderate — durability is not yet fully established.",
  "investmentCase.reasoning.businessQuality.weak": "Business quality is weak and raises durability questions.",

  // ---------- investment case figma-fidelity rebuild: company health assessment ----------
  "investmentCase.companyHealth.heading": "Company Health Assessment",
  "investmentCase.companyHealth.businessQualityLabel": "Business Quality",
  "investmentCase.companyHealth.financialStrengthLabel": "Financial Strength",
  "investmentCase.companyHealth.managementGovernanceLabel": "Management & Governance",
  "investmentCase.companyHealth.capitalAllocationLabel": "Capital Allocation",
  "investmentCase.companyHealth.competitivePositionLabel": "Competitive Position",
  "investmentCase.companyHealth.expandLabel": "Show supporting evidence",
  "investmentCase.companyHealth.supportingHeading": "Supporting evidence",
  "investmentCase.companyHealth.contradictingHeading": "Contradicting evidence",
  "investmentCase.companyHealth.missingHeading": "Missing evidence",
  "investmentCase.companyHealth.noneFound": "None recorded.",
  "investmentCase.companyHealth.notYetEvaluated": "Not yet evaluated — the evidence needed hasn't been gathered.",
  "investmentCase.companyHealth.businessQuality.strong": "Business quality looks strong on the evidence gathered so far.",
  "investmentCase.companyHealth.businessQuality.moderate":
    "Business quality looks moderate on the evidence gathered so far.",
  "investmentCase.companyHealth.businessQuality.weak": "Business quality looks weak on the evidence gathered so far.",
  "investmentCase.companyHealth.financialStrength.low": "Financial risk is currently assessed as low.",
  "investmentCase.companyHealth.financialStrength.moderate": "Financial risk is currently assessed as moderate.",
  "investmentCase.companyHealth.financialStrength.high": "Financial risk is currently assessed as high.",
  "investmentCase.companyHealth.management.strong":
    "Management and governance look strong on the evidence gathered so far.",
  "investmentCase.companyHealth.management.moderate":
    "Management and governance look moderate on the evidence gathered so far.",
  "investmentCase.companyHealth.management.weak":
    "Management and governance look weak on the evidence gathered so far.",
  "investmentCase.companyHealth.capitalAllocation.strong":
    "Capital allocation looks strong on the evidence gathered so far.",
  "investmentCase.companyHealth.capitalAllocation.moderate":
    "Capital allocation looks moderate on the evidence gathered so far.",
  "investmentCase.companyHealth.capitalAllocation.weak":
    "Capital allocation looks weak on the evidence gathered so far.",
  "investmentCase.companyHealth.competitivePosition.strong":
    "Competitive position looks strong on the evidence gathered so far.",
  "investmentCase.companyHealth.competitivePosition.moderate":
    "Competitive position looks moderate on the evidence gathered so far.",
  "investmentCase.companyHealth.competitivePosition.weak":
    "Competitive position looks weak on the evidence gathered so far.",

  // ---------- investment case figma-fidelity rebuild: interpreted financial evidence ----------
  "investmentCase.financialEvidence.heading": "Interpreted Financial Evidence",
  "investmentCase.financialEvidence.operatingMarginLabel": "Operating Margin",
  "investmentCase.financialEvidence.detailedFinancialsLabel": "Detailed Financials, Sources & Methodology",
  "investmentCase.financialEvidence.notEnoughHistory": "Not enough history to interpret yet.",
  "investmentCase.financialEvidence.revenue.up": "Revenue is growing — demand continues to expand.",
  "investmentCase.financialEvidence.revenue.down": "Revenue is declining — worth watching for a continued trend.",
  "investmentCase.financialEvidence.revenue.flat": "Revenue is essentially flat versus the prior period.",
  "investmentCase.financialEvidence.operatingMargin.up":
    "Operating margin is expanding — the business is converting revenue into profit more efficiently.",
  "investmentCase.financialEvidence.operatingMargin.down":
    "Operating margin is contracting — profitability is coming under pressure.",
  "investmentCase.financialEvidence.operatingMargin.flat":
    "Operating margin is essentially unchanged versus the prior period.",
  "investmentCase.financialEvidence.freeCashFlow.up":
    "Free cash flow is growing, giving the business more room to invest, return capital, or absorb a downturn.",
  "investmentCase.financialEvidence.freeCashFlow.down":
    "Free cash flow is declining, reducing the business's flexibility.",
  "investmentCase.financialEvidence.freeCashFlow.flat":
    "Free cash flow is essentially unchanged versus the prior period.",
  "investmentCase.financialEvidence.totalDebt.up": "Total debt is rising — worth monitoring alongside cash flow.",
  "investmentCase.financialEvidence.totalDebt.down": "Total debt is declining, a modest positive for the balance sheet.",
  "investmentCase.financialEvidence.totalDebt.flat": "Total debt is essentially unchanged versus the prior period.",

  // ---------- daily brief v2 (Workspace Migration Phase 4) ----------
  "dailyBrief.title": "Daily Brief",
  "dailyBrief.subtitle": "Atlas morning brief for your attention.",
  "dailyBrief.lastUpdated": "Last updated {{time}}",
  "dailyBrief.entry.unknownCompany": "Unknown company",
  "dailyBrief.entry.openInvestmentCase": "Open Investment Case",
  "dailyBrief.priorities.heading": "Today's Priorities",
  "dailyBrief.priorities.empty": "Nothing needs your attention right now.",
  "dailyBrief.priorities.reviewButton": "Review",
  "dailyBrief.priorities.goToPortfolioButton": "Go to Portfolio",
  "dailyBrief.portfolioChanges.heading": "Portfolio Changes",
  "dailyBrief.portfolioChanges.empty": "No portfolio holdings have a meaningful change to review.",
  "dailyBrief.watchlistUpdates.heading": "Watchlist Updates",
  "dailyBrief.watchlistUpdates.empty": "No watchlist entries have a meaningful change to review.",

  // ---------- discovery v1 implementation sprint ----------
  "discovery.title": "Discovery",
  "discovery.workingOnBehalf": "Atlas has been working on your behalf.",
  "discovery.whatFound.heading": "What Atlas Found",
  "discovery.whatFound.empty": "No new analytical findings since your last visit.",
  "discovery.watchlistUpdates.heading": "Watchlist Updates",
  "discovery.watchlistUpdates.empty": "No watchlist entries have a meaningful change to review.",
  "discovery.reviewCompany.heading": "Review a company",
  "discovery.reviewCompany.createCase": "Create Investment Case →",
  "discovery.reviewCompany.openCase": "Open Investment Case →",
  "discovery.reviewCompany.notInPortfolio":
    "{{ticker}} is not in your current portfolio yet. Atlas cannot create a linked Investment Case for a company you don't hold.",
  "discovery.reviewCompany.error": "Could not create the Investment Case: {{message}}",

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

  // ---------- Atlas Companion (persistent cross-workspace conversational layer) ----------
  "companion.toggle.openLabel": "Open Atlas",
  "companion.toggle.closeLabel": "Close Atlas",
  "companion.panel.title": "Atlas Companion",
  "companion.role.user": "You",
  "companion.role.atlas": "Atlas",
  "companion.context.discussing": "Discussing: {{subject}}",
  "companion.context.portfolioWide": "Portfolio-wide",
  "companion.context.changed": "Context changed: {{from}} → {{to}}",
  "companion.input.placeholder": "Message Atlas…",
  "companion.input.send": "Send",
  "companion.sending": "Atlas is responding…",
  "companion.notConfigured": "Atlas Companion isn't connected in this Alpha yet.",
  "companion.providerError": "Atlas couldn't respond just now — try asking again.",
  "companion.outcome.opened": "Opened the existing Investment Case for {{ticker}}.",
  "companion.outcome.created": "Created a new Investment Case for {{ticker}}.",
  "companion.outcome.unresolved":
    "{{ticker}} isn't in your current portfolio, so Atlas couldn't open a linked Investment Case for it.",
  "companion.outcome.failed": "Atlas couldn't create the Investment Case for {{ticker}} just now. Try asking again.",

  // ---------- company workspace (Company Workspace v1) ----------
  "companyWorkspace.breadcrumbPortfolio": "Portfolio",
  "companyWorkspace.notFound": "Atlas doesn't have this company in your Portfolio or Watchlist yet.",
  "companyWorkspace.loadError": "Could not load this company's workspace.",
  "companyWorkspace.backToPortfolio": "← Back to Portfolio",
  "companyWorkspace.dismissButton": "Dismiss",
  "companyWorkspace.dismissUnavailable": "Not yet available",
  "companyWorkspace.header.positionValue": "Position value",
  "companyWorkspace.header.positionWeight": "Portfolio weight",
  "companyWorkspace.header.notHeld": "Not currently held",
  "companyWorkspace.header.lastUpdated": "Analysis last updated {{when}}",
  "companyWorkspace.currentPicture.heading": "Current Picture",
  "companyWorkspace.thesis.heading": "Investment Thesis",
  "companyWorkspace.thesis.empty": "No recorded thesis yet for this company.",
  "companyWorkspace.thesis.viewFull": "View full thesis",
  "companyWorkspace.decisionSupport.heading": "Decision Support",
  "companyWorkspace.decisionSupport.viewFull": "View full Decision Support",
  "companyWorkspace.decisionSupport.supportingHeading": "Supports the current thesis",
  "companyWorkspace.decisionSupport.disclaimer": "This records your intent — Atlas never executes or simulates a trade.",
  "companyWorkspace.decisionSupport.recordButton": "Record a Decision",
  "companyWorkspace.risk.heading": "Risk",
  "companyWorkspace.evidence.heading": "Evidence & Coverage",
  "companyWorkspace.evidence.qualityLabel": "Evidence quality",
  "companyWorkspace.evidence.coverageLabel": "Evidence coverage",
  "companyWorkspace.evidence.analysisCoverageLabel": "Analysis coverage",
  "companyWorkspace.evidence.missingLabel": "Open questions",
  "companyWorkspace.evidence.viewMissing": "View open questions",
  "companyWorkspace.recentActivity.heading": "Recent Activity",
  "companyWorkspace.recentActivity.empty": "No recent activity recorded for this company.",
  "companyWorkspace.notYetAnalyzed.heading": "Atlas hasn't gathered company data yet",
  "companyWorkspace.notYetAnalyzed.explanation":
    "This can happen right after adding a new holding or watchlist entry, or if automatic enrichment hasn't completed yet.",
  "companyWorkspace.notYetAnalyzed.knownHeading": "What Atlas knows so far",
  "companyWorkspace.notYetAnalyzed.knownTicker": "Ticker: {{ticker}}",
  "companyWorkspace.notYetAnalyzed.knownWeight": "Portfolio weight: {{percent}}%",
  "companyWorkspace.notYetAnalyzed.missingHeading": "What's not yet available",
  "companyWorkspace.notYetAnalyzed.missingBody": "Company profile, financial history, valuation, and risk analysis.",
  "companyWorkspace.notYetAnalyzed.nextSteps": "Reload this page in a little while to check for updates.",
} as const;

export type TranslationKey = keyof typeof en;
