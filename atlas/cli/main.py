import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from atlas.comparison import (
    InvestmentComparisonEngine,
    InvestmentComparisonInput,
    demo_investment_comparison_input,
    render_investment_comparison,
)
from atlas.analysis.memory import (
    MemoryEngine,
    MemoryStore,
    render_memory_comparison,
    render_memory_entries,
)
from atlas.analysis.portfolio import (
    Portfolio,
    PortfolioIntelligenceEngine,
    render_portfolio_analysis,
)
from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
from atlas.domains.portfolio import portfolio_summary as domain_portfolio_summary
from atlas.analysis.report import build_investment_report, render_investment_report
from atlas.analysis.watchlist import Watchlist, WatchlistEngine, render_watchlist_analysis
from atlas.watchlist_review import (
    WatchlistReviewEngine,
    demo_watchlist_review_input,
    render_watchlist_review,
    watchlist_review_input_from_json_file,
)
from atlas.conversation import (
    ConversationEngine,
    ConversationInput,
    render_conversation_response,
)
from atlas.dashboard import DashboardEngine, DashboardInput, render_dashboard
from atlas.daily import DailyBriefEngine, DailyBriefInput, render_daily_brief
from atlas.capabilities.daily_brief import DailyBriefCapability
from atlas.capabilities.daily_brief import DailyBriefInput as CapDailyBriefInput
from atlas.capabilities.daily_brief import build_daily_brief_input
from atlas.capabilities.daily_brief.engine import render_daily_brief_report
from atlas.capabilities.daily_brief.json_loader import (
    load_json_file,
    parse_company_analysis_json,
    parse_discovery_json,
    parse_research_json,
    parse_watchlist_json,
)
from atlas.capabilities.watchlist_intelligence import (
    WatchlistIntelligenceEngine,
    WatchlistIntelligenceInput,
)
from atlas.capabilities.watchlist_intelligence.exporter import watchlist_report_to_dict
from atlas.capabilities.discovery import DiscoveryEngine, DiscoveryInput
from atlas.capabilities.discovery.exporter import discovery_report_to_dict
from atlas.adapters.watchlist import watchlist_input_from_dict
from atlas.adapters.knowledge import knowledge_facts_from_dict
from atlas.adapters.research_input import research_projects_from_dict
from atlas.capabilities.daily_brief.research_exporter import research_projects_to_dict
from atlas.capabilities.company_analysis.exporter import company_reports_to_list
from atlas.capabilities.company_analysis import CompanyAnalysisEngine, CompanyAnalysisInput
from atlas.adapters.company_analysis import company_reports_from_dict
from atlas.shared import Company
from atlas.decision_journal import (
    DecisionJournalEngine,
    render_decision_journal_entries,
    render_decision_journal_entry,
    render_decision_journal_review,
)
from atlas.economics import EconomicSignalsEngine, render_economic_signal_analysis
from atlas.evidence import EvidenceQualityEngine, render_evidence_assessment
from atlas.home import AtlasHomeEngine, AtlasHomeInput, render_atlas_home
from atlas.intelligence import (
    IntelligenceContext,
    IntelligenceEngine,
    IntelligenceInput,
    render_intelligence_report,
)
from atlas.language import AtlasLanguageEngine, render_atlas_language_report
from atlas.market import (
    MarketHealthEngine,
    MarketIndicators,
    MarketRegimeEngine,
    MarketSnapshot,
    render_market_health,
    render_market_regime,
)
from atlas.monitoring import MonitoringAlert, MonitoringEngine, render_monitoring_alert
from atlas.profile import (
    InvestmentGoal,
    InvestorProfile,
    InvestorProfileEngine,
    PortfolioPurpose,
    RiskCapacity,
    RiskPreference,
    RiskTolerance,
    TimeHorizon,
    render_investor_profile,
)
from atlas.principles import PrinciplesEngine, render_principles_check
from atlas.portfolio_review import (
    PortfolioReviewEngine,
    PortfolioReviewInput,
    render_portfolio_review,
)
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider, YahooFinanceProvider
from atlas.reasoning import (
    ReasoningEngine,
    ReasoningInput,
    ReasoningReport,
    render_reasoning_report,
)
from atlas.risk_drift import (
    RiskDriftAssessment,
    RiskDriftEngine,
    RiskDriftInput,
    render_risk_drift_assessment,
)
from atlas.risk import PositionSizingInput, RiskEngine, render_risk_analysis
from atlas.services.database_service import init_database
from atlas.services.company_service import add_company, list_companies
from atlas.services.financial_import_service import import_financials
from atlas.suitability import (
    SuitabilityAssessment,
    SuitabilityEngine,
    SuitabilityInput,
    render_suitability_assessment,
)
from atlas.themes import ThemeEngine, ThemeInput, render_theme_analysis

app = typer.Typer(help="Atlas investment research platform")
company_analysis_app = typer.Typer(help="Company analysis export commands")
dashboard_app = typer.Typer(help="Atlas home dashboard commands")
daily_app = typer.Typer(help="Atlas daily briefing commands")
discovery_app = typer.Typer(help="Discovery capability commands")
economics_app = typer.Typer(help="Economic signals commands")
evidence_app = typer.Typer(help="Evidence quality commands")
intelligence_app = typer.Typer(help="Atlas intelligence synthesis commands")
journal_app = typer.Typer(help="Decision journal commands")
language_app = typer.Typer(help="Atlas language and rating commands")
memory_app = typer.Typer(help="Investment memory commands")
market_app = typer.Typer(help="Market regime commands")
portfolio_app = typer.Typer(help="Portfolio intelligence commands")
profile_app = typer.Typer(help="Investor profile context commands")
principles_app = typer.Typer(help="Atlas principles validation commands")
reason_app = typer.Typer(help="Atlas reasoning thesis commands")
research_app = typer.Typer(help="Research export commands")
risk_drift_app = typer.Typer(help="Risk drift review commands")
risk_app = typer.Typer(help="Risk and position sizing commands")
suitability_app = typer.Typer(help="Investor suitability context commands")
theme_app = typer.Typer(help="Theme intelligence commands")
watchlist_app = typer.Typer(help="Watchlist intelligence commands")
app.add_typer(company_analysis_app, name="company-analysis")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(daily_app, name="daily")
app.add_typer(discovery_app, name="discovery")
app.add_typer(economics_app, name="economics")
app.add_typer(evidence_app, name="evidence")
app.add_typer(intelligence_app, name="intelligence")
app.add_typer(journal_app, name="journal")
app.add_typer(language_app, name="language")
app.add_typer(memory_app, name="memory")
app.add_typer(market_app, name="market")
app.add_typer(portfolio_app, name="portfolio")
app.add_typer(profile_app, name="profile")
app.add_typer(principles_app, name="principles")
app.add_typer(reason_app, name="reason")
app.add_typer(research_app, name="research")
app.add_typer(risk_drift_app, name="risk-drift")
app.add_typer(risk_app, name="risk")
app.add_typer(suitability_app, name="suitability")
app.add_typer(theme_app, name="theme")
app.add_typer(watchlist_app, name="watchlist")
console = Console()

