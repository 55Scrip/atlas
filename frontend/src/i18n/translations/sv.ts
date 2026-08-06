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

  // ---------- dashboard ----------
  "dashboard.title": "Översikt",
  "dashboard.portfolioStatus.heading": "Portföljstatus",
  "dashboard.portfolioStatus.loadError": "Kunde inte läsa in portföljstatus: {{message}}",
  "dashboard.portfolioStatus.notEstablished": "Ingen portfölj skapad ännu.",
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
  "investmentCase.returnToPortfolio": "← Tillbaka till portföljen",
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
  "investmentCase.outcome.quantityLabel": "Antal",
  "investmentCase.outcome.executionPriceLabel": "Avslutspris",
  "investmentCase.outcome.feesLabel": "Avgifter (valfritt)",
  "investmentCase.outcome.executedAtLabel": "Datum för genomförande (valfritt — standard är nu)",
  "investmentCase.outcome.recordError": "Kunde inte registrera utfallet: {{message}}",
  "investmentCase.outcome.validation.tradeRequiredFields":
    "Värdepapper, antal och avslutspris krävs för en affär.",
};
