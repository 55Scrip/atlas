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

  "portfolio.unallocated":
    "Ofördelat: {{percent}}% — den här portföljen täcker ännu inte 100% av innehaven; Atlas hittar inte på resten.",
  "portfolio.concentration": "Koncentration: {{value}}",
  "portfolio.concentrationLevel.low": "Låg",
  "portfolio.concentrationLevel.moderate": "Måttlig",
  "portfolio.concentrationLevel.elevated": "Förhöjd",
  "portfolio.concentrationLevel.high": "Hög",

  // ---------- portfolio intelligence (ATLAS-015) ----------
  "portfolio.summary.heading": "Portföljöversikt",
  "portfolio.summary.holdings": "Innehav",
  "portfolio.summary.noLargestPosition": "—",
  // ---------- portfolio summary bar (Portfolio Workspace v3) ----------
  "portfolio.summary.cash": "Kontanter",
  "portfolio.summary.needsAttention": "Behöver uppmärksamhet",
  "portfolio.summary.health": "Hälsa",
  "portfolio.summary.unknownInstrumentsWarning": "{{count}} innehav kunde inte tolkas fullt ut. Granska instrumenten.",

  // ---------- portfolio action center (ATLAS UI Sprint) ----------
  "portfolio.actionCenter.heading": "Dagens prioriteringar",
  "portfolio.actionCenter.empty": "Inget behöver din uppmärksamhet just nu.",
  "portfolio.actionCenter.severity.highest": "Högsta prioritet",
  "portfolio.actionCenter.severity.high": "Hög prioritet",
  "portfolio.actionCenter.severity.medium": "Medelhög prioritet",
  "portfolio.actionCenter.reviewTitle": "Granska {{ticker}}",
  "portfolio.actionCenter.completeEvidenceTitle": "Komplettera belägg för {{ticker}}",
  "portfolio.actionCenter.concentrationTitle": "Granska koncentrationen i {{ticker}}",
  "portfolio.actionCenter.allocationTitle": "Granska portföljens allokering",
  "portfolio.actionCenter.evidenceReason": "Belägg saknas.",
  "portfolio.actionCenter.allocationReason": "{{percent}}% är för närvarande oallokerat.",
  "portfolio.actionCenter.itemCount": "{{count}} post(er)",
  "portfolio.actionCenter.reviewButton": "Granska",
  "portfolio.actionCenter.openCaseButton": "Öppna case",
  "portfolio.actionCenter.reason.missingCase": "Inget investeringscase än.",
  "portfolio.actionCenter.reason.decisionWithoutOutcome": "Beslutet saknar rapporterat utfall.",
  "portfolio.actionCenter.reason.outcomeWithoutExecution": "Utfallet saknar bekräftat genomförande.",
  "portfolio.actionCenter.reason.awaitingReconciliation": "Väntar på avstämning efter en affär.",
  "portfolio.actionCenter.reason.veryOldCase": "Investeringscaset är {{days}} dagar gammalt.",
  "portfolio.actionCenter.reason.observationWithoutDecision": "En observation saknar beslut.",

  "portfolio.health.coverage": "{{withCase}} av {{total}} innehav har ett investeringscase",

  // ---------- holdings table (Portfolio Workspace v3) ----------
  "portfolio.holdingsTable.statusHeader": "Status",
  "portfolio.holdingsTable.tickerHeader": "Ticker",
  "portfolio.holdingsTable.weightHeader": "Andel",
  "portfolio.holdingsTable.convictionHeader": "Övertygelse",
  "portfolio.holdingsTable.evidenceHeader": "Underlag",
  "portfolio.holdingsTable.priorityHeader": "Prioritet",
  "portfolio.holdingsTable.thesisHeader": "Tes",
  "portfolio.holdingsTable.thesisFresh": "Aktuell",
  "portfolio.holdingsTable.thesisStale": "Inaktuell",
  "portfolio.holdingsTable.reconcileToggle": "Stäm av",

  // ---------- today's discussions (Portfolio Workspace v3) ----------
  "portfolio.discussions.heading": "Dagens diskussioner",
  "portfolio.discussions.intro": "Atlas har uppmärksammat några saker värda att diskutera.",
  "portfolio.discussions.empty": "Inget särskilt att diskutera just nu.",
  "portfolio.discussions.discussButton": "Diskutera",
  "portfolio.discussions.askPlaceholder": "Fråga Atlas vad som helst om din portfölj…",
  "portfolio.discussions.askButton": "Fråga",
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
  "investmentCase.analysis.companyOverview.empty": "Atlas har ännu inte automatiskt identifierat det här företaget. Berikning kan fortfarande pågå eller vara otillgänglig för den här tickern.",
  "investmentCase.analysis.financials.heading": "Finansiell information",
  "investmentCase.analysis.financials.periodLabel": "Räkenskapsperiod som slutar {{date}}",
  "investmentCase.analysis.financials.revenueLabel": "Intäkter",
  "investmentCase.analysis.financials.freeCashFlowLabel": "Fritt kassaflöde",
  "investmentCase.analysis.financials.capitalExpenditureLabel": "Investeringar",
  "investmentCase.analysis.financials.shareBuybacksLabel": "Återköp av aktier",
  "investmentCase.analysis.financials.dividendsLabel": "Utdelningar",
  "investmentCase.analysis.financials.marketSnapshotHeading": "Aktuell marknadsdata",
  "investmentCase.analysis.financials.sharePriceLabel": "Aktiekurs",
  "investmentCase.analysis.financials.sharesOutstandingLabel": "Utestående aktier",
  "investmentCase.analysis.financials.empty": "Atlas har ännu inte automatiskt hämtat finansiell data för det här företaget.",
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
  "investmentCase.analysis.evidence.noneRecorded": "Inget underlag registrerat för det här caset ännu.",
  "investmentCase.analysis.recommendation.heading": "Rekommendation",
  "investmentCase.analysis.recommendation.withheld": "Avstår",
  "investmentCase.analysis.recommendation.reasonLabel": "Skäl",
  "investmentCase.analysis.recommendation.reason.engine_not_implemented": "Rekommendationsmotorn har inte byggts ännu.",
  "investmentCase.analysis.recommendation.reason.evidence_insufficient": "Den nödvändiga utvärderingstäckningen är ännu inte tillräcklig.",
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
  "investmentCase.header.caseIdLabel": "Case-id: {{caseId}}",
  "investmentCase.header.untitled": "Investeringscase",

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

  // ---------- daily brief implementation sprint 1 ----------
  "dailyBrief.title": "Dagens genomgång",
  "dailyBrief.verdict.nothingUrgent": "Inget viktigt kräver din uppmärksamhet idag.",
  "dailyBrief.verdict.oneItem": "En sak kräver din uppmärksamhet idag.",
  "dailyBrief.verdict.items": "{{count}} saker kräver din uppmärksamhet idag.",
  "dailyBrief.priority.heading": "Prioritet",
  "dailyBrief.recentDecisions.heading": "Senaste beslut",
  "dailyBrief.recentDecisions.empty": "Inga beslut registrerade ännu.",
  "dailyBrief.monitoring.heading": "Övervakning",
  "dailyBrief.monitoring.body":
    "Atlas fortsätter övervaka dina registrerade portföljbeslut och investeringscase.",
  "dailyBrief.footer.reminder":
    "Håll Atlas uppdaterad när din portfölj förändras så att framtida genomgångar förblir korrekta.",

  // ---------- discovery v1 implementation sprint ----------
  "discovery.title": "Discovery",
  "discovery.prompt.heading": "Hur kan jag hjälpa dig?",
  "discovery.prompt.supporting":
    "Fråga om bolag, branscher, marknadshändelser, din portfölj eller vilken investeringsidé som helst.",
  "discovery.info.ariaLabel": "Mer information",
  "discovery.info.body":
    "Här kan du diskutera allt från en specifik kvartalsrapport eller ett enskilt bolag till bredare marknadstrender, makroekonomi och portföljstrategi.",
  "discovery.info.learnMore": "Läs mer om hur Atlas Discovery fungerar →",
  "discovery.portfolioContext.available": "Din portfölj är tillgänglig som kontext för framtida Discovery-analys.",
  "discovery.input.placeholder": "Fråga Atlas vad som helst om investeringar…",
  "discovery.input.submit": "Skicka",
  "discovery.suggestions.aiStocks": "Är AI-aktier attraktiva efter den senaste nedgången?",
  "discovery.suggestions.compare": "Jämför två bolag",
  "discovery.suggestions.strengthenPortfolio": "Vad skulle stärka min portfölj?",
  "discovery.suggestions.reviewIdea": "Granska en investeringsidé",
  "discovery.suggestions.marketTrend": "Hjälp mig tänka igenom en marknadstrend",
  "discovery.response.bounded":
    "Discoverys analysmotor är inte ansluten i den här Alpha-versionen än. Du kan fortfarande öppna eller skapa ett investeringscase för ett bolag du vill granska.",
  "discovery.response.providerError":
    "Atlas kunde inte generera ett svar just nu. Du kan försöka fråga igen.",
  "discovery.chat.sending": "Tänker…",
  "discovery.chat.unavailable": "Atlas kunde inte nås. Kontrollera din anslutning och försök igen.",
  "discovery.reviewCompany.heading": "Granska ett bolag",
  "discovery.reviewCompany.createCase": "Skapa investeringscase →",
  "discovery.reviewCompany.openCase": "Öppna investeringscase →",
  "discovery.reviewCompany.notInPortfolio":
    "{{ticker}} finns inte i din nuvarande portfölj än. Atlas kan inte skapa ett länkat investeringscase för ett bolag du inte äger.",
  "discovery.reviewCompany.error": "Kunde inte skapa investeringscaset: {{message}}",
  "discovery.opportunities.heading": "Möjligheter",
  "discovery.opportunities.notYet": "Atlas har inte genererat några marknadsmöjligheter i den här Alpha-versionen än.",
  "discovery.tool.caseOpened": "Öppnar ditt befintliga investeringscase för {{ticker}}.",
  "discovery.tool.caseCreated": "Skapar och öppnar ett investeringscase för {{ticker}}.",
  "discovery.tool.tickerUnresolved":
    "{{ticker}} finns inte i din nuvarande portfölj, så Atlas kan inte öppna ett länkat investeringscase för det än. Du kan bekräfta exakt ticker, eller använda \"Granska ett bolag\" nedan när det finns i din portfölj.",
  "discovery.tool.caseFailed":
    "Atlas kunde inte skapa investeringscaset för {{ticker}} just nu. Du kan försöka igen, eller använda \"Granska ett bolag\" nedan.",

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
};
