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
  "portfolio.cashLabel": "Kontanter: {{percent}}%",
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
  "portfolio.summary.largestPosition": "Största position",
  "portfolio.summary.noLargestPosition": "—",
  "portfolio.summary.investmentCases": "Investeringscase",
  "portfolio.summary.openDecisions": "Öppna beslut",
  "portfolio.summary.pendingOutcomes": "Väntande utfall",
  "portfolio.summary.pendingExecutions": "Väntande genomföranden",
  "portfolio.summary.concentration": "Koncentration",
  "portfolio.summary.unallocated": "Ej allokerat",
  "portfolio.needsAttention.heading": "Behöver uppmärksamhet",
  "portfolio.needsAttention.empty": "Inget behöver uppmärksamhet just nu.",
  "portfolio.needsAttention.missingCase": "{{ticker}} — inget investeringscase än",
  "portfolio.needsAttention.decisionWithoutOutcome": "{{ticker}} — ett beslut saknar rapporterat utfall",
  "portfolio.needsAttention.outcomeWithoutExecution": "{{ticker}} — ett utfall saknar bekräftat genomförande",
  "portfolio.needsAttention.awaitingReconciliation": "{{ticker}} — väntar på avstämning efter en affär",
  "portfolio.needsAttention.veryOldCase": "{{ticker}} — investeringscaset är {{days}} dagar gammalt",
  "portfolio.needsAttention.observationWithoutDecision": "{{ticker}} — en observation saknar beslut",
  "portfolio.reviewQueue.heading": "Granskningskö",
  "portfolio.reviewQueue.empty": "Inget köat för granskning.",
  "portfolio.reviewQueue.item": "Granska {{ticker}}",
  "portfolio.reviewQueue.reasonCount": "{{count}} poster",
  "portfolio.health.heading": "Portföljhälsa",
  "portfolio.health.coverage": "{{withCase}} av {{total}} innehav har ett investeringscase",
  "portfolio.health.freshness": "Senaste beslut: {{date}}",
  "portfolio.health.noDecisions": "Inga beslut registrerade än",
  "portfolio.health.outstandingItems": "Utestående arbetsposter",
  "portfolio.health.completeness": "Portföljens fullständighet",
  "portfolio.health.unknownInstruments": "Okända instrument",
  "portfolio.health.noUnknownInstruments": "Inga upptäckta",

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
  "investmentCase.status.placeholder":
    "Reserverad för indikatorer för utkast, historik och bevakning i en framtida version.",
  "investmentCase.primaryWorkArea.heading": "Primärt arbetsområde",
  "investmentCase.timeline.heading": "Tidslinje",
  "investmentCase.timeline.placeholder":
    "Reserverad för beslutets egen tidslinje i en framtida version.",
  "investmentCase.footer.heading": "Sidfot",

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