@app.command()
def init():
    """Initialize the Atlas SQLite database."""
    path = init_database()
    console.print(f"[green]Atlas database initialized:[/green] {path}")

@app.command("add-company")
def add_company_command(
    ticker: str,
    name: str = typer.Option(..., help="Company name"),
    atlas_id: str = typer.Option(..., help="Atlas ID, e.g. AI-001"),
    exchange: str = typer.Option(None),
    country: str = typer.Option(None),
    currency: str = typer.Option("USD"),
    sector: str = typer.Option(None),
    industry: str = typer.Option(None),
):
    """Add a company to Atlas."""
    company = add_company(
        ticker=ticker,
        name=name,
        atlas_id=atlas_id,
        exchange=exchange,
        country=country,
        currency=currency,
        sector=sector,
        industry=industry,
    )
    console.print(f"[green]Company ready:[/green] {company.atlas_id} {company.name} ({company.ticker})")

@app.command("list-companies")
def list_companies_command():
    """List companies in Atlas."""
    companies = list_companies()
    table = Table(title="Atlas Companies")
    table.add_column("Atlas ID")
    table.add_column("Ticker")
    table.add_column("Name")
    table.add_column("Status")
    for c in companies:
        table.add_row(c.atlas_id, c.ticker, c.name, c.status or "")
    console.print(table)

@app.command("report")
def report_command(
    ticker: str,
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Generate a formatted investment report."""
    try:
        provider = _provider_from_name(provider_name)
        analysis = provider.get_company_analysis(ticker)
    except (LookupError, ValueError) as exc:
        console.print(f"[red]Report failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    report = build_investment_report(analysis)
    console.print(render_investment_report(report))


@app.command("monitor")
def monitor_command(
    inputs: list[str] = typer.Argument(...),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Compare deterministic monitoring snapshots for a company, portfolio, or theme."""
    try:
        provider = _provider_from_name(provider_name)
        alert = _monitor_from_inputs(inputs, provider)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Monitoring failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_monitoring_alert(alert))


@app.command("import-financials")
def import_financials_command(ticker: str, csv_path: Path):
    """Import annual financial history from CSV."""
    try:
        imported_count = import_financials(ticker=ticker, csv_path=csv_path)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Import failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]Imported financial history:[/green] {imported_count} rows for {ticker.upper()}"
    )

@app.command("analyze")
def analyze_command(
    ticker: str,
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Generate a structured company intelligence report."""
    try:
        provider = _provider_from_name(provider_name)
        analysis = provider.get_company_analysis(ticker)
    except (LookupError, ValueError) as exc:
        console.print(f"[red]Analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    report = build_investment_report(analysis)
    console.print(render_investment_report(report))


@app.command("ask")
def ask_command(
    question: str,
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    ticker: str | None = typer.Option(None, "--ticker", help="Ticker context"),
    portfolio_path: Path | None = typer.Option(None, "--portfolio", help="Portfolio JSON path"),
    watchlist_path: Path | None = typer.Option(None, "--watchlist", help="Watchlist JSON path"),
    theme: str = typer.Option("AI infrastructure", "--theme", help="Theme template context"),
):
    """Answer a natural investment question using deterministic Atlas routing."""
    try:
        provider = _provider_from_name(provider_name)
        portfolio = Portfolio.from_json_file(portfolio_path) if portfolio_path else None
        watchlist = Watchlist.from_json_file(watchlist_path) if watchlist_path else None
        response = ConversationEngine().answer(
            ConversationInput(
                question=question,
                provider=provider,
                ticker=ticker,
                portfolio=portfolio,
                watchlist=watchlist,
                theme=theme,
            )
        )
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Conversation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_conversation_response(response))


@app.command("home")
def home_command(
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--profile",
        help="Investor profile JSON path",
    ),
    portfolio_path: Path | None = typer.Option(
        None,
        "--portfolio",
        help="Portfolio JSON path",
    ),
    watchlist_path: Path | None = typer.Option(
        None,
        "--watchlist",
        help="Watchlist JSON path",
    ),
    journal_path: Path = typer.Option(
        Path(".atlas/decision_journal.json"),
        "--journal",
        help="Decision journal JSON path",
    ),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Show the primary Atlas Home briefing."""
    try:
        provider = _provider_from_name(provider_name)
        profile = _profile_from_path_or_default(profile_path)
        portfolio = Portfolio.from_json_file(portfolio_path) if portfolio_path else None
        watchlist = Watchlist.from_json_file(watchlist_path) if watchlist_path else None
        output = AtlasHomeEngine().build(
            AtlasHomeInput(
                investor_profile=profile,
                portfolio=portfolio,
                watchlist=watchlist,
                provider=provider,
                journal_path=journal_path,
            )
        )
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Home failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_atlas_home(output))


