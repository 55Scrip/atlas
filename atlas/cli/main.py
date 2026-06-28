import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from atlas.analysis.comparison import ComparisonEngine, render_comparison_result
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
from atlas.analysis.report import build_investment_report, render_investment_report
from atlas.analysis.watchlist import Watchlist, WatchlistEngine, render_watchlist_analysis
from atlas.conversation import (
    ConversationEngine,
    ConversationInput,
    render_conversation_response,
)
from atlas.dashboard import DashboardEngine, DashboardInput, render_dashboard
from atlas.daily import DailyBriefEngine, DailyBriefInput, render_daily_brief
from atlas.economics import EconomicSignalsEngine, render_economic_signal_analysis
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
dashboard_app = typer.Typer(help="Atlas home dashboard commands")
daily_app = typer.Typer(help="Atlas daily briefing commands")
economics_app = typer.Typer(help="Economic signals commands")
intelligence_app = typer.Typer(help="Atlas intelligence synthesis commands")
language_app = typer.Typer(help="Atlas language and rating commands")
memory_app = typer.Typer(help="Investment memory commands")
market_app = typer.Typer(help="Market regime commands")
portfolio_app = typer.Typer(help="Portfolio intelligence commands")
profile_app = typer.Typer(help="Investor profile context commands")
principles_app = typer.Typer(help="Atlas principles validation commands")
reason_app = typer.Typer(help="Atlas reasoning thesis commands")
risk_drift_app = typer.Typer(help="Risk drift review commands")
risk_app = typer.Typer(help="Risk and position sizing commands")
suitability_app = typer.Typer(help="Investor suitability context commands")
theme_app = typer.Typer(help="Theme intelligence commands")
watchlist_app = typer.Typer(help="Watchlist intelligence commands")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(daily_app, name="daily")
app.add_typer(economics_app, name="economics")
app.add_typer(intelligence_app, name="intelligence")
app.add_typer(language_app, name="language")
app.add_typer(memory_app, name="memory")
app.add_typer(market_app, name="market")
app.add_typer(portfolio_app, name="portfolio")
app.add_typer(profile_app, name="profile")
app.add_typer(principles_app, name="principles")
app.add_typer(reason_app, name="reason")
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


@app.command("compare")
def compare_command(
    tickers: list[str] = typer.Argument(...),
    provider_name: str = typer.Option("mock", "--provider", help="Data provider: mock or yahoo"),
):
    """Compare multiple companies with the Atlas investment engine."""
    if len(tickers) < 2:
        console.print("[red]Comparison failed:[/red] At least two tickers are required.")
        raise typer.Exit(code=1)

    try:
        provider = _provider_from_name(provider_name)
        result = ComparisonEngine().compare_tickers(tickers, provider)
    except (LookupError, ValueError) as exc:
        console.print(f"[red]Comparison failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_comparison_result(result))


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


@economics_app.command("analyze")
def economics_analyze_command():
    """Analyze deterministic macro and financial signal groups."""
    analysis = EconomicSignalsEngine().analyze()
    console.print(render_economic_signal_analysis(analysis))


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
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Portfolio analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_portfolio_analysis(analysis))


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
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Portfolio review failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_portfolio_review(report))


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
