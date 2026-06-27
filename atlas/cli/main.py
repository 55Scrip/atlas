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
from atlas.economics import EconomicSignalsEngine, render_economic_signal_analysis
from atlas.intelligence import (
    IntelligenceContext,
    IntelligenceEngine,
    IntelligenceInput,
    render_intelligence_report,
)
from atlas.market import (
    MarketHealthEngine,
    MarketIndicators,
    MarketRegimeEngine,
    MarketSnapshot,
    render_market_health,
    render_market_regime,
)
from atlas.monitoring import MonitoringAlert, MonitoringEngine, render_monitoring_alert
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider, YahooFinanceProvider
from atlas.reasoning import (
    ReasoningEngine,
    ReasoningInput,
    ReasoningReport,
    render_reasoning_report,
)
from atlas.risk import PositionSizingInput, RiskEngine, render_risk_analysis
from atlas.services.database_service import init_database
from atlas.services.company_service import add_company, list_companies
from atlas.services.financial_import_service import import_financials
from atlas.themes import ThemeEngine, ThemeInput, render_theme_analysis

app = typer.Typer(help="Atlas investment research platform")
economics_app = typer.Typer(help="Economic signals commands")
intelligence_app = typer.Typer(help="Atlas intelligence synthesis commands")
memory_app = typer.Typer(help="Investment memory commands")
market_app = typer.Typer(help="Market regime commands")
portfolio_app = typer.Typer(help="Portfolio intelligence commands")
reason_app = typer.Typer(help="Atlas reasoning thesis commands")
risk_app = typer.Typer(help="Risk and position sizing commands")
theme_app = typer.Typer(help="Theme intelligence commands")
watchlist_app = typer.Typer(help="Watchlist intelligence commands")
app.add_typer(economics_app, name="economics")
app.add_typer(intelligence_app, name="intelligence")
app.add_typer(memory_app, name="memory")
app.add_typer(market_app, name="market")
app.add_typer(portfolio_app, name="portfolio")
app.add_typer(reason_app, name="reason")
app.add_typer(risk_app, name="risk")
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