@app.command("compare")
def compare_command(
    ideas: list[str] | None = typer.Argument(
        None,
        help="Two or more companies, themes, ETFs, or ideas. Uses demo mode when omitted.",
    ),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Compare investment ideas with deterministic Atlas reasoning."""
    try:
        provider = _provider_from_name(provider_name)
        comparison_input = (
            InvestmentComparisonInput(ideas=tuple(ideas), provider=provider)
            if ideas
            else demo_investment_comparison_input(provider=provider)
        )
        result = InvestmentComparisonEngine().compare(comparison_input)
    except (LookupError, ValueError) as exc:
        console.print(f"[red]Comparison failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_investment_comparison(result))


@dashboard_app.command("show")
def dashboard_show_command(
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--profile",
        help="Investor profile JSON path",
    ),
    portfolio_path: Path | None = typer.Option(
        None,
        "--portfolio",
        help="Portfolio JSON path",
    ),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    ticker: str | None = typer.Option(
        None,
        "--ticker",
        help="Optional ticker for target portfolio-fit context",
    ),
):
    """Show the Atlas home dashboard briefing."""
    try:
        provider = _provider_from_name(provider_name)
        profile = _profile_from_path_or_default(profile_path)
        portfolio = Portfolio.from_json_file(portfolio_path) if portfolio_path else None
        summary = DashboardEngine().build(
            DashboardInput(
                investor_profile=profile,
                portfolio=portfolio,
                provider=provider,
                target_ticker=ticker,
            )
        )
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Dashboard failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_dashboard(summary))


@daily_app.command("brief")
def daily_brief_command(
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--profile",
        help="Investor profile JSON path",
    ),
    portfolio_path: Path | None = typer.Option(
        None,
        "--portfolio",
        help="Portfolio JSON path",
    ),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    ticker: str | None = typer.Option(
        None,
        "--ticker",
        help="Optional ticker for dashboard context",
    ),
):
    """Show a calm deterministic Atlas Daily briefing."""
    try:
        provider = _provider_from_name(provider_name)
        profile = _profile_from_path_or_default(profile_path)
        portfolio = Portfolio.from_json_file(portfolio_path) if portfolio_path else None
        brief = DailyBriefEngine().build(
            DailyBriefInput(
                investor_profile=profile,
                portfolio=portfolio,
                provider=provider,
                target_ticker=ticker,
            )
        )
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Daily brief failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_daily_brief(brief))


@daily_app.command("summary")
def daily_summary_command(
    portfolio_path: Path | None = typer.Option(
        None, "--portfolio", help="Portfolio JSON path (optional)",
    ),
    research_path: Path | None = typer.Option(
        None, "--research", help="Research JSON path (optional)",
    ),
    watchlist_path: Path | None = typer.Option(
        None, "--watchlist", help="Watchlist intelligence JSON path (optional)",
    ),
    discovery_path: Path | None = typer.Option(
        None, "--discovery", help="Discovery report JSON path (optional)",
    ),
    company_analysis_path: Path | None = typer.Option(
        None, "--company-analysis", help="Company analysis JSON path (optional)",
    ),
):
    """Show a deterministic Daily Brief from Blueprint-aligned domain inputs.

    All flags are optional. With no flags the brief reports no meaningful
    developments. Each flag accepts a local JSON file — no network calls
    are made regardless of which flags are provided.
    """
    try:
        portfolio_summary_data = None
        if portfolio_path is not None:
            legacy_portfolio = Portfolio.from_json_file(portfolio_path)
            domain_portfolio = legacy_portfolio_to_domain_portfolio(legacy_portfolio)
            portfolio_summary_data = domain_portfolio_summary(domain_portfolio)

        research_notes: tuple = ()
        extra_questions: tuple[str, ...] = ()
        if research_path is not None:
            raw = load_json_file(research_path)
            research_notes, extra_questions = parse_research_json(raw, research_path)

        watchlist_report = None
        if watchlist_path is not None:
            raw = load_json_file(watchlist_path)
            watchlist_report = parse_watchlist_json(raw, watchlist_path)

        discovery_report = None
        if discovery_path is not None:
            raw = load_json_file(discovery_path)
            discovery_report = parse_discovery_json(raw, discovery_path)

        company_reports: tuple = ()
        if company_analysis_path is not None:
            raw = load_json_file(company_analysis_path)
            company_reports = parse_company_analysis_json(raw, company_analysis_path)

        brief_input = build_daily_brief_input(
            portfolio_summary=portfolio_summary_data,
            research_notes=research_notes,
            company_reports=company_reports,
            watchlist_report=watchlist_report,
            discovery_report=discovery_report,
            open_research_questions=extra_questions,
        )
        brief = DailyBriefCapability().generate(brief_input)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Daily summary failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_daily_brief_report(brief))


@economics_app.command("analyze")
def economics_analyze_command():
    """Analyze deterministic macro and financial signal groups."""
    analysis = EconomicSignalsEngine().analyze()
    console.print(render_economic_signal_analysis(analysis))


@evidence_app.command("assess")
def evidence_assess_command():
    """Show an example deterministic evidence quality assessment."""
    assessment = EvidenceQualityEngine().example_assessment()
    console.print(render_evidence_assessment(assessment))


@intelligence_app.command("analyze")
def intelligence_analyze_command(
    inputs: list[str] = typer.Argument(...),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    theme: str = typer.Option("AI infrastructure", "--theme", help="Theme template to include"),
):
    """Synthesize Atlas engine outputs into one deterministic intelligence report."""
    try:
        portfolio, ticker = _parse_intelligence_inputs(inputs)
        provider = _provider_from_name(provider_name)
        report = IntelligenceEngine().analyze(
            IntelligenceInput(
                ticker=ticker,
                provider=provider,
                context=IntelligenceContext(portfolio=portfolio, theme=theme),
            )
        )
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Intelligence analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_intelligence_report(report))


@journal_app.command("create")
def journal_create_command(
    journal_path: Path = typer.Option(
        Path(".atlas/decision_journal.json"),
        "--path",
        help="Decision journal JSON path",
    ),
):
    """Create a deterministic demo decision journal entry."""
    try:
        engine = DecisionJournalEngine()
        entry = engine.save_entry(engine.demo_entry(), journal_path)
    except ValueError as exc:
        console.print(f"[red]Journal create failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_decision_journal_entry(entry))


@journal_app.command("list")
def journal_list_command(
    journal_path: Path = typer.Option(
        Path(".atlas/decision_journal.json"),
        "--path",
        help="Decision journal JSON path",
    ),
):
    """List local decision journal entries."""
    try:
        entries = DecisionJournalEngine().load_entries(journal_path)
    except ValueError as exc:
        console.print(f"[red]Journal list failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_decision_journal_entries(entries))


@journal_app.command("review")
def journal_review_command(
    journal_path: Path = typer.Option(
        Path(".atlas/decision_journal.json"),
        "--path",
        help="Decision journal JSON path",
    ),
):
    """Review the latest decision journal entry, or a deterministic demo entry."""
    try:
        engine = DecisionJournalEngine()
        entries = engine.load_entries(journal_path)
        entry = entries[-1] if entries else engine.demo_entry()
        review = engine.review_entry(entry)
    except ValueError as exc:
        console.print(f"[red]Journal review failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_decision_journal_review(review))


@language_app.command("explain")
def language_explain_command():
    """Show an example Atlas language and rating report."""
    report = AtlasLanguageEngine().example_report()
    console.print(render_atlas_language_report(report))


@memory_app.command("save")
def memory_save_command(ticker: str, memory_path: Path):
    """Save the current Atlas analysis for a ticker to JSON memory."""
    provider = MockCompanyAnalysisProvider()
    try:
        entry = MemoryEngine().save_ticker(
            store=MemoryStore(memory_path),
            ticker=ticker,
            provider=provider,
        )
    except LookupError as exc:
        console.print(f"[red]Memory save failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]Memory saved:[/green] {entry.ticker} at {entry.timestamp} "
        f"({entry.atlas_score}/100, {entry.recommendation})"
    )


@memory_app.command("show")
def memory_show_command(memory_path: Path):
    """Show saved Atlas memory entries."""
    try:
        entries = MemoryEngine().load(MemoryStore(memory_path))
    except ValueError as exc:
        console.print(f"[red]Memory show failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_memory_entries(entries))


@memory_app.command("compare")
def memory_compare_command(memory_path: Path, ticker: str):
    """Compare the two latest memory entries for a ticker."""
    try:
        comparison = MemoryEngine().compare(MemoryStore(memory_path), ticker)
    except ValueError as exc:
        console.print(f"[red]Memory compare failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_memory_comparison(comparison))


@market_app.command("analyze")
def market_analyze_command(market_path: Path):
    """Analyze the current market regime from JSON indicators."""
    try:
        snapshot = MarketSnapshot.from_json_file(market_path)
        analysis = MarketRegimeEngine().analyze(snapshot)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Market analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_market_regime(analysis))


@market_app.command("health")
def market_health_command():
    """Assess deterministic market health signal groups."""
    report = MarketHealthEngine().analyze()
    console.print(render_market_health(report))


@portfolio_app.command("analyze")
def portfolio_analyze_command(
    portfolio_path: Path,
    ticker: str,
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Analyze a company in the context of an existing portfolio."""
    try:
        provider = _provider_from_name(provider_name)
        portfolio = Portfolio.from_json_file(portfolio_path)
        analysis = PortfolioIntelligenceEngine().analyze_ticker(
            portfolio=portfolio,
            ticker=ticker,
            provider=provider,
        )
        domain_summary = domain_portfolio_summary(legacy_portfolio_to_domain_portfolio(portfolio))
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Portfolio analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_portfolio_analysis(analysis))
    console.print("")
    console.print(_render_portfolio_domain_summary(domain_summary))


