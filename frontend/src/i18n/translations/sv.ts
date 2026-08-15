import type { TranslationKey } from "./en";

/**
 * Swedish translation dictionary. Typed as `Record<TranslationKey, string>`
 * against `en.ts`'s own key set, so a key added to English and forgotten
 * here fails the build rather than silently falling back — the same
 * completeness guarantee any future third language gets for free.
 *
 * Swedish is Atlas Alpha's default language (its first investors are
 * primarily Swedish); English remains the language the application
 * thinks in internally (enums, models, prompts, engineering terms) per
 * `frontend/src/i18n/LanguageContext.tsx` — this file translates only
 * what an investor reads on screen.
 */
export const sv: Record<TranslationKey, string> = {
  // ---------- common ----------
  "common.loading": "Läser in…",
  "common.saving": "Sparar…",
  "common.submit": "Skicka in",
  "common.submitting": "Skickar in…",
  "common.cancel": "Avbryt",
  "common.delete": "Ta bort",
  "common.deleting": "Tar bort…",
  "common.addAnother": "Lägg till en till",
  "common.unknownError": "Okänt fel",
  "common.invalidInput": "Ogiltig inmatning.",

  // ---------- shared form field labels ----------
  "form.ticker": "Ticker",
  "form.weightPercent": "Andel %",
  "form.valueOptional": "Värde (valfritt)",
  "form.cashPercent": "Kontanter %",
  "form.cashValueOptional": "Kontantvärde (valfritt)",
  "form.preferencesOptional": "Preferenser (valfritt)",
  "form.removeButton": "Ta bort",

  // ---------- application shell ----------
  "shell.header.brand": "Atlas",
  "shell.header.languageAriaLabel": "Välj språk",
  "shell.nav.ariaLabel": "Huvudnavigering",
  "shell.nav.dashboard": "Översikt",
  "shell.nav.portfolio": "Portfölj",
  "shell.notFound.title": "Sidan hittades inte",
  "shell.notFound.body": "Det finns ingen sida på den här adressen.",
  "shell.error.title": "Något gick fel",

  // ---------- index route ----------
  "indexRoute.error": "Kunde inte nå Atlas: {{message}}",

  // ---------- welcome ----------
  "welcome.title": "Välkommen till Atlas",
  "welcome.choice.prompt": "Hur vill du börja?",
  "welcome.choice.haveExisting": "Jag har en befintlig portfölj",
  "welcome.choice.startFromScratch": "Börja från grunden",
  "welcome.continueButton": "Fortsätt till portföljen",
  "welcome.backButton": "Tillbaka",
  "welcome.import.heading": "Din befintliga portfölj",
  "welcome.import.instructions":
    "Ange varje innehav som en andel av din portfölj. Exakta värden är valfria.",
  "welcome.import.addHoldingButton": "+ Lägg till innehav",
  "welcome.import.errors.noHoldings": "Ange minst ett innehav.",
  "welcome.import.errors.missingPercentage": "Alla innehav behöver en andel i procent.",
  "welcome.import.errors.invalidValueFor": '"{{value}}" är inte ett giltigt värde för {{ticker}}.',
  "welcome.import.errors.duplicateTickers": "Dubblerad(e) ticker: {{tickers}}.",
  "welcome.import.errors.invalidCashPercent": '"{{value}}" är inte en giltig andel kontanter.',
  "welcome.import.errors.invalidCashValue": '"{{value}}" är inte ett giltigt kontantvärde.',
  "welcome.import.errors.cashBothOrNeither":
    "Ange både kontanter i procent och kontantvärde, eller lämna båda tomma.",
  "welcome.import.errors.saveFailed": "Kunde inte spara portföljen: {{message}}",
  "welcome.scratch.heading": "Börja från grunden",
  "welcome.scratch.objectiveLabel": "Investeringsmål",
  "welcome.scratch.horizonLabel": "Investeringshorisont",
  "welcome.scratch.errors.required": "Både mål och horisont krävs.",
  "welcome.scratch.errors.saveFailed": "Kunde inte spara: {{message}}",

  // ---------- portfolio ----------
  "portfolio.title": "Portfölj",
  "portfolio.loadError": "Kunde inte läsa in din portfölj: {{message}}",
  "portfolio.notEstablished": "Ingen portfölj har skapats ännu.",
  "portfolio.setupLink": "Skapa din portfölj",
  "portfolio.empty.title": "Din portfölj är tom.",
  "portfolio.empty.objective": "Mål: {{value}}",
  "portfolio.empty.horizon": "Horisont: {{value}}",
  "portfolio.empty.explanation":
    "Det finns inget att visa här än — Atlas hittar inte på innehav eller möjligheter. När du öppnar Investeringscase och registrerar beslut kommer de att visas här.",
  "portfolio.openNewCase": "Öppna ett nytt Investeringscase",
  "portfolio.awaitingBanner.title": "Affär registrerad. Fördelningen behöver stämmas av.",
  "portfolio.awaitingBanner.body":
    "Ett eller flera innehav handlades medan Atlas endast kände till procentandelar, så fördelningen lämnades orörd i stället för att gissas fram. Uppdatera det berörda innehavet nedan, eller ersätt hela fördelningen.",
  "portfolio.replaceAllocationButton": "Ersätt hela fördelningen",
  "portfolio.replaceForm.heading": "Ersätt hela fördelningen",
  "portfolio.replaceForm.saveButton": "Spara fördelning",
  "portfolio.replaceForm.errors.invalidPercentage": "Alla innehav behöver en giltig andel i procent.",
  "portfolio.holdings.heading": "Innehav",
  "portfolio.holdings.percentOnly":
    "Visar endast procentandelar — inget totalt portföljvärde har angetts.",
  "portfolio.holdings.totalValue": "Totalt värde: {{value}}",
  "portfolio.holdings.updatedAutomatically": "Uppdaterad automatiskt",
  "portfolio.holdings.awaitingReconciliation": "Väntar på avstämning",
  "portfolio.holdings.newWeightLabel": "Ny andel %",
  "portfolio.holdings.updateButton": "Uppdatera detta innehav",
  "portfolio.holdings.updating": "Uppdaterar…",
  "portfolio.holdings.openCaseButton": "Öppna Investeringscase",
  "portfolio.holdings.opening": "Öppnar…",
  "portfolio.holdings.openCaseError": "Kunde inte öppna ett Investeringscase.",
  "portfolio.holdings.errors.invalidPercentage": "Ange en giltig andel i procent.",
  // ---------- portfolio cockpit (ATLAS-028) ----------
  "portfolio.cockpit.conviction.label": "Övertygelse",
  "portfolio.cockpit.conviction.very_high": "Mycket hög",
  "portfolio.cockpit.conviction.high": "Hög",
  "portfolio.cockpit.conviction.moderate": "Måttlig",
  "portfolio.cockpit.conviction.low": "Låg",
  "portfolio.cockpit.conviction.insufficient_evidence": "Otillräckligt underlag",
  // ---------- Internal Alpha Fix Sprint 1: Analysis Coverage (IA-003) ----------
  "portfolio.cockpit.analysisCoverage.label": "Analystäckning",
  "portfolio.cockpit.analysisCoverage.no_coverage": "Ingen täckning",
  "portfolio.cockpit.analysisCoverage.partial_coverage": "Delvis",
  "portfolio.cockpit.analysisCoverage.substantial_coverage": "Omfattande",
  "portfolio.cockpit.valuation.label": "Värdering",
  "portfolio.cockpit.valuation.not_evaluated": "Inte utvärderad",
  "portfolio.cockpit.valuation.insufficient_input": "Otillräckligt underlag",
  "portfolio.cockpit.valuation.undervalued": "Undervärderad",
  "portfolio.cockpit.valuation.fairly_valued": "Rimligt värderad",
  "portfolio.cockpit.valuation.expensive": "Dyr",
  "portfolio.cockpit.risk.label": "Risk",
  "portfolio.cockpit.risk.status.not_evaluated": "Inte utvärderad",
  "portfolio.cockpit.risk.status.insufficient_input": "Otillräckligt underlag",
  "portfolio.cockpit.risk.status.low": "Låg",
  "portfolio.cockpit.risk.status.moderate": "Måttlig",
  "portfolio.cockpit.risk.status.high": "Hög",
  "portfolio.cockpit.risk.category.business_risk": "Verksamhet",
  "portfolio.cockpit.risk.category.financial_risk": "Finansiell",
  "portfolio.cockpit.risk.category.valuation_risk": "Värdering",
  "portfolio.cockpit.risk.category.thesis_risk": "Tes",
  "portfolio.cockpit.business.growthLabel": "Tillväxt",
  "portfolio.cockpit.business.capitalAllocationLabel": "Kapitalallokering",
  "portfolio.cockpit.business.not_evaluated": "Inte utvärderad",
  "portfolio.cockpit.business.insufficient_input": "Otillräckligt underlag",
  "portfolio.cockpit.business.weak": "Svag",
  "portfolio.cockpit.business.moderate": "Måttlig",
  "portfolio.cockpit.business.strong": "Stark",
  "portfolio.cockpit.evidenceLabel": "Underlag",
  "portfolio.cockpit.review.none": "—",
  "portfolio.cockpit.review.standard_review": "Standardgranskning",
  "portfolio.cockpit.review.evidence_review": "Underlagsgranskning",
  "portfolio.cockpit.review.priority_review": "Prioriterad granskning",
  "portfolio.cockpit.viewCaseButton": "Visa Investeringscase",
  "portfolio.cockpit.unresolved": "Investeringscase kunde inte hämtas",
  "portfolio.holdingsTable.rowAriaLabel": "Visa Investeringscase för {{ticker}}",

  "portfolio.unallocated":
    "Ofördelat: {{percent}}% — den här portföljen täcker ännu inte 100% av innehaven; Atlas hittar inte på resten.",
  "portfolio.concentration": "Koncentration: {{value}}",
  "portfolio.concentrationLevel.low": "Låg",
  "portfolio.concentrationLevel.moderate": "Måttlig",
  "portfolio.concentrationLevel.elevated": "Förhöjd",
  "portfolio.concentrationLevel.high": "Hög",

  // ---------- portfolio header bar (Figma-fidelity rebuild) ----------
  "portfolio.header.holdings": "Innehav",
  "portfolio.header.cash": "Kontanter",
  "portfolio.header.unallocated": "Oallokerat",
  "portfolio.header.expectedReturn": "Förväntad avkastning",
  "portfolio.header.actionRequired": "{{count}} åtgärd(er) krävs",
  "portfolio.header.notAvailable": "—",
  "portfolio.summary.unknownInstrumentsWarning": "{{count}} innehav kunde inte tolkas fullt ut. Granska instrumenten.",

  // ---------- portfolio priority strip (Figma-fidelity rebuild) ----------
  "portfolio.priorityStrip.empty": "Inget behöver din uppmärksamhet just nu.",
  "portfolio.priorityStrip.reviewTitle": "Granska {{ticker}}",
  "portfolio.priorityStrip.completeEvidenceTitle": "Komplettera belägg för {{ticker}}",
  "portfolio.priorityStrip.concentrationTitle": "Granska koncentrationen i {{ticker}}",
  "portfolio.priorityStrip.allocationTitle": "Granska portföljens allokering",
  "portfolio.priorityStrip.evidenceReason": "Belägg saknas.",
  "portfolio.priorityStrip.allocationReason": "{{percent}}% är för närvarande oallokerat.",
  "portfolio.priorityStrip.reason.missingCase": "Inget investeringscase än.",
  "portfolio.priorityStrip.reason.decisionWithoutOutcome": "Beslutet saknar rapporterat utfall.",
  "portfolio.priorityStrip.reason.outcomeWithoutExecution": "Utfallet saknar bekräftat genomförande.",
  "portfolio.priorityStrip.reason.awaitingReconciliation": "Väntar på avstämning efter en affär.",
  "portfolio.priorityStrip.reason.veryOldCase": "Investeringscaset är {{days}} dagar gammalt.",
  "portfolio.priorityStrip.reason.observationWithoutDecision": "En observation saknar beslut.",
  "portfolio.priorityStrip.reviewButton": "Granska",
  "portfolio.priorityStrip.openCaseButton": "Öppna case",
  "portfolio.priorityStrip.viewAll": "Visa alla {{count}}",
  "portfolio.priorityStrip.viewFewer": "Visa färre",

  // ---------- holdings table (Figma-fidelity rebuild) ----------
  "portfolio.holdingsTable.tickerHeader": "Ticker",
  "portfolio.holdingsTable.weightHeader": "Andel",
  "portfolio.holdingsTable.convictionHeader": "Övertygelse",
  "portfolio.holdingsTable.fitHeader": "Passform",
  "portfolio.holdingsTable.expReturnHeader": "Förv. avkastning",
  "portfolio.holdingsTable.upsideHeader": "Uppsida",
  "portfolio.holdingsTable.downsideHeader": "Nedsida",
  "portfolio.holdingsTable.riskHeader": "Risk",
  "portfolio.holdingsTable.actionHeader": "Åtgärd",
  "portfolio.holdingsTable.reconcileToggle": "Stäm av",
  "portfolio.holdingsTable.showingCount": "Visar {{shown}} av {{total}}",
  "portfolio.holdingsTable.viewAll": "Visa alla innehav ({{count}})",
  "portfolio.holdingsTable.viewFewer": "Visa färre",

  // ---------- portfolio intelligence panels (Figma-fidelity rebuild) ----------
  "portfolio.keyFindingsPanel.heading": "Viktiga observationer",
  "portfolio.keyFindingsPanel.empty": "Inga anmärkningsvärda observationer just nu.",
  "portfolio.riskSignalsPanel.heading": "Risksignaler",
  "portfolio.riskSignalsPanel.empty": "Inga risksignaler just nu.",
  "portfolio.riskSignalsPanel.missingEvidenceCount": "{{count}} innehav saknar belägg.",
  "portfolio.riskSignals.high_concentration": "{{ticker}} är en koncentrerad position.",
  "portfolio.riskSignals.missing_case": "{{ticker}} har inget investeringscase än.",
  "portfolio.riskSignals.missing_evidence": "{{ticker}} saknar belägg.",
  "portfolio.riskSignals.awaiting_reconciliation": "{{ticker}} väntar på avstämning efter en affär.",
  "portfolio.riskSignals.stale_review": "{{ticker}} har inte granskats på länge.",

  // ---------- discussion prompts (Workspace Migration Phase 2: the
  // page-local "Today's Discussions" Ask box itself was removed --
  // Decision Log #2 -- these remain only as `deriveDiscussionPrompts.ts`'s
  // own real candidate input for the future Atlas Companion, plus one
  // key still shared with Investment Case's own placeholder note) ----------
  "portfolio.discussions.comingSoonNote":
    "Samtal med Atlas är inte tillgängliga än — detta är förberett för en framtida version.",
  "portfolio.discussions.prompt.priorityHolding":
    "{{ticker}} är just nu ditt högst prioriterade innehav. Vill du granska det?",
  "portfolio.discussions.prompt.diversification":
    "Din portfölj är spridd över {{count}} innehav med låg koncentration. Skulle en koncentration mot dina mest övertygande idéer förbättra den förväntade avkastningen?",
  "portfolio.discussions.prompt.concentration":
    "{{ticker}} utgör en stor del av din portfölj. Skulle en minskning av positionen förbättra diversifieringen?",
  "portfolio.discussions.prompt.unallocated":
    "{{percent}}% av ditt kapital är för närvarande oallokerat. Var bör detta kapital placeras?",
  "portfolio.discussions.prompt.evidenceGaps":
    "{{count}} innehav har luckor i sina belägg. Vill du granska vad som saknas?",
  "portfolio.discussions.prompt.staleCases":
    "{{count}} investeringscase har inte granskats på länge. Vill du gå igenom dem?",
  "portfolio.discussions.prompt.missingCases":
    "{{count}} innehav saknar fortfarande ett investeringscase. Vill du starta ett?",

  // ---------- portfolio intelligence (ATLAS-016) ----------
  "portfolio.intelligence.confidence.not_applicable": "Otillräckligt underlag",
  "portfolio.intelligence.confidence.none": "Inga belägg registrerade",
  "portfolio.intelligence.confidence.partial": "Delvisa belägg",
  "portfolio.intelligence.confidence.full": "Fullständig belägg­täckning",

  "portfolio.intelligence.keyFindings.high_concentration":
    "Hög koncentration i ditt största innehav ({{tickers}})",
  "portfolio.intelligence.keyFindings.elevated_concentration":
    "Förhöjd koncentration i ditt största innehav ({{tickers}})",
  "portfolio.intelligence.keyFindings.large_unallocated": "En betydande del av portföljen är oallokerad",
  "portfolio.intelligence.keyFindings.multiple_missing_cases":
    "{{count}} innehav saknar fortfarande investeringscase ({{tickers}})",
  "portfolio.intelligence.keyFindings.multiple_stale_cases":
    "{{count}} investeringscase har inte granskats på länge ({{tickers}})",
  "portfolio.intelligence.keyFindings.multiple_evidence_gaps":
    "{{count}} innehav har luckor i beläggen för sitt investeringscase ({{tickers}})",

  // ---------- dashboard ----------
  "dashboard.title": "Översikt",
  "dashboard.portfolioStatus.heading": "Portföljstatus",
  "dashboard.portfolioStatus.loadError": "Kunde inte läsa in portföljstatus: {{message}}",
  "dashboard.portfolioStatus.notEstablished": "Ingen portfölj skapad ännu.",
  "dashboard.portfolioStatus.setupCta": "Skapa portfölj →",
  "dashboard.portfolioStatus.holdingSingular": "innehav",
  "dashboard.portfolioStatus.holdingPlural": "innehav",
  "dashboard.portfolioStatus.summary": "{{count}} {{holdingWord}}",
  "dashboard.portfolioStatus.cashSuffix": " — {{percent}}% kontanter",
  "dashboard.portfolioStatus.goToPortfolio": "Gå till portföljen →",
  "dashboard.monitoring.heading": "Aktiva bevakningsvillkor",
  "dashboard.notYetImplemented": "Ännu inte implementerat.",
  "dashboard.recentDecisions.heading": "Senaste besluten",
  "dashboard.recentDecisions.loadError": "Kunde inte läsa in senaste besluten: {{message}}",
  "dashboard.recentDecisions.empty": "Inga beslut registrerade ännu.",
  "dashboard.outcomes.heading": "Utfall",
  "dashboard.outcomes.loadError": "Kunde inte läsa in utfall: {{message}}",
  "dashboard.outcomes.empty": "Inga utfall registrerade ännu.",
  "dashboard.tradeExecutions.heading": "Genomförda affärer",
  "dashboard.tradeExecutions.loadError": "Kunde inte läsa in genomförda affärer: {{message}}",
  "dashboard.tradeExecutions.empty": "Inga affärer registrerade ännu.",
  "dashboard.signals.heading": "Signaler",
  "dashboard.workspaces.heading": "Arbetsytor",
  "dashboard.workspaces.empty": "Inga aktiva arbetsytor ännu.",

  // ---------- investment case: shell ----------
  "investmentCase.heading": "Investeringscase",
  "investmentCase.returnTo.dashboard": "← Tillbaka till Översikt",
  "investmentCase.returnTo.history": "← Tillbaka till Historik",
  "investmentCase.returnTo.portfolio": "← Tillbaka till Portfölj",
  "investmentCase.returnTo.dailyBrief": "← Tillbaka till Dagens genomgång",
  "investmentCase.returnTo.discovery": "← Tillbaka till Discovery",
  "investmentCase.noCaseSelected": "Inget case valt.",
  "investmentCase.loadError": "Kunde inte läsa in caset: {{message}}",
  "investmentCase.subject": "Ämne: Case {{caseId}}",
  "investmentCase.status.heading": "Status",
  "investmentCase.status.healthy": "Frisk",
  "investmentCase.status.needsReview": "Behöver granskning",
  "investmentCase.status.highPriority": "Hög prioritet",
  "investmentCase.primaryWorkArea.heading": "Primärt arbetsområde",
  "investmentCase.timeline.heading": "Tidslinje",
  "investmentCase.timeline.placeholder":
    "Reserverad för beslutets egen tidslinje i en framtida version.",
  "investmentCase.footer.heading": "Sidfot",

  // ---------- investment case: canonical analysis (ATLAS-029) ----------
  "investmentCase.analysis.conviction.heading": "Övertygelse",
  "investmentCase.analysis.conviction.reasonsHeading": "Varför",
  "investmentCase.analysis.confidence.heading": "Underlag",
  "investmentCase.analysis.confidence.explanation": "Hur väl de registrerade observationerna för det här caset stöds av underlag.",
  "investmentCase.analysis.thesis.heading": "Nuvarande tes",
  "investmentCase.analysis.thesis.investorDecisionReason": "Investerarens angivna skäl (senaste beslutet)",
  "investmentCase.analysis.thesis.investorObservation": "Investerarens senaste observation",
  "investmentCase.analysis.thesis.none": "Ingen tes registrerad ännu — inget beslut eller ingen observation har gjorts för det här caset.",
  "investmentCase.analysis.thesis.stale": "Den här tesen har inte granskats på länge.",
  "investmentCase.atlasView.heading": "Atlas syn",
  "investmentCase.atlasView.thesis.heading": "Nuvarande case",
  "investmentCase.atlasView.strengths.heading": "Styrkor",
  "investmentCase.atlasView.strengths.empty": "Atlas har inte identifierat någon tydlig styrka ännu.",
  "investmentCase.atlasView.risks.heading": "Risker",
  "investmentCase.atlasView.risks.empty": "Atlas har inte identifierat någon tydlig risk ännu.",
  "investmentCase.atlasView.growth.heading": "Tillväxt",
  "investmentCase.atlasView.growth.recentTrendLabel": "Senaste perioderna ({{periods}})",
  "investmentCase.atlasView.growth.trend.strong_metric": "genomgående ökande",
  "investmentCase.atlasView.growth.trend.weak_metric": "genomgående minskande",
  "investmentCase.atlasView.growth.trend.mixed_metric": "blandad, med både ökningar och minskningar",
  "investmentCase.atlasView.valuationContext.heading": "Värdering",
  "investmentCase.atlasView.valuationContext.currentYieldLabel": "Nuvarande FCF-avkastning",
  "investmentCase.atlasView.valuationContext.scenarioUnavailable": "Atlas har ännu inte tillräckligt scenariobaserat värderingsstöd för att avgöra om det aktuella priset ger attraktiv förväntad avkastning.",
  "investmentCase.atlasView.openQuestions.heading": "Öppna frågor",
  "investmentCase.atlasView.openQuestions.empty": "Inga öppna frågor identifierade för det här caset just nu.",
  "investmentCase.atlasView.openQuestions.growth_inconclusive": "Växer det här företaget verkligen? Atlas har ännu inte tillräcklig intäkts- eller kassaflödeshistorik för att avgöra det.",
  "investmentCase.atlasView.openQuestions.growth_mixed": "Är den senaste tillväxten hållbar, eller var den tillfällig?",
  "investmentCase.atlasView.openQuestions.capital_allocation_inconclusive": "Hur allokeras kapital? Atlas har ännu inte tillräcklig data om återköp, nyemission eller skuld.",
  "investmentCase.atlasView.openQuestions.capital_allocation_weak": "Är den nuvarande kapitalallokeringen (utspädning eller ökande skuldsättning) tillfällig eller varaktig?",
  "investmentCase.atlasView.openQuestions.valuation_inconclusive": "Är det aktuella priset billigt eller dyrt? Atlas har ännu inte tillräcklig historisk värderingsdata för att avgöra det.",
  "investmentCase.atlasView.openQuestions.valuation_expensive_versus_growth": "Diskonterar det aktuella priset redan den tillväxt Atlas ser?",
  "investmentCase.atlasView.openQuestions.scenario_valuation_unavailable": "Ger det aktuella priset attraktiv förväntad avkastning under uttryckliga framtidsantaganden? Atlas stöder ännu inte scenariobaserad värdering.",
  "investmentCase.atlasView.highlight.valuation": "Pris kontra historik",
  "investmentCase.atlasView.notAvailable": "—",
  "investmentCase.atlasView.dimension.businessStrength": "Verksamhetens styrka",
  "investmentCase.atlasView.dimension.growth": "Tillväxt",
  "investmentCase.atlasView.dimension.valuation": "Värdering",
  "investmentCase.atlasView.dimension.riskLevel": "Risknivå",
  "investmentCase.atlasView.dimension.capitalAllocation": "Kapitalallokering",
  "investmentCase.atlasView.dimension.expectedReturn": "Förväntad avkastning",
  "investmentCase.atlasView.dimension.portfolioFit": "Portföljpassform",
  "investmentCase.whatChanged.heading": "Vad som ändrats",
  "investmentCase.whatChanged.baseline": "Atlas har etablerat en baslinje för det här caset. Framtida analyser jämförs mot den.",
  "investmentCase.whatChanged.noChange": "Ingen väsentlig förändring sedan föregående analys.",
  "investmentCase.whatChanged.sincePrevious": "Sedan föregående analys:",
  "investmentCase.whatChanged.thesisImpact.strengthened": "Sammantaget har Atlas tes stärkts.",
  "investmentCase.whatChanged.thesisImpact.weakened": "Sammantaget har Atlas tes försvagats, men kvarstår intakt.",
  "investmentCase.whatChanged.thesisImpact.mixed": "Caset visar blandade signaler, men Atlas övergripande tes kvarstår intakt.",
  "investmentCase.whatChanged.thesisImpact.unchanged": "Atlas tes är oförändrad i sak.",
  "investmentCase.whatChanged.verb.improved": "förbättrades",
  "investmentCase.whatChanged.verb.weakened": "försvagades",
  "investmentCase.whatChanged.verb.increased": "ökade",
  "investmentCase.whatChanged.verb.decreased": "minskade",
  "investmentCase.whatChanged.verb.moreAttractive": "mer attraktiv",
  "investmentCase.whatChanged.verb.lessAttractive": "mindre attraktiv",
  "investmentCase.whatChanged.change.dimensionChanged": "{{dimension}} {{verb}} från {{previous}} till {{current}}.",
  "investmentCase.whatChanged.change.valuationChanged": "Värderingen blev {{verb}}.",
  "investmentCase.whatChanged.change.coverageGained": "Atlas kan nu utvärdera {{dimension}} efter att ny data blivit tillgänglig.",
  "investmentCase.whatChanged.change.coverageLost": "Atlas kan inte längre utvärdera {{dimension}} — underliggande data finns inte längre tillgänglig.",
  "investmentCase.whatChanged.change.strengthAdded": "Ny styrka identifierad: {{label}}.",
  "investmentCase.whatChanged.change.strengthRemoved": "{{label}} klassas inte längre som en styrka.",
  "investmentCase.whatChanged.change.riskAdded": "Ny risk identifierad: {{label}}.",
  "investmentCase.whatChanged.change.riskRemoved": "{{label}} klassas inte längre som en risk.",
  "investmentCase.whatChanged.change.openQuestionAdded": "En ny öppen fråga har uppstått.",
  "investmentCase.whatChanged.change.openQuestionResolved": "En tidigare öppen fråga har besvarats.",
  "investmentCase.analysis.companyOverview.heading": "Företagsöversikt",
  "investmentCase.analysis.companyOverview.exchangeLabel": "Börs",
  "investmentCase.analysis.companyOverview.sectorLabel": "Sektor",
  "investmentCase.analysis.companyOverview.industryLabel": "Bransch",
  "investmentCase.analysis.companyOverview.countryLabel": "Land",
  "investmentCase.analysis.companyOverview.fiscalYearEndLabel": "Räkenskapsårets slut",
  "investmentCase.analysis.companyOverview.foundedLabel": "Grundat",
  "investmentCase.analysis.companyOverview.ceoLabel": "VD",
  "investmentCase.analysis.companyOverview.employeesLabel": "Anställda",
  "investmentCase.analysis.companyOverview.empty": "Ännu inte identifierat",
  "investmentCase.analysis.financials.heading": "Finansiell information",
  "investmentCase.analysis.financials.unknownPeriodLabel": "Okänd period",
  "investmentCase.analysis.financials.revenueLabel": "Intäkter",
  "investmentCase.analysis.financials.operatingIncomeLabel": "Rörelseresultat",
  "investmentCase.analysis.financials.netIncomeLabel": "Nettoresultat",
  "investmentCase.analysis.financials.epsLabel": "Vinst per aktie (utspädd)",
  "investmentCase.analysis.financials.freeCashFlowLabel": "Fritt kassaflöde",
  "investmentCase.analysis.financials.capitalExpenditureLabel": "Investeringar",
  "investmentCase.analysis.financials.shareBuybacksLabel": "Återköp av aktier",
  "investmentCase.analysis.financials.dividendsLabel": "Utdelningar",
  "investmentCase.analysis.financials.cashLabel": "Kassa och likvida medel",
  "investmentCase.analysis.financials.totalDebtLabel": "Total skuld",
  "investmentCase.analysis.financials.marketSnapshotHeading": "Aktuell marknadsdata",
  "investmentCase.analysis.financials.sharePriceLabel": "Aktiekurs",
  "investmentCase.analysis.financials.sharesOutstandingLabel": "Utestående aktier",
  "investmentCase.analysis.financials.marketCapLabel": "Börsvärde",
  "investmentCase.analysis.financials.empty": "Ännu inte tillgängligt",
  "investmentCase.analysis.business.heading": "Verksamhetsanalys",
  "investmentCase.analysis.business.category.business_model": "Affärsmodell",
  "investmentCase.analysis.business.category.competitive_position": "Konkurrensposition",
  "investmentCase.analysis.business.category.management": "Ledning",
  "investmentCase.analysis.business.category.capital_allocation": "Kapitalallokering",
  "investmentCase.analysis.business.category.growth": "Tillväxt",
  "investmentCase.analysis.business.category.durability": "Uthållighet",
  "investmentCase.analysis.business.supportingLabel": "Stödjande",
  "investmentCase.analysis.business.contradictingLabel": "Motsägande",
  "investmentCase.analysis.business.missingLabel": "Saknas",
  "investmentCase.analysis.business.portfolioContextHeading": "Portföljkontext",
  "investmentCase.analysis.business.largestPositionLabel": "Största position: {{ticker}} ({{percent}}%)",
  "investmentCase.analysis.business.otherCategoriesHeading": "Övriga dimensioner",
  "investmentCase.analysis.valuation.heading": "Värdering",
  "investmentCase.analysis.valuation.method.fcf_yield_relative": "FCF-avkastning (relativ)",
  "investmentCase.analysis.valuation.currentYieldLabel": "Aktuell FCF-avkastning",
  "investmentCase.analysis.valuation.scenarioHeading": "Scenarioanalys",
  "investmentCase.analysis.valuation.scenarioNote": "Inte tillgänglig ännu — framåtblickande antaganden har inte angetts.",
  "investmentCase.analysis.risk.heading": "Risk",
  "investmentCase.analysis.risk.subheading": "Varje kategori visas oberoende — slås aldrig ihop till en enda poäng.",
  "investmentCase.analysis.evidence.heading": "Underlag",
  "investmentCase.analysis.evidence.supportingCount": "{{count}} observation(er) med stödjande underlag",
  "investmentCase.analysis.evidence.challengingCount": "{{count}} observation(er) med motsägande underlag",
  "investmentCase.analysis.evidence.coverageLabel": "Täckning",
  "investmentCase.analysis.evidence.qualityHeading": "Underlagets kvalitet",
  "investmentCase.analysis.evidence.missingEvidenceHeading": "Saknat underlag",
  "investmentCase.analysis.evidence.latestLabel": "Senaste",
  "investmentCase.analysis.evidence.viewAll": "Visa allt underlag",
  "investmentCase.analysis.evidence.noneRecorded": "Inget underlag registrerat för det här caset ännu.",
  "investmentCase.analysis.valuationScenarios.heading": "Värderingsscenarier",
  "investmentCase.analysis.valuationScenarios.notYet": "Stöds inte ännu",
  "investmentCase.analysis.recommendation.heading": "Beslutsstöd",
  "decisionSupport.badge.entry_supported": "Nyinvestering stöds",
  "decisionSupport.badge.increase_supported": "Ökning stöds",
  "decisionSupport.badge.thesis_intact": "Tesen kvarstår",
  "decisionSupport.badge.reduction_supported": "Minskning stöds",
  "decisionSupport.badge.exit_supported": "Avyttring stöds",
  "decisionSupport.badge.no_action_supported": "Ingen åtgärd stöds",
  "decisionSupport.badge.insufficient_evidence": "Otillräckligt underlag",
  "decisionSupport.statement.entry_supported": "Nuvarande underlag stöder att inleda en position.",
  "decisionSupport.statement.increase_supported": "Nuvarande underlag stöder att öka exponeringen.",
  "decisionSupport.statement.thesis_intact": "Den nuvarande tesen kvarstår oförändrad.",
  "decisionSupport.statement.reduction_supported": "Nuvarande underlag stöder att minska exponeringen.",
  "decisionSupport.statement.exit_supported": "Nuvarande underlag stöder att avyttra positionen.",
  "decisionSupport.statement.no_action_supported": "Nuvarande underlag stöder inte att inleda en position i detta värdepapper.",
  "decisionSupport.statement.insufficient_evidence": "Nuvarande underlag räcker inte för att stödja någon portföljåtgärd.",
  "investmentCase.analysis.decisionHistory.heading": "Beslutshistorik",
  "investmentCase.analysis.decisionHistory.empty": "Inga beslut registrerade ännu.",
  "investmentCase.analysis.observations.heading": "Investerarens observationer",
  "investmentCase.analysis.observations.empty": "Inga observationer registrerade ännu — analysen kräver inga.",
  "investmentCase.analysis.outcomes.heading": "Utfall",
  "investmentCase.analysis.outcomes.empty": "Inga utfall registrerade ännu.",

  // ---------- investment case: observations ----------
  "investmentCase.observations.heading": "Observationer",
  "investmentCase.observations.loading": "Läser in observationer…",
  "investmentCase.observations.loadError": "Kunde inte läsa in observationer: {{message}}",
  "investmentCase.observations.empty": "Inga observationer registrerade ännu.",
  "investmentCase.observations.addButton": "Lägg till observation",
  "investmentCase.observations.recorded": "Observation registrerad: {{subject}}",
  "investmentCase.observations.subjectLabel": "Ämne",
  "investmentCase.observations.statementLabel": "Beskrivning",
  "investmentCase.observations.recordError": "Kunde inte registrera observationen: {{message}}",

  // ---------- investment case: evidence ----------
  "investmentCase.evidence.heading": "Belägg",
  "investmentCase.evidence.loading": "Läser in belägg…",
  "investmentCase.evidence.loadError": "Kunde inte läsa in belägg: {{message}}",
  "investmentCase.evidence.empty": "Inga belägg registrerade ännu.",
  "investmentCase.evidence.addButton": "+ Lägg till belägg",
  "investmentCase.evidence.recorded": "Belägg registrerat: {{statement}}",
  "investmentCase.evidence.summaryLabel": "Sammanfattning",
  "investmentCase.evidence.sourceLabel": "Källa",
  "investmentCase.evidence.directionLabel": "Riktning",
  "investmentCase.evidence.directionSupports": "Stödjer",
  "investmentCase.evidence.directionChallenges": "Ifrågasätter",
  "investmentCase.evidence.recordError": "Kunde inte registrera belägget: {{message}}",
  "investmentCase.evidence.deleteError": "Kunde inte ta bort belägget.",

  // ---------- investment case: knowledge reference ----------
  "investmentCase.knowledgeReference.heading": "Kunskapsreferenser",
  "investmentCase.knowledgeReference.loading": "Läser in kunskapsreferenser…",
  "investmentCase.knowledgeReference.loadError":
    "Kunde inte läsa in kunskapsreferenser: {{message}}",
  "investmentCase.knowledgeReference.empty": "Inga kunskapsreferenser registrerade ännu.",
  "investmentCase.knowledgeReference.addButton": "+ Lägg till kunskapsreferens",
  "investmentCase.knowledgeReference.itemLabel": "Kunskapsreferens {{id}}",
  "investmentCase.knowledgeReference.recorded": "Kunskapsreferens registrerad: {{id}}",
  "investmentCase.knowledgeReference.prompt":
    "Registrera en kunskapsreferens för den här observationen.",
  "investmentCase.knowledgeReference.recordError":
    "Kunde inte registrera kunskapsreferensen: {{message}}",
  "investmentCase.knowledgeReference.deleteError": "Kunde inte ta bort kunskapsreferensen.",

  // ---------- investment case: reasoning trace ----------
  "investmentCase.reasoningTrace.heading": "Resonemangsspår",
  "investmentCase.reasoningTrace.loading": "Läser in resonemangsspår…",
  "investmentCase.reasoningTrace.loadError": "Kunde inte läsa in resonemangsspår: {{message}}",
  "investmentCase.reasoningTrace.empty": "Inget resonemangsspår registrerat ännu.",
  "investmentCase.reasoningTrace.addButton": "+ Skapa resonemangsspår",
  "investmentCase.reasoningTrace.itemLabel": "Resonemangsspår {{id}}",
  "investmentCase.reasoningTrace.recorded": "Resonemangsspår registrerat: {{id}}",
  "investmentCase.reasoningTrace.prompt":
    "Registrera ett resonemangsspår som stöds av den här observationen.",
  "investmentCase.reasoningTrace.recordError":
    "Kunde inte registrera resonemangsspåret: {{message}}",
  "investmentCase.reasoningTrace.deleteError": "Kunde inte ta bort resonemangsspåret.",

  // ---------- investment case: judgment ----------
  "investmentCase.judgment.heading": "Bedömning",
  "investmentCase.judgment.loading": "Läser in bedömning…",
  "investmentCase.judgment.loadError": "Kunde inte läsa in bedömning: {{message}}",
  "investmentCase.judgment.empty": "Ingen bedömning registrerad ännu.",
  "investmentCase.judgment.addButton": "+ Skapa bedömning",
  "investmentCase.judgment.recorded": "Bedömning registrerad: {{characterization}}",
  "investmentCase.judgment.characterizationLabel": "Karaktärisering",
  "investmentCase.judgment.recordError": "Kunde inte registrera bedömningen: {{message}}",
  "investmentCase.judgment.deleteError": "Kunde inte ta bort bedömningen.",

  // ---------- investment case: decision ----------
  "investmentCase.decision.heading": "Beslut",
  "investmentCase.decision.loading": "Läser in beslut…",
  "investmentCase.decision.loadError": "Kunde inte läsa in beslut: {{message}}",
  "investmentCase.decision.empty": "Inget beslut registrerat ännu.",
  "investmentCase.decision.addButton": "+ Registrera beslut",
  "investmentCase.decision.recorded": "Beslut registrerat: {{decisionType}} — {{subject}}",
  "investmentCase.decision.typeLabel": "Beslutstyp",
  "investmentCase.decision.typeBuy": "Köp",
  "investmentCase.decision.typeSell": "Sälj",
  "investmentCase.decision.typeHold": "Behåll",
  "investmentCase.decision.typeWatch": "Bevaka",
  "investmentCase.decision.typePass": "Avstå",
  "investmentCase.decision.subjectLabel": "Ämne",
  "investmentCase.decision.reasonLabel": "Motivering",
  "investmentCase.decision.confidenceLabel": "Säkerhet (0–100)",
  "investmentCase.decision.confidencePrefix": "Säkerhet: {{value}}",
  "investmentCase.decision.recordError": "Kunde inte registrera beslutet: {{message}}",

  // ---------- investment case: outcome ----------
  "investmentCase.outcome.heading": "Utfall",
  "investmentCase.outcome.loading": "Läser in utfall…",
  "investmentCase.outcome.loadError": "Kunde inte läsa in utfall: {{message}}",
  "investmentCase.outcome.empty": "Inget utfall registrerat ännu.",
  "investmentCase.outcome.needsDecisionFirst":
    "Inget beslut registrerat ännu — registrera ett beslut först.",
  "investmentCase.outcome.addButton": "+ Registrera utfall",
  "investmentCase.outcome.recorded": "Utfall registrerat: {{statement}}",
  "investmentCase.outcome.updatingPortfolio": "Uppdaterar portfölj…",
  "investmentCase.outcome.updatedAutomatically": "Portföljen uppdaterades automatiskt.",
  "investmentCase.outcome.awaitingReconciliation":
    "Affär registrerad. Fördelningen behöver stämmas av på portföljsidan.",
  "investmentCase.outcome.applyTradeError":
    "Utfallet registrerades, men portföljen kunde inte uppdateras: {{message}}",
  "investmentCase.outcome.decisionLabel": "Beslut",
  "investmentCase.outcome.decisionPlaceholder": "Välj ett beslut…",
  "investmentCase.outcome.statementLabel": "Beskrivning",
  "investmentCase.outcome.noteLabel": "Anteckning (valfritt)",
  "investmentCase.outcome.externalTradeCheckbox":
    "Detta var en extern affär — registrera genomförandet",
  "investmentCase.outcome.securityLabel": "Värdepapper",
  "investmentCase.outcome.typeLabel": "Typ",
  "investmentCase.outcome.transactionTypeAdd": "Lägg till",
  "investmentCase.outcome.transactionTypeExit": "Avsluta (tar bort innehavet)",
  "investmentCase.outcome.quantityLabel": "Antal",
  "investmentCase.outcome.executionPriceLabel": "Avslutspris",
  "investmentCase.outcome.feesLabel": "Avgifter (valfritt)",
  "investmentCase.outcome.executedAtLabel": "Datum för genomförande (valfritt — standard är nu)",
  "investmentCase.outcome.recordError": "Kunde inte registrera utfallet: {{message}}",
  "investmentCase.outcome.validation.tradeRequiredFields":
    "Värdepapper, antal och avslutspris krävs för en affär.",

  // ---------- investment case v2: header ----------
  "investmentCase.header.inPortfolio": "I din portfölj",
  "investmentCase.header.notLinked": "Inte kopplat till ett portföljinnehav ännu",
  "investmentCase.header.currentAllocation": "Nuvarande andel: {{percent}}%",
  "investmentCase.header.valuationLabel": "Värdering",
  "investmentCase.header.portfolioFitLabel": "Portföljpassform",
  "investmentCase.header.untitled": "Investeringscase",

  // ---------- investment case hero (UX-020 / APP-002 / APP-003) ----------
  "investmentCase.hero.srHeading": "Atlas nuvarande syn",
  "investmentCase.hero.loading": "Atlas förbereder sin nuvarande bedömning av {{ticker}}…",
  "investmentCase.hero.why.aligned_positive":
    "De grundläggande förutsättningarna förblir starka, och dagens värdering står inte i vägen.",
  "investmentCase.hero.why.aligned_negative":
    "Verksamheten har försvagats, och värderingen ger liten anledning att bortse från det.",
  "investmentCase.hero.why.business_strong_valuation_weak":
    "Den underliggande verksamheten förblir stark, även om dagens värdering lämnar liten marginal.",
  "investmentCase.hero.why.business_weak_valuation_strong":
    "Värderingen ser attraktiv ut här, även om den underliggande verksamheten väcker frågor som bör redas ut först.",
  "investmentCase.hero.why.insufficient":
    "Underlaget är hittills tunnare än vanligt, så den här bedömningen bör ses som en utgångspunkt snarare än en färdig slutsats.",
  "investmentCase.hero.closing.changed": "Något har förändrats sedan din senaste genomgång — värt en närmare titt nedan.",
  "investmentCase.hero.closing.none": "Inget har förändrats sedan ditt senaste besök.",
  "investmentCase.hero.closing.outcomeMissing":
    "En sak värd en stund: ett registrerat beslut här väntar fortfarande på sitt utfall.",
  "investmentCase.hero.closing.reconciliationNeeded":
    "En sak värd en stund: den här positionen behöver fortfarande stämmas av.",
  "investmentCase.hero.closing.thesisStale":
    "En sak värd en stund: tesen här har inte setts över på ett tag.",
  "investmentCase.hero.closing.openQuestion":
    "En sak värd en stund: det finns en öppen fråga som fortfarande är värd att reda ut.",
  "investmentCase.hero.withheld.opening":
    "Atlas har ännu inte tillräckligt underlag för att bilda en tydlig syn på {{ticker}}.",
  "investmentCase.hero.withheld.reason":
    "Det som finns tillgängligt hittills lämnar verkliga, olösta frågor som gör att Atlas inte kan dra en säker slutsats åt något håll.",
  "investmentCase.hero.withheld.closing":
    "Det finns inget att agera på idag — det här är inte en lucka Atlas har förbisett, utan en ärlig återspegling av vad som går att veta just nu.",
  "investmentCase.hero.asOf": "Speglar Atlas analys per {{when}}.",
  "investmentCase.hero.riskLabel": "{{category}}risk: {{status}}",
  "investmentCase.hero.supportingDetailsLabel": "Kompletterande detaljer",

  // ---------- investment case workspace v2: executive summary (Sprint 2) ----------
  "investmentCase.executiveSummary.heading": "Sammanfattning",
  "investmentCase.executiveSummary.assessment.conviction.very_high": "Övertygelsen är mycket hög.",
  "investmentCase.executiveSummary.assessment.conviction.high": "Övertygelsen förblir hög.",
  "investmentCase.executiveSummary.assessment.conviction.moderate": "Övertygelsen är måttlig.",
  "investmentCase.executiveSummary.assessment.conviction.low": "Övertygelsen är låg.",
  "investmentCase.executiveSummary.assessment.conviction.insufficient_evidence":
    "Det finns ännu inte tillräckligt underlag för en övertygelsebedömning.",
  "investmentCase.executiveSummary.assessment.valuation.undervalued": "Värderingen ser attraktiv ut.",
  "investmentCase.executiveSummary.assessment.valuation.fairly_valued": "Värderingen ser rimlig ut.",
  "investmentCase.executiveSummary.assessment.valuation.expensive": "Värderingen har blivit ansträngd.",
  "investmentCase.executiveSummary.assessment.risk": "{{category}}risken är för närvarande {{status}}.",
  "investmentCase.executiveSummary.assessment.thesisStale": "Tesen har inte granskats på länge.",
  "investmentCase.executiveSummary.assessment.insufficientOverall":
    "Det finns ännu inte tillräckligt underlag för en fullständig bedömning.",
  "investmentCase.executiveSummary.priority.heading": "Nuvarande prioritet",
  "investmentCase.executiveSummary.priority.outcomeMissing": "Komplettera saknat utfall.",
  "investmentCase.executiveSummary.priority.reconciliationNeeded": "Granska positionen.",
  "investmentCase.executiveSummary.priority.thesisStale": "Granska tesen.",
  "investmentCase.executiveSummary.priority.openQuestion": "Granska beläggen.",
  "investmentCase.executiveSummary.priority.none": "Inget behöver uppmärksamhet just nu.",
  "investmentCase.executiveSummary.portfolioImpact.heading": "Påverkan på portföljen",
  "investmentCase.executiveSummary.portfolioImpact.weight": "Portföljandel: {{percent}}%",
  "investmentCase.executiveSummary.portfolioImpact.largestPosition": "Detta är din största position.",
  "investmentCase.executiveSummary.portfolioImpact.cash": "Kontantexponering: {{percent}}%",
  "investmentCase.executiveSummary.outstandingIssues.heading": "Utestående frågor",
  "investmentCase.executiveSummary.outstandingIssues.missingEvidence": "Belägg saknas.",
  "investmentCase.executiveSummary.outstandingIssues.thesisStale": "Tesen är inaktuell.",
  "investmentCase.executiveSummary.outstandingIssues.outcomeMissing": "Utfall saknas.",
  "investmentCase.executiveSummary.outstandingIssues.tradeMissing": "Affären är inte rapporterad än.",
  "investmentCase.executiveSummary.outstandingIssues.reconciliationNeeded": "Behöver stämmas av.",
  "investmentCase.executiveSummary.outstandingIssues.moreCount": "+ {{count}} fler fråga/frågor",
  "investmentCase.executiveSummary.discuss.heading": "Diskutera detta case",
  "investmentCase.executiveSummary.discuss.valuationVsConviction":
    "Värderingen ser för närvarande ansträngd ut medan övertygelsen förblir {{conviction}}. Vill du diskutera om detta förändrar din tes?",
  "investmentCase.executiveSummary.discuss.thesisStale":
    "Den här tesen har inte granskats på länge. Vill du diskutera om något har förändrats?",
  "investmentCase.executiveSummary.discuss.evidenceGap":
    "Det finns luckor i beläggen för det här caset. Vill du gå igenom vad som saknas?",
  "investmentCase.executiveSummary.discuss.outstandingWork":
    "Det finns utestående arbete på det här caset. Vill du granska det tillsammans?",
  "investmentCase.executiveSummary.discuss.generic": "Vill du diskutera den här positionen?",
  "investmentCase.executiveSummary.discuss.button": "Diskutera",
  "investmentCase.executiveSummary.discuss.askButton": "Fråga",
  "investmentCase.executiveSummary.askPlaceholder": "Fråga Atlas vad som helst om det här caset…",

  // ---------- investment case v2: Atlas Assessment ----------
  "investmentCase.assessment.heading": "Atlas bedömning",
  "investmentCase.assessment.notLinkedYet":
    "Det här caset är inte kopplat till ett portföljinnehav ännu. Atlas har inget bolag eller portföljläge att bedöma.",
  "investmentCase.assessment.noAnalysisYet":
    "Atlas har ännu inte gjort tillräcklig analys för att rekommendera en portföljförändring.",
  "investmentCase.assessment.heldNoAssessment":
    "Den här positionen finns för närvarande registrerad i din portfölj. Ingen Atlas-genererad bolagsbedömning finns tillgänglig ännu.",
  "investmentCase.assessment.decisionRecorded": "Ett beslut har registrerats för det här caset.",
  "investmentCase.assessment.outcomeRecorded": "En genomförd extern affär har registrerats.",
  "investmentCase.assessment.explanation":
    "Atlas genererar ännu inte bolagsspecifik analys (värdering, övertygelse, bolagskvalitet). Det du ser nedan speglar endast ditt registrerade portföljläge och din beslutshistorik.",

  // ---------- investment case v2: why now ----------
  "investmentCase.whyNow.heading": "Varför nu?",
  "investmentCase.whyNow.awaitingReconciliation": "Fördelningen väntar på avstämning",
  "investmentCase.whyNow.decisionRecorded": "Ett beslut har registrerats",
  "investmentCase.whyNow.outcomeRecorded": "Ett utfall har registrerats",
  "investmentCase.whyNow.none": "Ingen specifik anledning är tillgänglig just nu.",

  // ---------- investment case v2: key decision info cards ----------
  "investmentCase.cards.currentAllocation": "Nuvarande andel",
  "investmentCase.cards.cashAllocation": "Kontantandel",
  "investmentCase.cards.portfolioMode": "Portföljläge",
  "investmentCase.cards.portfolioModePercentOnly": "Endast procent",
  "investmentCase.cards.portfolioModeAbsolute": "Absoluta värden tillgängliga",
  "investmentCase.cards.decisionStatus": "Beslutsstatus",
  "investmentCase.cards.outcomeStatus": "Utfallsstatus",
  "investmentCase.cards.recordedValue": "Registrerat",
  "investmentCase.cards.notRecordedValue": "Inte registrerat ännu",
  "investmentCase.cards.reconciliationStatus": "Avstämningsstatus",
  "investmentCase.cards.lastActivity": "Senast registrerad aktivitet",
  "investmentCase.cards.supportingRecords": "Underliggande poster",

  // ---------- investment case v2: portfolio impact ----------
  "investmentCase.portfolioImpact.heading": "Påverkan på portföljen",
  "investmentCase.portfolioImpact.notHeld": "Det här bolaget finns inte i din portfölj för närvarande.",
  "investmentCase.portfolioImpact.percentOnlyNote":
    "Påverkan på portföljen kan bara uttryckas i procent — inget totalt portföljvärde har angetts.",
  "investmentCase.portfolioImpact.awaitingReconciliation":
    "Den senaste affären mot det här innehavet behöver stämmas av på portföljsidan.",

  // ---------- investment case v2: what Atlas knows ----------
  "investmentCase.whatAtlasKnows.heading": "Det här vet Atlas",
  "investmentCase.whatAtlasKnows.observationsCount": "Registrerade observationer: {{count}}",
  "investmentCase.whatAtlasKnows.supportingEvidenceCount": "Stödjande belägg: {{count}}",
  "investmentCase.whatAtlasKnows.challengingEvidenceCount": "Belägg som talar emot: {{count}}",
  "investmentCase.whatAtlasKnows.judgmentAvailable": "Registrerad bedömning: finns",
  "investmentCase.whatAtlasKnows.judgmentNotAvailable": "Registrerad bedömning: finns inte",
  "investmentCase.whatAtlasKnows.decisionLabel": "Investerarens beslut: {{type}}",
  "investmentCase.whatAtlasKnows.decisionNone": "Investerarens beslut: inte registrerat ännu",
  "investmentCase.whatAtlasKnows.outcomeYes": "Utfall: registrerat",
  "investmentCase.whatAtlasKnows.outcomeNone": "Utfall: inte registrerat",
  "investmentCase.whatAtlasKnows.latestObservation": "Senast registrerade observation",

  // ---------- investment case v2: what remains uncertain ----------
  "investmentCase.uncertain.heading": "Det här är fortfarande osäkert",
  "investmentCase.uncertain.noValuation": "Ingen värderingsanalys finns tillgänglig just nu.",
  "investmentCase.uncertain.noMarketData": "Atlas har ännu inte fått marknadsdata för det här bolaget.",
  "investmentCase.uncertain.noEvidence": "Inga bolagsspecifika belägg har registrerats.",
  "investmentCase.uncertain.percentOnly": "Påverkan på portföljen kan bara uttryckas i procent.",
  "investmentCase.uncertain.awaitingReconciliation": "Den senaste fördelningen behöver stämmas av.",

  // ---------- investment case v2: more details ----------
  "investmentCase.moreDetails.heading": "Mer information",
  "investmentCase.moreDetails.subheading": "Underliggande dokumentation",

  // ---------- investment case v2: decision actions ----------
  "investmentCase.actions.recordDecisionTrigger": "Registrera ett beslut",
  "investmentCase.actions.outcomeAwaitingNudge": "{{count}} beslut väntar på ett utfall",
  "investmentCase.actions.heading": "Vad vill du göra?",
  "investmentCase.actions.addToPosition": "Öka position",
  "investmentCase.actions.trimPosition": "Minska position",
  "investmentCase.actions.removePosition": "Avveckla position",
  "investmentCase.actions.leaveAsIs": "Lämna oförändrad",
  "investmentCase.actions.notLinkedNote":
    "Beslutsåtgärder blir tillgängliga när det här caset kopplas till ett portföljinnehav.",
  "investmentCase.actions.deferredWatchlist": "Bevakningslista-åtgärder är inte tillgängliga i Alpha ännu.",
  "investmentCase.actions.deferredDiscovery": "Upptäck-åtgärder är inte tillgängliga i Alpha ännu.",
  "investmentCase.actions.reasonLabel": "Motivering",
  "investmentCase.actions.confidenceLabel": "Din säkerhet (0–100)",
  "investmentCase.actions.submit": "Registrera beslut",
  "investmentCase.actions.decisionRecordedNote":
    "Beslut registrerat. Atlas genomför aldrig affärer själv — rapportera den genomförda affären nedan när den har skett externt, eller stäng det här om inget har hänt än.",
  "investmentCase.actions.leaveAsIsRecordedNote": "Registrerat — ingen förändring av portföljen.",
  "investmentCase.actions.reportTransaction": "Rapportera genomförd affär",
  "investmentCase.actions.close": "Stäng",
  "investmentCase.actions.openHistory": "Öppna Historik →",
  "investmentCase.actions.recordError": "Kunde inte registrera beslutet: {{message}}",

  // ---------- investment case v2: continuity footer ----------
  "investmentCase.continuity.line1":
    "Atlas använder registrerade portföljförändringar och casehistorik i framtida genomgångar.",
  "investmentCase.continuity.line2":
    "Rapportera genomförda köp eller försäljningar för att hålla portföljens nuvarande läge korrekt.",

  // ---------- investment case: case intelligence (ATLAS-017) ----------
  "investmentCase.intelligence.confidence.heading": "Tillförlitlighet",
  "investmentCase.intelligence.confidence.explanation":
    "Hur väl underbyggd den nuvarande förståelsen är — inte en förutsägelse om framtida avkastning.",
  "investmentCase.intelligence.conviction.heading": "Övertygelse",
  "investmentCase.intelligence.conviction.available": "Tillgänglig.",
  "investmentCase.intelligence.conviction.unavailable":
    "Inte tillgänglig — Atlas beräknar inte ett övertygelsevärde.",

  "investmentCase.intelligence.evidence.heading": "Belägg",
  "investmentCase.intelligence.evidence.supportingCount": "Stödjande belägg: {{count}}",
  "investmentCase.intelligence.evidence.challengingCount": "Motstridiga belägg: {{count}}",
  "investmentCase.intelligence.evidence.contradictingHeading": "Motstridiga belägg, per observation:",
  "investmentCase.intelligence.evidence.contradictingItem": "{{status}} ({{count}} motstridiga)",

  "investmentCase.intelligence.epistemicStatus.supported": "styrkt",
  "investmentCase.intelligence.epistemicStatus.challenged": "ifrågasatt",
  "investmentCase.intelligence.epistemicStatus.contradicted": "motstridig",
  "investmentCase.intelligence.epistemicStatus.assumed": "antagen (inga belägg än)",

  "investmentCase.intelligence.keyRisks.heading": "Viktiga risker",
  "investmentCase.intelligence.keyRisks.empty": "Inga viktiga risker identifierade just nu.",
  "investmentCase.intelligence.keyRisks.contradictingEvidence": "Belägg motsäger den nuvarande tesen.",
  "investmentCase.intelligence.keyRisks.highConcentration": "Hög koncentration i detta innehav.",
  "investmentCase.intelligence.keyRisks.awaitingReconciliation": "Väntar på avstämning efter en affär.",

  "investmentCase.intelligence.missingEvidence.heading": "Saknade belägg",
  "investmentCase.intelligence.missingEvidence.noEvidenceRecorded":
    "Inga belägg registrerade för detta investeringscase.",
  "investmentCase.intelligence.missingEvidence.observationWithoutEvidence":
    "En observation saknar länkade belägg.",
  "investmentCase.intelligence.missingEvidence.decisionWithoutLinkedObservation":
    "Ett beslut saknar länkad observation.",

  "investmentCase.intelligence.openQuestions.heading": "Öppna frågor",
  "investmentCase.intelligence.openQuestions.noEvidenceRecordedForCase":
    "Vilka belägg stödjer eller ifrågasätter denna tes?",
  "investmentCase.intelligence.openQuestions.observationWithoutEvidence":
    "Har denna observation stödjande eller ifrågasättande belägg?",
  "investmentCase.intelligence.openQuestions.decisionWithoutLinkedObservation":
    "Vilken observation föranledde detta beslut?",
  "investmentCase.intelligence.openQuestions.businessDurabilityNotAssessable":
    "Atlas saknar affärsfaktadata för att bedöma uthållighet.",
  "investmentCase.intelligence.openQuestions.valuationThesisNotDocumented":
    "Ingen värderingstes har dokumenterats.",
  "investmentCase.intelligence.openQuestions.portfolioFactorNotAssessable":
    "En portföljövergripande faktor är inte bedömbar än.",

  "investmentCase.intelligence.portfolioContext.heading": "Portföljkontext",
  "investmentCase.intelligence.portfolioContext.notHeld": "Inte för närvarande ett portföljinnehav.",
  "investmentCase.intelligence.portfolioContext.noFacts": "Inga anmärkningsvärda portföljfakta just nu.",
  "investmentCase.intelligence.portfolioContext.largestHolding": "Detta är portföljens största position.",
  "investmentCase.intelligence.portfolioContext.recentlyIncreased": "Senast ökad.",
  "investmentCase.intelligence.portfolioContext.recentlyTrimmed": "Senast minskad.",
  "investmentCase.intelligence.portfolioContext.highConcentration": "Hög koncentration i portföljen.",
  "investmentCase.intelligence.portfolioContext.pendingWorkflow": "Väntande arbetsposter för detta case.",
  "investmentCase.intelligence.portfolioContext.evidenceIncomplete": "Belägg­täckningen är ofullständig.",

  "investmentCase.intelligence.observationTimeline.heading": "Observationstidslinje",
  "investmentCase.intelligence.observationTimeline.empty": "Inga observationer registrerade än.",
  "investmentCase.intelligence.observationTimeline.evidenceCount": "{{count}} belägg­post(er)",

  // ---------- sprint 4: navigation ----------
  "shell.nav.history": "Historik",

  // ---------- daily brief implementation sprint 1: navigation ----------
  "shell.nav.dailyBrief": "Dagens genomgång",
  "shell.nav.discovery": "Discovery",

  // ---------- sprint 4: relative time ----------
  "relativeTime.today": "idag",
  "relativeTime.oneDayAgo": "1 dag sedan",
  "relativeTime.daysAgo": "{{count}} dagar sedan",
  "relativeTime.oneWeekAgo": "1 vecka sedan",
  "relativeTime.weeksAgo": "{{count}} veckor sedan",
  "relativeTime.oneMonthAgo": "1 månad sedan",
  "relativeTime.monthsAgo": "{{count}} månader sedan",

  // ---------- sprint 4: history page ----------
  "history.title": "Historik",
  "history.loadError": "Kunde inte läsa in historiken: {{message}}",
  "history.empty": "Historiken börjar efter ditt första investeringsbeslut.",
  "history.empty.portfolioLink": "Öppna Portfölj →",
  "history.noneMatchFilter": "Ingen aktivitet matchar det här filtret.",
  "history.filter.all": "Alla",
  "history.filter.open": "Öppna",
  "history.filter.completed": "Avslutade",
  "history.sort.newest": "Nyast först",
  "history.sort.oldest": "Äldst först",
  "history.status.open": "Öppen",
  "history.status.completed": "Avslutad",
  "history.row.kindDecision": "Beslut registrerat",
  "history.row.kindOutcome": "Utfall rapporterat",
  "history.row.kindTrade": "Affär genomförd",

  // ---------- History v1: analytical timeline ----------
  "history.scope.all": "Alla",
  "history.scope.decisions": "Beslut och affärer",
  "history.scope.investmentCases": "Förändringar i investeringscase",
  "history.analytical.emptyOnly": "Ingen analyshistorik ännu.",
  "history.analytical.baseline": "Baslinje etablerad",
  "history.analytical.baselineDescription": "Atlas skapade sitt första strukturerade investeringscase för {{company}}.",
  "history.analytical.headline.strengthened": "Tesen stärktes",
  "history.analytical.headline.weakened": "Tesen försvagades",
  "history.analytical.headline.mixed": "Blandade signaler",
  "history.analytical.headline.unchanged": "Ingen väsentlig förändring",
  "history.analytical.viewDetails": "Visa detaljer",
  "history.analytical.hideDetails": "Dölj detaljer",
  "history.analytical.detail.thesisHeading": "Atlas tes vid denna tidpunkt",
  "history.analytical.detail.noThesis": "Ingen Atlas-tes registrerad vid denna tidpunkt.",
  "history.analytical.detail.strengthsHeading": "Styrkor",
  "history.analytical.detail.risksHeading": "Risker",
  "history.analytical.detail.growthHeading": "Tillväxt",
  "history.analytical.detail.valuationHeading": "Värdering",
  "history.analytical.detail.openQuestionsHeading": "Öppna frågor",
  "history.analytical.detail.empty": "Inget registrerat vid denna tidpunkt.",

  // ---------- Visual Fidelity Pass: History ----------
  "history.summary": "Du har registrerat {{count}} investeringsbeslut i {{companies}} bolag sedan {{since}}.",
  "history.timeline.heading": "Beslutstidslinje",
  "history.timeline.viewFull": "Visa hela tidslinjen",
  "history.reviews.heading": "Beslutsgenomgångar",
  "history.reviews.subheading": "Nyliga beslut värda att reflektera över",
  "history.reviews.originalThesis": "Ursprunglig tes",
  "history.reviews.outcome": "Utfall",
  "history.reviews.observedProperties.heading": "Observerat i din beslutshistorik",
  "history.reviews.observedProperties.scope.singleCompany": "Bolagsspecifikt",
  "history.reviews.observedProperties.scope.portfolioWide": "Portföljövergripande",
  "history.reviews.observedProperties.dateRange": "{{from}} – {{to}}",
  "history.reviews.observedProperties.smallSample": "Litet registrerat urval.",
  "history.reviews.observedProperties.limitation": "Baserat endast på registrerade beslut. Utfall och avkastning beaktas inte.",

  // ---------- Sprint 21: Explicit Security Confirmation ----------
  "history.reviews.securityConfirmation.recordedAs": "Registrerat som",
  "history.reviews.securityConfirmation.loadError": "Kunde inte läsa in värdepappersbekräftelse.",
  "history.reviews.securityConfirmation.confirmedSelection": "Bekräftat val",
  "history.reviews.securityConfirmation.confirmedByYou": "Bekräftat av dig.",
  "history.reviews.securityConfirmation.findSecurity": "Hitta värdepapper",
  "history.reviews.securityConfirmation.discoveryError": "Kunde inte söka efter detta värdepapper.",
  "history.reviews.securityConfirmation.possibleMatch": "Möjlig träff",
  "history.reviews.securityConfirmation.noCandidateFound": "Ingen kandidat hittades.",
  "history.reviews.securityConfirmation.confirmThisSecurity": "Bekräfta detta värdepapper",
  "history.reviews.securityConfirmation.notThisSecurity": "Inte detta värdepapper",
  "history.reviews.securityConfirmation.confirmError": "Kunde inte spara din bekräftelse. Försök igen.",
  "history.reviews.securityConfirmation.changeSelection": "Ändra val",
  "history.reviews.securityConfirmation.removeConfirmation": "Ta bort bekräftelse",
  "history.reviews.securityConfirmation.revokeError": "Kunde inte ta bort din bekräftelse. Försök igen.",
  "history.reviews.securityConfirmation.changeSelectionNote": "Din tidigare bekräftelse finns kvar i Atlas historik.",

  // ---------- sprint 4: dashboard sections ----------
  "dashboard.needsAttention.heading": "Kräver uppmärksamhet",
  "dashboard.needsAttention.empty": "Inget kräver din uppmärksamhet just nu.",
  "dashboard.needsAttention.outcomeMissing": "{{security}}: utfall inte rapporterat ännu",
  "dashboard.needsAttention.tradeMissing": "{{security}}: affär inte rapporterad ännu",
  "dashboard.needsAttention.reconciliationNeeded": "{{security}}: fördelningen väntar på avstämning",
  "dashboard.recentActivity.heading": "Senaste aktivitet",
  "dashboard.recentActivity.empty": "Ingen aktivitet registrerad ännu.",
  "dashboard.continueWorking.heading": "Fortsätt arbeta",
  "dashboard.continueWorking.empty": "Ingen nyligen aktivitet i något case ännu.",
  "dashboard.viewHistoryLink": "Visa historik →",

  // ---------- sprint 4: investment case last activity / timeline / outstanding work ----------
  "investmentCase.lastActivity.heading": "Senaste aktivitet",
  "investmentCase.lastActivity.noneYet": "Ingen aktivitet registrerad för det här caset ännu.",
  "investmentCase.lastActivity.lastDecision": "Senaste beslut: {{type}} registrerat {{relativeTime}}.",
  "investmentCase.lastActivity.lastOutcome": "Senaste utfall: rapporterat {{relativeTime}}.",
  "investmentCase.lastActivity.lastTrade": "Senaste affär: {{type}} {{detail}}, {{relativeTime}}.",
  "investmentCase.lastActivity.reconciliationOk": "Portföljfördelningen är uppdaterad.",
  "investmentCase.lastActivity.reconciliationNeeded": "Fördelningen väntar på avstämning.",
  "investmentCase.timeline.empty": "Inga tidslinjehändelser ännu.",
  "investmentCase.timeline.currentStatus": "Aktuell status",
  "investmentCase.outstandingWork.heading": "Återstående att göra",
  "investmentCase.outstandingWork.none": "Inget återstår för det här caset.",
  "investmentCase.outstandingWork.outcomeMissing": "Utfall inte rapporterat ännu.",
  "investmentCase.outstandingWork.tradeMissing": "Affär inte rapporterad ännu.",

  // ---------- sprint 4: navigation continuity (origin badges) ----------
  "investmentCase.origin.dashboard": "Öppnat från översikten",
  "investmentCase.origin.portfolio": "Öppnat från portföljen",
  "investmentCase.origin.history": "Återvänt från historiken",
  "investmentCase.origin.dailyBrief": "Öppnad från Dagens genomgång",
  "investmentCase.origin.discovery": "Öppnad från Discovery",
  "investmentCase.origin.companion": "Öppnad från Atlas Companion",

  // ---------- investment case figma-fidelity rebuild: key metrics / strength-concern-priority ----------
  "investmentCase.keyMetrics.heading": "Nyckeltal",
  "investmentCase.keyMetrics.recommendationLabel": "Rekommendation",
  "investmentCase.keyMetrics.convictionLabel": "Analysdjup",
  "investmentCase.keyMetrics.valuationSupportLabel": "Nedsidesstöd",
  "investmentCase.valuationSupport.present": "Nedsidesstöd finns",
  "investmentCase.valuationSupport.absent": "Nedsidesstöd saknas",
  "investmentCase.valuationSupport.unresolved": "Värderingsslutsats ej fastställd",
  "investmentCase.valuationSupport.cardHeading": "Värderingsstöd",
  "investmentCase.valuationSupport.gap.missingCapitalDeploymentValuationSupport":
    "Atlas har ännu inte gjort den separata bedömningen om dagens pris stödjer att nytt kapital tillförs.",
  "investmentCase.valuationSupport.gap.noDurableGrowthBasis":
    "Det finns ännu ingen period av verklig tillväxt för Atlas att bygga ett värderingsintervall utifrån.",
  "investmentCase.valuationSupport.gap.insufficientHistoricalValuationData":
    "Det finns ännu inte tillräcklig prishistorik för att slutföra denna kontroll.",
  "investmentCase.valuationSupport.gap.scenarioEnvelopeInconclusive":
    "Värderingsintervallet innehåller både en uppgång och en nedgång, beroende på vilket scenario som används.",
  "investmentCase.valuationSupport.gap.conflictingValuationProofs":
    "Två verkliga värderingskontroller pekar åt olika håll, och Atlas väljer inte sida.",
  "investmentCase.valuationSupport.gap.noSufficientValuationProof":
    "Atlas har ännu inget tillförlitligt sätt att bedöma detta bolags värdering.",
  "investmentCase.limitingFactors.heading": "Vad begränsar denna slutsats?",
  "investmentCase.limitingFactors.valuationGapTitle": "Värdering",
  "investmentCase.hero.limitedByPrefix": "Begränsas av:",
  "investmentCase.withheld.missing.businessEvaluation": "Atlas har ännu inte slutfört sin affärsanalys för detta bolag.",
  "investmentCase.withheld.missing.valuation": "Atlas har ännu inte slutfört en värderingsanalys för detta bolag.",
  "investmentCase.withheld.missing.portfolioIntelligence":
    "Atlas har ännu inte slutfört en portföljanpassningsanalys för detta bolag.",
  "investmentCase.withheld.missing.reasoning": "Atlas har ännu inte slutfört sin resonemangssyntes för detta bolag.",
  "investmentCase.keyMetrics.currentPriceLabel": "Aktuellt pris",
  "investmentCase.keyMetrics.expectedReturnLabel": "Förväntad avkastning",
  "investmentCase.keyMetrics.upsideDownsideLabel": "Uppsida / nedsida",
  "investmentCase.keyMetrics.notYetAvailable": "Inte tillgängligt ännu",
  "investmentCase.keyMetrics.expectedReturnCaption": "Långsiktigt tillväxt- och återgångsintervall -- inte en kursmålsättning.",

  // ---------- Recommendation / Decision Intelligence Sprint 1: Outlook<->rekommendation-samstämmighet ----------
  "investmentCase.outlookAlignment.corroborates": "Atlas oberoende beräknade långsiktiga utsikter pekar också på svag förväntad avkastning, vilket överensstämmer med denna rekommendation.",
  "investmentCase.outlookAlignment.diverges": "Atlas oberoende beräknade långsiktiga utsikter pekar på starkare förväntad avkastning än vad denna rekommendation speglar -- en verklig spänning värd att väga in, inte en motsägelse.",
  "investmentCase.outlookAlignment.mixed": "Atlas oberoende beräknade långsiktiga utsikter är blandade och varken tydligt bekräftar eller avviker från denna rekommendation.",
  "investmentCase.outlookAlignment.unavailable": "Långsiktiga utsikter är inte tillgängliga ännu för jämförelse med denna rekommendation.",

  "investmentCase.strengthConcernPriority.strengthLabel": "Största styrka",
  "investmentCase.strengthConcernPriority.concernLabel": "Största orosmoment",
  "investmentCase.strengthConcernPriority.priorityLabel": "Aktuell prioritet",
  "investmentCase.strengthConcernPriority.noStrength": "Ingen styrka har tydligt bevisstöd ännu.",
  "investmentCase.strengthConcernPriority.noConcern": "Inget orosmoment har tydligt bevisstöd ännu.",
  "investmentCase.currentPriority.none": "Inget är för närvarande utestående för det här caset.",
  "investmentCase.concern.thesis_risk": "Själva tesen bär på en identifierad risk värd att bevaka.",

  // ---------- investment case figma-fidelity rebuild: atlas outlook ----------
  "investmentCase.outlook.heading": "Atlas utsikter",
  "investmentCase.outlook.notYetComputed": "Inte beräknat ännu",
  "investmentCase.outlook.shortTerm.heading": "Kort sikt",
  "investmentCase.outlook.longTerm.heading": "Lång sikt",
  "investmentCase.outlook.expectedReturnLabel": "Värderingsimplicerat avkastningsintervall",
  "investmentCase.outlook.convictionLabel": "Övertygelse",
  "investmentCase.outlook.bullCaseLabel": "Värdering — optimistiskt",
  "investmentCase.outlook.baseCaseLabel": "Värdering — bas",
  "investmentCase.outlook.bearCaseLabel": "Värdering — pessimistiskt",
  "investmentCase.outlook.momentumLabel": "Momentum",
  "investmentCase.outlook.keyDriversLabel": "Nyckeldrivkrafter",
  "investmentCase.outlook.whatChangedLabel": "Vad som ändrats",
  "investmentCase.outlook.noDrivers": "Inga nyckeldrivkrafter identifierade ännu.",
  "investmentCase.outlook.noChanges": "Inget har ändrats nyligen.",

  // ---------- outlook intelligence sprint 1: real expected return / scenarios / momentum / drivers ----------
  "investmentCase.outlook.returnBasisNote": "{{basis}}, över {{low}}–{{high}} månader.",
  "investmentCase.outlook.basis.cumulative": "Kumulativ avkastning",
  "investmentCase.outlook.basis.annualized": "Årlig avkastning",
  "investmentCase.outlook.gap.noHistoricalValuationRange":
    "Inte tillräckligt med historisk värderingsdata för att bygga ett intervall ännu.",
  "investmentCase.outlook.gap.valuationNotConclusive": "Ingen aktuell värdering att utgå från ännu.",
  "investmentCase.outlook.gap.noDurableGrowthTrajectory":
    "Ingen verklig, nyligen uppvisad, varaktig tillväxtbana som Atlas ansvarsfullt kan projicera framåt ännu — aldrig påhittat här.",
  "investmentCase.outlook.momentum.strengthening": "Förstärks",
  "investmentCase.outlook.momentum.stable": "Stabil",
  "investmentCase.outlook.momentum.mixed": "Blandad",
  "investmentCase.outlook.momentum.weakening": "Försvagas",
  "investmentCase.outlook.rerangeAssumptionNote":
    "Förutsätter att det fria kassaflödet ligger kvar på dagens nivå och att endast marknadens egen värderingsmultipel förändras — ingen prognos för verksamhetens utveckling.",
  "investmentCase.outlook.scenarioAssumptionNote": "Förutsätter att marknaden omvärderar till en FCF-avkastning på {{targetYield}}.",
  "investmentCase.outlook.scenariosCaption":
    "Endast värderingsscenarier — baserat på {{count}} historiska FCF-avkastningsobservationer, inklusive eventuella ovanliga perioder.",
  "investmentCase.outlook.growthScenariosCaption":
    "Affärstillväxtscenarier som delar ett terminalvärderingsantagande — tillväxten baseras på {{growthCount}} intäktsstyrkta historiska observationer; terminalavkastningen på {{count}} historiska FCF-avkastningsobservationer.",
  "investmentCase.outlook.convictionCaption":
    "Speglar caset-övergripande övertygelse, begränsad när denna horisonts egna underlag är otillräckligt — ingen självständigt modellerad utsiktsövertygelse.",
  "investmentCase.outlook.driver.valuationRerating": "Omvärdering",
  "investmentCase.outlook.driver.revenueTrend": "Senaste intäktstrend",
  "investmentCase.outlook.driver.growth": "Tillväxt",
  "investmentCase.outlook.driver.capitalAllocation": "Kapitalallokering",
  "investmentCase.outlook.driver.financialRisk": "Finansiell risk",
  "investmentCase.outlook.driver.businessRisk": "Affärsrisk",
  "investmentCase.outlook.driver.valuationRisk": "Värderingsrisk",
  "investmentCase.outlook.driver.fcfGrowthTrend": "Senaste trend för fritt kassaflöde",
  "investmentCase.outlook.driver.debtTrend": "Skuldtrend",
  "investmentCase.outlook.driver.marginTrend": "Rörelsemarginaltrend",

  // ---------- long-term expected return v1 ----------
  "investmentCase.outlook.growthAssumptionNote":
    "Förutsätter att det fria kassaflödet växer med {{growthRate}} årligen i {{years}} år, baserat på bolagets egen faktiska historik, och att marknaden sedan omvärderar till en FCF-avkastning på {{targetYield}} — ingen prognos för verksamhetens framtida utveckling.",
  "investmentCase.outlook.scenarioGrowthAssumptionNote":
    "Förutsätter {{growthRate}} årlig tillväxt i fritt kassaflöde och en terminal FCF-avkastning på {{targetYield}}.",

  // ---------- long-term expected return calibration sprint ----------
  "investmentCase.outlook.growthBullCaseLabel": "Affärstillväxt — optimistiskt",
  "investmentCase.outlook.growthBaseCaseLabel": "Affärstillväxt — bas",
  "investmentCase.outlook.growthBearCaseLabel": "Affärstillväxt — pessimistiskt",
  "investmentCase.outlook.expectedReturnLabel.growth": "Förväntat avkastningsintervall",

  // ---------- investment case figma-fidelity rebuild: investment argument ----------
  "investmentCase.argument.heading": "Investeringsargument",
  "investmentCase.argument.supportsHeading": "Talar för caset",
  "investmentCase.argument.challengesHeading": "Talar mot caset",
  "investmentCase.argument.supportsEmpty": "Inget har klassificerats som en stödjande faktor ännu.",
  "investmentCase.argument.challengesEmpty": "Inget har klassificerats som en motverkande faktor ännu.",
  "investmentCase.argument.supports.growth": "Tillväxttrenderna är starka nog för att stödja caset.",
  "investmentCase.argument.supports.capital_allocation":
    "Kapitalallokeringen har varit disciplinerad nog för att stödja caset.",
  "investmentCase.argument.supports.valuation": "Dagens värdering stödjer caset snarare än att motverka det.",
  "investmentCase.argument.challenges.growth": "Avtagande tillväxt talar mot caset.",
  "investmentCase.argument.challenges.capital_allocation":
    "Kapitalallokeringen arbetar för närvarande mot aktieägarna, vilket talar mot caset.",
  "investmentCase.argument.challenges.valuation":
    "Dagens värdering framstår som dyr i förhållande till bolagets egen historik, vilket talar mot caset.",
  "investmentCase.argument.challenges.business_risk": "En identifierad affärsrisk talar mot caset.",
  "investmentCase.argument.challenges.financial_risk": "En identifierad finansiell risk talar mot caset.",
  "investmentCase.argument.challenges.valuation_risk": "En identifierad värderingsrisk talar mot caset.",

  // ---------- investment case figma-fidelity rebuild: atlas reasoning ----------
  "investmentCase.reasoning.heading": "Atlas resonemang",
  "investmentCase.reasoning.growthLabel": "Tillväxt",
  "investmentCase.reasoning.valuationLabel": "Värdering",
  "investmentCase.reasoning.financialHealthLabel": "Finansiell hälsa",
  "investmentCase.reasoning.businessQualityLabel": "Verksamhetens kvalitet",
  "investmentCase.reasoning.notYetEvaluated": "Inte utvärderat ännu.",
  "investmentCase.reasoning.growth.strong": "Tillväxten är stark och stödjer caset.",
  "investmentCase.reasoning.growth.moderate": "Tillväxten är måttlig — en verklig men inte avgörande faktor.",
  "investmentCase.reasoning.growth.weak": "Tillväxten är svag och talar mot caset.",
  "investmentCase.reasoning.valuation.undervalued": "Verksamheten framstår som undervärderad till dagens pris.",
  "investmentCase.reasoning.valuation.fairly_valued": "Verksamheten framstår som rimligt värderad till dagens pris.",
  "investmentCase.reasoning.valuation.expensive": "Verksamheten framstår som dyr till dagens pris.",
  "investmentCase.reasoning.financialHealth.low":
    "Finansiell risk är låg — balansräkningen är inget bekymmer på kort sikt.",
  "investmentCase.reasoning.financialHealth.moderate":
    "Finansiell risk är måttlig — värt att bevaka, men inget bekymmer ännu.",
  "investmentCase.reasoning.financialHealth.high": "Finansiell risk är hög och kräver uppmärksamhet.",
  "investmentCase.reasoning.businessQuality.strong": "Verksamhetens kvalitet är stark och stödjer uthållighet.",
  "investmentCase.reasoning.businessQuality.moderate":
    "Verksamhetens kvalitet är måttlig — uthålligheten är inte fullt fastställd ännu.",
  "investmentCase.reasoning.businessQuality.weak":
    "Verksamhetens kvalitet är svag och väcker frågor om uthållighet.",

  // ---------- investment case figma-fidelity rebuild: company health assessment ----------
  "investmentCase.companyHealth.heading": "Bedömning av bolagets hälsa",
  "investmentCase.companyHealth.businessQualityLabel": "Verksamhetens kvalitet",
  "investmentCase.companyHealth.financialStrengthLabel": "Finansiell styrka",
  "investmentCase.companyHealth.managementGovernanceLabel": "Ledning & styrning",
  "investmentCase.companyHealth.capitalAllocationLabel": "Kapitalallokering",
  "investmentCase.companyHealth.competitivePositionLabel": "Konkurrensposition",
  "investmentCase.companyHealth.expandLabel": "Visa underliggande bevis",
  "investmentCase.companyHealth.supportingHeading": "Stödjande bevis",
  "investmentCase.companyHealth.contradictingHeading": "Motsägande bevis",
  "investmentCase.companyHealth.missingHeading": "Saknade bevis",
  "investmentCase.companyHealth.noneFound": "Inget registrerat.",
  "investmentCase.companyHealth.notYetEvaluated": "Inte utvärderat ännu — de bevis som krävs har inte samlats in.",
  "investmentCase.companyHealth.businessQuality.strong":
    "Verksamhetens kvalitet ser stark ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.businessQuality.moderate":
    "Verksamhetens kvalitet ser måttlig ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.businessQuality.weak":
    "Verksamhetens kvalitet ser svag ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.financialStrength.low": "Finansiell risk bedöms för närvarande som låg.",
  "investmentCase.companyHealth.financialStrength.moderate": "Finansiell risk bedöms för närvarande som måttlig.",
  "investmentCase.companyHealth.financialStrength.high": "Finansiell risk bedöms för närvarande som hög.",
  "investmentCase.companyHealth.management.strong":
    "Ledning och styrning ser stark ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.management.moderate":
    "Ledning och styrning ser måttlig ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.management.weak":
    "Ledning och styrning ser svag ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.capitalAllocation.strong":
    "Kapitalallokeringen ser stark ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.capitalAllocation.moderate":
    "Kapitalallokeringen ser måttlig ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.capitalAllocation.weak":
    "Kapitalallokeringen ser svag ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.competitivePosition.strong":
    "Konkurrenspositionen ser stark ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.competitivePosition.moderate":
    "Konkurrenspositionen ser måttlig ut utifrån de bevis som samlats in hittills.",
  "investmentCase.companyHealth.competitivePosition.weak":
    "Konkurrenspositionen ser svag ut utifrån de bevis som samlats in hittills.",

  // ---------- investment case figma-fidelity rebuild: interpreted financial evidence ----------
  "investmentCase.financialEvidence.heading": "Tolkad finansiell bevisning",
  "investmentCase.financialEvidence.operatingMarginLabel": "Rörelsemarginal",
  "investmentCase.financialEvidence.detailedFinancialsLabel": "Detaljerad finansiell data, källor & metod",
  "investmentCase.financialEvidence.notEnoughHistory": "Inte tillräcklig historik för att tolka ännu.",
  "investmentCase.financialEvidence.revenue.up": "Intäkterna växer — efterfrågan fortsätter att expandera.",
  "investmentCase.financialEvidence.revenue.down": "Intäkterna minskar — värt att bevaka om trenden håller i sig.",
  "investmentCase.financialEvidence.revenue.flat": "Intäkterna är i princip oförändrade jämfört med föregående period.",
  "investmentCase.financialEvidence.operatingMargin.up":
    "Rörelsemarginalen ökar — verksamheten omvandlar intäkter till vinst allt effektivare.",
  "investmentCase.financialEvidence.operatingMargin.down":
    "Rörelsemarginalen krymper — lönsamheten är under press.",
  "investmentCase.financialEvidence.operatingMargin.flat":
    "Rörelsemarginalen är i princip oförändrad jämfört med föregående period.",
  "investmentCase.financialEvidence.freeCashFlow.up":
    "Det fria kassaflödet växer, vilket ger verksamheten mer utrymme att investera, dela ut kapital eller möta en nedgång.",
  "investmentCase.financialEvidence.freeCashFlow.down":
    "Det fria kassaflödet minskar, vilket minskar verksamhetens flexibilitet.",
  "investmentCase.financialEvidence.freeCashFlow.flat":
    "Det fria kassaflödet är i princip oförändrat jämfört med föregående period.",
  "investmentCase.financialEvidence.totalDebt.up": "Den totala skulden ökar — värt att bevaka tillsammans med kassaflödet.",
  "investmentCase.financialEvidence.totalDebt.down": "Den totala skulden minskar, ett litet plus för balansräkningen.",
  "investmentCase.financialEvidence.totalDebt.flat":
    "Den totala skulden är i princip oförändrad jämfört med föregående period.",

  // ---------- daily brief v2 (Workspace Migration Phase 4) ----------
  "dailyBrief.title": "Dagens genomgång",
  "dailyBrief.subtitle": "Atlas morgongenomgång för din uppmärksamhet.",
  "dailyBrief.lastUpdated": "Senast uppdaterad {{time}}",
  "dailyBrief.entry.unknownCompany": "Okänt företag",
  "dailyBrief.entry.openInvestmentCase": "Öppna Investment Case",
  "dailyBrief.priorities.heading": "Dagens prioriteringar",
  "dailyBrief.priorities.empty": "Inget behöver din uppmärksamhet just nu.",
  "dailyBrief.priorities.reviewButton": "Granska",
  "dailyBrief.priorities.goToPortfolioButton": "Gå till portföljen",
  "dailyBrief.portfolioChanges.heading": "Portföljförändringar",
  "dailyBrief.portfolioChanges.empty": "Inga portföljinnehav har någon relevant förändring att granska.",
  "dailyBrief.watchlistUpdates.heading": "Bevakningslista – uppdateringar",
  "dailyBrief.watchlistUpdates.empty": "Inga bevakade bolag har någon relevant förändring att granska.",

  // ---------- discovery v1 implementation sprint ----------
  "discovery.title": "Discovery",
  "discovery.workingOnBehalf": "Atlas har arbetat å dina vägnar.",
  "discovery.whatFound.heading": "Vad Atlas hittade",
  "discovery.whatFound.empty": "Inga nya analytiska fynd sedan ditt senaste besök.",
  "discovery.watchlistUpdates.heading": "Bevakningslista – uppdateringar",
  "discovery.watchlistUpdates.empty": "Inga bevakade bolag har en meningsfull förändring att granska.",
  "discovery.reviewCompany.heading": "Granska ett bolag",
  "discovery.reviewCompany.createCase": "Skapa investeringscase →",
  "discovery.reviewCompany.openCase": "Öppna investeringscase →",
  "discovery.reviewCompany.notInPortfolio":
    "{{ticker}} finns inte i din nuvarande portfölj än. Atlas kan inte skapa ett länkat investeringscase för ett bolag du inte äger.",
  "discovery.reviewCompany.error": "Kunde inte skapa investeringscaset: {{message}}",

  // ---------- portfolio import v1.4 ----------
  "portfolioImport.title": "Importera portfölj",
  "portfolioImport.paste.heading": "Importera din portfölj",
  "portfolioImport.paste.instructions": "Klistra in dina innehav nedan.",
  "portfolioImport.paste.placeholder": "AMD 40\nNVDA 30\nASML 20",
  "portfolioImport.paste.reviewNote": "Du får granska allt innan Atlas uppdaterar din portfölj.",
  "portfolioImport.paste.continueButton": "Granska portfölj",
  "portfolioImport.review.heading": "Granska portfölj",
  "portfolioImport.review.holdingsFound": "{{count}} innehav hittades",
  "portfolioImport.review.weightPercentLabel": "Vikt %",
  "portfolioImport.review.resolved": "Bekräftad",
  "portfolioImport.review.needsConfirmation": "Behöver bekräftas",
  "portfolioImport.review.statsResolved": "{{count}} bekräftades automatiskt",
  "portfolioImport.review.statsNeedsConfirmation": "{{count}} behöver bekräftas",
  "portfolioImport.review.statsUnsupported": "{{count}} kända icke-aktieinstrument",
  "portfolioImport.review.recognizedUnsupported": "Känt instrument — behöver bekräftas före import",
  "portfolioImport.review.unsupportedManualWarning":
    "Om du anger en ticker importeras det här som en vanlig aktie, trots att Atlas känner igen det som: {{instrumentType}}. Fortsätt bara om det är avsiktligt.",
  "portfolioImport.instrumentType.equity": "Aktie",
  "portfolioImport.instrumentType.fund": "Fond",
  "portfolioImport.instrumentType.etp": "Börshandlad produkt",
  "portfolioImport.instrumentType.private": "Privat bolag",
  "portfolioImport.instrumentType.other": "Övrigt instrument",
  "portfolioImport.review.manualTickerPlaceholder": "Ange ticker",
  "portfolioImport.review.confirmationRequired": "{{count}} rader behöver en ticker innan du kan importera",
  "portfolioImport.review.errorsHeading": "Kunde inte importera {{count}} rader",
  "portfolioImport.review.lineError": "Rad {{line}} — {{error}}",
  "portfolioImport.review.noHoldingsFound": "Inga innehav hittades i den inklistrade texten.",
  "portfolioImport.review.replaceWarning": "Det här ersätter de innehav som just nu visas i Atlas.",
  "portfolioImport.review.backButton": "Tillbaka och redigera",
  "portfolioImport.review.submitError": "Kunde inte importera din portfölj: {{message}}",
  "portfolioImport.error.missingName": "Namn saknas",
  "portfolioImport.error.missingValue": "Värde saknas",
  "portfolioImport.error.invalidValue": "Värdet är inte ett tal",
  "portfolioImport.error.nonPositiveValue": "Värdet måste vara större än noll",
  "portfolioImport.error.duplicateTicker": "Dubblett av ticker: {{ticker}}",
  "portfolioImport.error.tooManyColumns": "För många kolumner",

  // ---------- Atlas Companion (persistent cross-workspace conversational layer) ----------
  "companion.toggle.openLabel": "Öppna Atlas",
  "companion.toggle.closeLabel": "Stäng Atlas",
  "companion.panel.title": "Atlas Companion",
  "companion.role.user": "Du",
  "companion.role.atlas": "Atlas",
  "companion.context.discussing": "Diskuterar: {{subject}}",
  "companion.context.portfolioWide": "Portföljövergripande",
  "companion.context.changed": "Kontext ändrad: {{from}} → {{to}}",
  "companion.input.placeholder": "Meddela Atlas…",
  "companion.input.send": "Skicka",
  "companion.sending": "Atlas svarar…",
  "companion.notConfigured": "Atlas Companion är inte ansluten i den här Alpha-versionen än.",
  "companion.providerError": "Atlas kunde inte svara just nu — försök fråga igen.",
  "companion.outcome.opened": "Öppnade det befintliga investeringscaset för {{ticker}}.",
  "companion.outcome.created": "Skapade ett nytt investeringscase för {{ticker}}.",
  "companion.outcome.unresolved":
    "{{ticker}} finns inte i din nuvarande portfölj, så Atlas kunde inte öppna ett länkat investeringscase för det.",
  "companion.outcome.failed": "Atlas kunde inte skapa investeringscaset för {{ticker}} just nu. Försök igen.",
};