@portfolio_app.command("summary")
def portfolio_summary_command(portfolio_path: Path):
    """Show a deterministic Portfolio Domain summary (read-only, no provider calls)."""
    try:
        legacy_portfolio = Portfolio.from_json_file(portfolio_path)
        domain_portfolio = legacy_portfolio_to_domain_portfolio(legacy_portfolio)
        summary = domain_portfolio_summary(domain_portfolio)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Portfolio summary failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(_render_portfolio_domain_summary(summary))


@portfolio_app.command("review")
def portfolio_review_command(
    portfolio_path: Path,
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--profile",
        help="Investor profile JSON path",
    ),
    market_path: Path | None = typer.Option(
        None,
        "--market",
        help="Optional market snapshot JSON path",
    ),
):
    """Generate a CIO-style portfolio review."""
    try:
        portfolio = Portfolio.from_json_file(portfolio_path)
        profile = _profile_from_path_or_default(profile_path)
        market_snapshot = MarketSnapshot.from_json_file(market_path) if market_path else None
        report = PortfolioReviewEngine().review(
            PortfolioReviewInput(
                portfolio=portfolio,
                investor_profile=profile,
                market_snapshot=market_snapshot,
            )
        )
        domain_summary = domain_portfolio_summary(legacy_portfolio_to_domain_portfolio(portfolio))
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Portfolio review failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_portfolio_review(report))
    console.print("")
    console.print(_render_portfolio_domain_summary(domain_summary))


@profile_app.command("create")
def profile_create_command(
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--path",
        help="Investor profile JSON path",
    ),
    name: str = typer.Option("Atlas Investor", "--name", help="Investor profile name"),
    goals: list[str] | None = typer.Option(
        None,
        "--goal",
        help="Investment goal. Repeat this option to set multiple goals.",
    ),
    portfolio_purpose: str = typer.Option(
        "Core Portfolio",
        "--purpose",
        help="Portfolio purpose",
    ),
    risk_preference: str = typer.Option(
        "Balanced",
        "--risk-profile",
        help="Risk profile preference",
    ),
    risk_tolerance: str = typer.Option(
        "Balanced",
        "--risk-tolerance",
        help="Emotional risk tolerance",
    ),
    risk_capacity: str = typer.Option(
        "Medium",
        "--risk-capacity",
        help="Financial risk capacity",
    ),
    time_horizon: str = typer.Option(
        "10+ years",
        "--time-horizon",
        help="Investment time horizon",
    ),
    notes: str = typer.Option("", "--notes", help="Optional investor notes"),
):
    """Create an investor profile JSON file."""
    try:
        engine = InvestorProfileEngine()
        profile = engine.create_profile(
            name=name,
            investment_goals=_parse_profile_goals(goals),
            portfolio_purpose=_parse_profile_enum(PortfolioPurpose, portfolio_purpose),
            risk_preference=_parse_profile_enum(RiskPreference, risk_preference),
            risk_tolerance=_parse_profile_enum(RiskTolerance, risk_tolerance),
            risk_capacity=_parse_profile_enum(RiskCapacity, risk_capacity),
            time_horizon=_parse_profile_enum(TimeHorizon, time_horizon),
            notes=notes,
        )
        engine.save_profile(profile, profile_path)
    except ValueError as exc:
        console.print(f"[red]Profile create failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_investor_profile(profile))


@profile_app.command("show")
def profile_show_command(
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--path",
        help="Investor profile JSON path",
    ),
):
    """Show an investor profile."""
    try:
        profile = InvestorProfileEngine().load_profile(profile_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Profile show failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_investor_profile(profile))


@profile_app.command("update")
def profile_update_command(
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--path",
        help="Investor profile JSON path",
    ),
    name: str | None = typer.Option(None, "--name", help="Investor profile name"),
    goals: list[str] | None = typer.Option(
        None,
        "--goal",
        help="Replace goals. Repeat this option to set multiple goals.",
    ),
    portfolio_purpose: str | None = typer.Option(
        None,
        "--purpose",
        help="Portfolio purpose",
    ),
    risk_preference: str | None = typer.Option(
        None,
        "--risk-profile",
        help="Risk profile preference",
    ),
    risk_tolerance: str | None = typer.Option(
        None,
        "--risk-tolerance",
        help="Emotional risk tolerance",
    ),
    risk_capacity: str | None = typer.Option(
        None,
        "--risk-capacity",
        help="Financial risk capacity",
    ),
    time_horizon: str | None = typer.Option(
        None,
        "--time-horizon",
        help="Investment time horizon",
    ),
    notes: str | None = typer.Option(None, "--notes", help="Optional investor notes"),
):
    """Update an existing investor profile JSON file."""
    try:
        engine = InvestorProfileEngine()
        profile = engine.load_profile(profile_path)
        updated = engine.update_profile(
            profile,
            name=name,
            investment_goals=_parse_profile_goals(goals) if goals else None,
            portfolio_purpose=_optional_profile_enum(
                PortfolioPurpose,
                portfolio_purpose,
            ),
            risk_preference=_optional_profile_enum(RiskPreference, risk_preference),
            risk_tolerance=_optional_profile_enum(RiskTolerance, risk_tolerance),
            risk_capacity=_optional_profile_enum(RiskCapacity, risk_capacity),
            time_horizon=_optional_profile_enum(TimeHorizon, time_horizon),
            notes=notes,
        )
        engine.save_profile(updated, profile_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Profile update failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_investor_profile(updated))


@principles_app.command("check")
def principles_check_command(text: str):
    """Validate text against Atlas communication principles and guardrails."""
    check = PrinciplesEngine().check(text)
    console.print(render_principles_check(check))


@reason_app.command("analyze")
def reason_analyze_command(
    ticker: str = typer.Option("NVDA", "--ticker", help="Ticker context"),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    theme: str = typer.Option("AI infrastructure", "--theme", help="Theme template context"),
):
    """Synthesize existing Atlas outputs into one deterministic investment thesis."""
    try:
        provider = _provider_from_name(provider_name)
        report = _build_reasoning_report(ticker=ticker, provider=provider, theme=theme)
    except (LookupError, ValueError) as exc:
        console.print(f"[red]Reasoning failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_reasoning_report(report))


@risk_drift_app.command("analyze")
def risk_drift_analyze_command(
    original_profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--original-profile",
        help="Original investor profile JSON path",
    ),
    current_profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--current-profile",
        help="Current investor profile JSON path",
    ),
    portfolio_path: Path | None = typer.Option(
        None,
        "--portfolio",
        help="Current portfolio JSON path",
    ),
    original_portfolio_size: float | None = typer.Option(
        None,
        "--original-portfolio-size",
        help="Original portfolio size",
    ),
    current_portfolio_size: float | None = typer.Option(
        None,
        "--current-portfolio-size",
        help="Current portfolio size",
    ),
    original_largest_position_weight: float | None = typer.Option(
        None,
        "--original-largest-weight",
        help="Original largest position weight, such as 0.15",
    ),
    current_largest_position_weight: float | None = typer.Option(
        None,
        "--current-largest-weight",
        help="Current largest position weight, such as 0.35",
    ),
    volatility_exposure: str | None = typer.Option(
        None,
        "--volatility",
        help="Current volatility exposure: low, medium, high, elevated, or aggressive",
    ),
):
    """Detect drift between original profile assumptions and current context."""
    try:
        assessment = _build_risk_drift_assessment(
            original_profile_path=original_profile_path,
            current_profile_path=current_profile_path,
            portfolio_path=portfolio_path,
            original_portfolio_size=original_portfolio_size,
            current_portfolio_size=current_portfolio_size,
            original_largest_position_weight=original_largest_position_weight,
            current_largest_position_weight=current_largest_position_weight,
            volatility_exposure=volatility_exposure,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Risk drift analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_risk_drift_assessment(assessment))


@risk_app.command("size")
def risk_size_command(risk_input_path: Path):
    """Analyze position size, liquidity, concentration, and deployment pacing."""
    try:
        sizing_input = PositionSizingInput.from_json_file(risk_input_path)
        analysis = RiskEngine().analyze(sizing_input)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Risk sizing failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_risk_analysis(analysis))


@suitability_app.command("analyze")
def suitability_analyze_command(
    subject: str,
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--profile",
        help="Investor profile JSON path",
    ),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    theme: str = typer.Option("AI infrastructure", "--theme", help="Theme template context"),
):
    """Assess profile compatibility for a ticker or portfolio JSON file."""
    try:
        provider = _provider_from_name(provider_name)
        profile = _profile_from_path_or_default(profile_path)
        assessment = _build_suitability_assessment(
            subject=subject,
            profile=profile,
            provider=provider,
            theme=theme,
        )
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Suitability analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_suitability_assessment(assessment))


@theme_app.command("analyze")
def theme_analyze_command(theme: str):
    """Analyze an investment theme with deterministic Atlas templates."""
    try:
        analysis = ThemeEngine().analyze(ThemeInput(theme=theme))
    except ValueError as exc:
        console.print(f"[red]Theme analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_theme_analysis(analysis))


@watchlist_app.command("intelligence")
def watchlist_intelligence_command(
    input_path: Path | None = typer.Option(
        None, "--input", help="Local watchlist JSON file path (optional).",
    ),
    output_path: Path | None = typer.Option(
        None, "--output", help="Write JSON export to this file path.",
    ),
):
    """Generate a Blueprint-aligned Watchlist Intelligence report.

    Runs WatchlistIntelligenceEngine on the supplied input (or an empty input
    when --input is omitted) and either prints a human-readable summary or
    writes a JSON export to --output. The JSON export is compatible with
    `atlas daily summary --watchlist` and `atlas discovery export --watchlist`.
    """
    try:
        if input_path is not None:
            raw = load_json_file(input_path)
            wi_input = watchlist_input_from_dict(raw, str(input_path))
        else:
            wi_input = WatchlistIntelligenceInput(name="My Watchlist")
        report = WatchlistIntelligenceEngine().analyze(wi_input)
        if output_path is not None:
            _write_json_export(output_path, watchlist_report_to_dict(report))
            console.print(f"Watchlist Intelligence report written to {output_path}")
            return
    except (OSError, ValueError) as exc:
        console.print(f"[red]Watchlist intelligence failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    lines = [
        "Watchlist Intelligence",
        "",
        report.overview,
    ]
    if report.open_questions:
        lines += ["", "Open Questions"]
        for q in report.open_questions:
            lines.append(f"  - {q.question}")
    if report.suggested_next_research_steps:
        lines += ["", "Suggested Next Research Steps"]
        for step in report.suggested_next_research_steps:
            lines.append(f"  - {step}")
    if not report.open_questions and not report.companies_needing_attention:
        lines += ["", "No items require attention at this time."]
    console.print("\n".join(lines))


@discovery_app.command("export")
def discovery_export_command(
    knowledge_path: Path | None = typer.Option(
        None, "--knowledge", help="Local knowledge JSON file path (optional).",
    ),
    research_path: Path | None = typer.Option(
        None, "--research", help="Local research JSON file path (optional).",
    ),
    watchlist_path: Path | None = typer.Option(
        None, "--watchlist", help="Local watchlist JSON file path (optional).",
    ),
    output_path: Path | None = typer.Option(
        None, "--output", help="Write JSON export to this file path.",
    ),
):
    """Generate a Blueprint-aligned Discovery report.

    Runs DiscoveryEngine on the supplied structured inputs (or an empty input
    when no flags are provided) and either prints a human-readable summary or
    writes a JSON export to --output. The JSON export is compatible with
    `atlas daily summary --discovery`.

    --knowledge  Local knowledge JSON (facts array)
    --research   Local research JSON (projects array with open questions)
    --watchlist  Local watchlist JSON (items array) — runs Watchlist
                 Intelligence first, then feeds the report into Discovery
    """
    try:
        knowledge_facts = ()
        if knowledge_path is not None:
            raw = load_json_file(knowledge_path)
            knowledge_facts = knowledge_facts_from_dict(raw, str(knowledge_path))

        research_projects = ()
        if research_path is not None:
            raw = load_json_file(research_path)
            research_projects = research_projects_from_dict(raw, str(research_path))

        watchlist_reports = ()
        if watchlist_path is not None:
            raw = load_json_file(watchlist_path)
            wi_input = watchlist_input_from_dict(raw, str(watchlist_path))
            watchlist_reports = (WatchlistIntelligenceEngine().analyze(wi_input),)

        report = DiscoveryEngine().discover(
            DiscoveryInput(
                knowledge_facts=knowledge_facts,
                research_projects=research_projects,
                watchlist_intelligence_reports=watchlist_reports,
            )
        )
        if output_path is not None:
            _write_json_export(output_path, discovery_report_to_dict(report))
            console.print(f"Discovery report written to {output_path}")
            return
    except (OSError, ValueError) as exc:
        console.print(f"[red]Discovery export failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    lines = [
        "Discovery",
        "",
        report.summary,
    ]
    if report.candidates:
        lines += ["", "Candidates"]
        for c in report.candidates:
            lines.append(f"  {c.identifier}: {c.title} ({c.priority.value})")
    else:
        lines += ["", "No discovery candidates identified from available inputs."]
    console.print("\n".join(lines))


@research_app.command("export")
def research_export_command(
    input_path: Path | None = typer.Option(
        None, "--input", help="Local research JSON file (projects format, optional).",
    ),
    output_path: Path | None = typer.Option(
        None, "--output", help="Write research JSON to this file path.",
    ),
):
    """Export research projects as a Daily Brief–compatible research JSON file.

    Reads a local research JSON file (``{"projects": [...]}``) via --input,
    converts open questions and project summaries to the format accepted by
    ``atlas daily summary --research``, and writes the result to --output.

    When --input is omitted the command runs with no projects (useful to verify
    the empty-export format). When --output is omitted the result is printed
    to stdout as a human-readable summary.

    No network calls are made. No recommendations are produced.
    """
    try:
        if input_path is not None:
            raw = load_json_file(input_path)
            projects = research_projects_from_dict(raw, str(input_path))
        else:
            projects = ()
        data = research_projects_to_dict(projects)
        if output_path is not None:
            _write_json_export(output_path, data)
            console.print(f"Research export written to {output_path}")
            return
    except (OSError, ValueError) as exc:
        console.print(f"[red]Research export failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    lines = ["Research Export", ""]
    if data["notes"]:
        lines.append(f"Projects: {len(data['notes'])}")
        for note in data["notes"]:
            lines.append(f"  - {note['title']} ({note['body']})")
    else:
        lines.append("No research projects.")
    if data["open_questions"]:
        lines += ["", "Open Questions"]
        for q in data["open_questions"]:
            lines.append(f"  - {q}")
    else:
        lines += ["", "No open questions."]
    console.print("\n".join(lines))


@company_analysis_app.command("export")
def company_analysis_export_command(
    input_path: Path | None = typer.Option(
        None, "--input", help="Local company analysis JSON file path (Sprint 54 path, optional).",
    ),
    ticker: str | None = typer.Option(
        None, "--ticker", help="Company ticker for engine-backed export (e.g. AMD).",
    ),
    company_name: str | None = typer.Option(
        None, "--company-name", help="Human-readable company name (e.g. 'AMD Corporation').",
    ),
    business_description: str | None = typer.Option(
        None, "--business-description", help="Plain-text business description (local only).",
    ),
    knowledge_path: Path | None = typer.Option(
        None, "--knowledge", help="Local knowledge JSON file path (optional).",
    ),
    research_path: Path | None = typer.Option(
        None, "--research", help="Local research JSON file path (optional).",
    ),
    output_path: Path | None = typer.Option(
        None, "--output", help="Write company analysis JSON to this file path.",
    ),
):
    """Export company analysis context as a Daily Brief–compatible JSON file.

    Two export paths are available:

    **Engine-backed export** (Sprint 55–56): provide --ticker and optionally
    --company-name, --business-description, --knowledge, and/or --research.
    CompanyAnalysisEngine runs deterministically on the supplied local inputs.

    .. code-block:: bash

        atlas company-analysis export \\
          --ticker AMD \\
          --company-name "AMD Corporation" \\
          --business-description "AMD designs high-performance CPUs and GPUs." \\
          --knowledge knowledge.json \\
          --research research.json \\
          --output company.json

    **Manual input export** (Sprint 54): provide --input with a pre-authored
    company analysis JSON file. The file is validated and re-exported.

    When neither --ticker nor --input is provided the command exports an empty
    list, valid for ``atlas daily summary --company-analysis``.

    No network calls are made. No recommendations are produced.
    """
    try:
        if ticker is not None:
            # Engine-backed path (Sprint 55–56)
            ticker_upper = ticker.strip().upper()
            if not ticker_upper:
                raise ValueError("--ticker must not be empty")

            resolved_name = (company_name or "").strip() or ticker_upper
            resolved_description = (business_description or "").strip()

            knowledge_facts = ()
            if knowledge_path is not None:
                raw = load_json_file(knowledge_path)
                knowledge_facts = knowledge_facts_from_dict(raw, str(knowledge_path))

            research_project = None
            if research_path is not None:
                raw = load_json_file(research_path)
                projects = research_projects_from_dict(raw, str(research_path))
                # Use the first project whose topic matches the ticker, or the first overall.
                research_project = next(
                    (p for p in projects if p.topic.upper() == ticker_upper),
                    projects[0] if projects else None,
                )

            company = Company(
                id=ticker_upper.lower(),
                name=resolved_name,
                ticker=ticker_upper,
            )
            analysis_input = CompanyAnalysisInput(
                company=company,
                business_description=resolved_description,
                knowledge_facts=knowledge_facts,
                research_project=research_project,
            )
            report = CompanyAnalysisEngine().analyze(analysis_input)
            data = [company_reports_to_list((report,))[0]]

        elif input_path is not None:
            # Manual input path (Sprint 54)
            raw = load_json_file(input_path)
            reports = company_reports_from_dict(raw, str(input_path))
            data = company_reports_to_list(reports)

        else:
            # No-input path
            data = []

        if output_path is not None:
            _write_json_export(output_path, data)
            console.print(f"Company analysis export written to {output_path}")
            return

    except (OSError, ValueError) as exc:
        console.print(f"[red]Company analysis export failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    lines = ["Company Analysis Export", ""]
    if data:
        lines.append(f"Reports: {len(data)}")
        for report_dict in data:
            company_d = report_dict.get("company", {})
            name = company_d.get("name", "Unknown")
            tick = company_d.get("ticker", "")
            confidence = report_dict.get("confidence", {})
            level = confidence.get("level", "") if isinstance(confidence, dict) else str(confidence)
            lines.append(f"  - {name} ({tick}): confidence {level}")
            unknowns = report_dict.get("unknowns", [])
            if unknowns:
                lines.append(f"    Unknowns: {len(unknowns)}")
    else:
        lines.append("No company analysis inputs provided.")
        lines.append("Export produces an empty list compatible with atlas daily summary --company-analysis.")
    console.print("\n".join(lines))


@watchlist_app.command("analyze")
def watchlist_analyze_command(
    watchlist_path: Path,
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Analyze opportunities across a watchlist."""
    try:
        provider = _provider_from_name(provider_name)
        watchlist = Watchlist.from_json_file(watchlist_path)
        analysis = WatchlistEngine().analyze(watchlist=watchlist, provider=provider)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Watchlist analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_watchlist_analysis(analysis))


@watchlist_app.command("review")
def watchlist_review_command(
    watchlist_path: Path | None = typer.Argument(
        None,
        help="Optional watchlist JSON path. Uses demo mode when omitted.",
    ),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
    profile_path: Path = typer.Option(
        Path("atlas_profile.json"),
        "--profile",
        help="Investor profile JSON path",
    ),
):
    """Generate a CIO-style watchlist review."""
    try:
        provider = _provider_from_name(provider_name)
        profile = _profile_from_path_or_default(profile_path)
        review_input = (
            watchlist_review_input_from_json_file(
                watchlist_path,
                provider=provider,
                investor_profile=profile,
            )
            if watchlist_path
            else demo_watchlist_review_input(provider=provider, investor_profile=profile)
        )
        report = WatchlistReviewEngine().review(review_input)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Watchlist review failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_watchlist_review(report))


def _write_json_export(path: Path, data: dict) -> None:
    """Write a JSON-serializable dict to a local file. Raises OSError on failure."""
    import json
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _render_portfolio_domain_summary(summary) -> str:
    lines = [
        "Portfolio Summary (Portfolio Domain)",
        "",
        f"Portfolio: {summary.portfolio_name} ({summary.portfolio_id})",
        f"Number of holdings: {summary.number_of_holdings}",
        f"Largest weight: {summary.largest_weight:.1%}",
        f"Cash weight: {summary.cash_weight:.1%}",
        f"Concentration: {summary.concentration.level.value}",
        "",
        "Sector Allocation",
    ]
    for allocation in summary.sector_allocation:
        lines.append(f"  {allocation.name}: {allocation.weight:.1%}")
    lines.append("")
    lines.append("Country Allocation")
    for allocation in summary.country_allocation:
        lines.append(f"  {allocation.name}: {allocation.weight:.1%}")
    lines.append("")
    lines.append("Top Holdings")
    for holding in summary.top_holdings:
        lines.append(f"  {holding.ticker}")
    return "\n".join(lines)


def _provider_from_name(provider_name: str) -> CompanyDataProvider:
    normalized = provider_name.strip().lower()
    if normalized == "mock":
        return MockCompanyAnalysisProvider()
    if normalized == "yahoo":
        return YahooFinanceProvider()
    raise ValueError("Unknown provider. Use 'mock' or 'yahoo'.")


def _parse_intelligence_inputs(inputs: list[str]) -> tuple[Portfolio | None, str]:
    if len(inputs) == 1:
        return None, inputs[0].upper()
    if len(inputs) == 2:
        return Portfolio.from_json_file(Path(inputs[0])), inputs[1].upper()
    raise ValueError("Use 'atlas intelligence analyze TICKER' or 'portfolio.json TICKER'.")


def _parse_profile_goals(goals: list[str] | None) -> tuple[InvestmentGoal, ...]:
    raw_goals = goals or [InvestmentGoal.WEALTH_ACCUMULATION.value]
    return tuple(_parse_profile_enum(InvestmentGoal, goal) for goal in raw_goals)


def _optional_profile_enum(enum_type, raw_value: str | None):
    if raw_value is None:
        return None
    return _parse_profile_enum(enum_type, raw_value)


def _parse_profile_enum(enum_type, raw_value: str):
    normalized = raw_value.strip().lower().replace("_", " ").replace("-", " ")
    for item in enum_type:
        if normalized in {
            item.name.lower().replace("_", " "),
            item.value.lower().replace("-", " "),
        }:
            return item
    valid = ", ".join(item.value for item in enum_type)
    raise ValueError(f"Unknown {enum_type.__name__}: {raw_value}. Valid values: {valid}")


def _profile_from_path_or_default(profile_path: Path) -> InvestorProfile:
    engine = InvestorProfileEngine()
    if profile_path.exists():
        return engine.load_profile(profile_path)
    return engine.create_default_profile()


def _build_suitability_assessment(
    subject: str,
    profile: InvestorProfile,
    provider: CompanyDataProvider,
    theme: str,
) -> SuitabilityAssessment:
    engine = SuitabilityEngine()
    if subject.lower().endswith(".json"):
        portfolio = Portfolio.from_json_file(Path(subject))
        return engine.assess(
            SuitabilityInput(
                investor_profile=profile,
                portfolio=portfolio,
            )
        )

    ticker = subject.upper()
    investment_report = build_investment_report(provider.get_company_analysis(ticker))
    theme_analysis = ThemeEngine().analyze(ThemeInput(theme=theme))
    intelligence_report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker=ticker,
            provider=provider,
            context=IntelligenceContext(theme=theme),
        )
    )
    return engine.assess(
        SuitabilityInput(
            investor_profile=profile,
            ticker=ticker,
            investment_report=investment_report,
            theme_analysis=theme_analysis,
            intelligence_report=intelligence_report,
        )
    )


def _build_risk_drift_assessment(
    original_profile_path: Path,
    current_profile_path: Path,
    portfolio_path: Path | None,
    original_portfolio_size: float | None,
    current_portfolio_size: float | None,
    original_largest_position_weight: float | None,
    current_largest_position_weight: float | None,
    volatility_exposure: str | None,
) -> RiskDriftAssessment:
    original_profile = _profile_from_path_or_default(original_profile_path)
    current_profile = _profile_from_path_or_default(current_profile_path)
    current_portfolio = Portfolio.from_json_file(portfolio_path) if portfolio_path else None
    market_regime = MarketRegimeEngine().analyze(
        MarketSnapshot(
            indicators=MarketIndicators(
                sp500_drawdown=-0.08,
                nasdaq_drawdown=-0.12,
                vix=22,
                interest_rate_trend="stable",
                inflation_trend="stable",
            ),
            source="deterministic-risk-drift-placeholder",
        )
    )
    return RiskDriftEngine().assess(
        RiskDriftInput(
            original_profile=original_profile,
            current_profile=current_profile,
            current_portfolio=current_portfolio,
            original_market_regime=None,
            current_market_regime=market_regime,
            current_market_health=MarketHealthEngine().analyze(),
            current_economic_signals=EconomicSignalsEngine().analyze(),
            original_portfolio_size=original_portfolio_size,
            current_portfolio_size=current_portfolio_size,
            original_largest_position_weight=original_largest_position_weight,
            current_largest_position_weight=current_largest_position_weight,
            volatility_exposure=volatility_exposure,
        )
    )


def _monitor_from_inputs(
    inputs: list[str],
    provider: CompanyDataProvider,
) -> MonitoringAlert:
    engine = MonitoringEngine()
    if not inputs:
        raise ValueError("Use 'atlas monitor TICKER', 'portfolio.json', or 'theme NAME'.")
    command = inputs[0].strip().lower()
    if command == "theme":
        if len(inputs) < 2:
            raise ValueError("Use 'atlas monitor theme THEME_NAME'.")
        return engine.monitor_theme(" ".join(inputs[1:]))
    if command == "watchlist":
        if len(inputs) != 2:
            raise ValueError("Use 'atlas monitor watchlist watchlist.json'.")
        return engine.monitor_watchlist(Watchlist.from_json_file(Path(inputs[1])), provider)
    if command in {"market-health", "health"} or inputs == ["market", "health"]:
        return engine.monitor_market_health()
    if command in {"market-regime", "regime"}:
        return engine.monitor_market_regime()
    if len(inputs) == 1 and inputs[0].lower().endswith(".json"):
        return engine.monitor_portfolio(Portfolio.from_json_file(Path(inputs[0])))
    if len(inputs) == 1:
        return engine.monitor_company(inputs[0], provider)
    raise ValueError("Use 'atlas monitor TICKER', 'portfolio.json', or 'theme NAME'.")


def _build_reasoning_report(
    ticker: str,
    provider: CompanyDataProvider,
    theme: str,
) -> ReasoningReport:
    company_analysis = provider.get_company_analysis(ticker)
    investment_report = build_investment_report(company_analysis)
    theme_analysis = ThemeEngine().analyze(ThemeInput(theme=theme))
    monitoring_report = MonitoringEngine().monitor_company(ticker, provider)
    economic_signals = EconomicSignalsEngine().analyze()
    market_health = MarketHealthEngine().analyze()
    market_regime = MarketRegimeEngine().analyze(
        MarketSnapshot(
            indicators=MarketIndicators(
                sp500_drawdown=-0.04,
                nasdaq_drawdown=-0.07,
                vix=19,
                interest_rate_trend="stable",
                inflation_trend="stable",
            ),
            source="deterministic-placeholder",
        )
    )
    return ReasoningEngine().analyze(
        ReasoningInput(
            company_analysis=investment_report,
            theme_analysis=theme_analysis,
            monitoring_report=monitoring_report,
            economic_signals=economic_signals,
            market_health=market_health,
            market_regime=market_regime,
        )
    )
