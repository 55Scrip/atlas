import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
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
    get_mock_company_portfolio_profile,
    render_portfolio_analysis,
)
from atlas.analysis.report import build_investment_report, render_investment_report
from atlas.analysis.watchlist import Watchlist, WatchlistEngine, render_watchlist_analysis
from atlas.services.database_service import init_database
from atlas.services.company_service import add_company, list_companies
from atlas.services.financial_import_service import import_financials

app = typer.Typer(help="Atlas investment research platform")
memory_app = typer.Typer(help="Investment memory commands")
portfolio_app = typer.Typer(help="Portfolio intelligence commands")
watchlist_app = typer.Typer(help="Watchlist intelligence commands")
app.add_typer(memory_app, name="memory")
app.add_typer(portfolio_app, name="portfolio")
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
def report_command(ticker: str):
    """Generate a formatted investment report."""
    provider = MockCompanyAnalysisProvider()
    try:
        analysis = provider.get_company_analysis(ticker)
    except LookupError as exc:
        console.print(f"[red]Report failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    report = build_investment_report(analysis)
    console.print(render_investment_report(report))

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
def analyze_command(ticker: str):
    """Generate a structured company intelligence report."""
    provider = MockCompanyAnalysisProvider()
    try:
        analysis = provider.get_company_analysis(ticker)
    except LookupError as exc:
        console.print(f"[red]Analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    report = build_investment_report(analysis)
    console.print(render_investment_report(report))


@app.command("compare")
def compare_command(tickers: list[str] = typer.Argument(...)):
    """Compare multiple companies with the Atlas investment engine."""
    if len(tickers) < 2:
        console.print("[red]Comparison failed:[/red] At least two tickers are required.")
        raise typer.Exit(code=1)

    provider = MockCompanyAnalysisProvider()
    analyses = {}
    try:
        for ticker in tickers:
            analyses[ticker.upper()] = provider.get_company_analysis(ticker)
    except LookupError as exc:
        console.print(f"[red]Comparison failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    result = ComparisonEngine().compare(analyses)
    console.print(render_comparison_result(result))


@memory_app.command("save")
def memory_save_command(ticker: str, memory_path: Path):
    """Save the current Atlas analysis for a ticker to JSON memory."""
    provider = MockCompanyAnalysisProvider()
    try:
        analysis = provider.get_company_analysis(ticker)
    except LookupError as exc:
        console.print(f"[red]Memory save failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    report = build_investment_report(analysis)
    entry = MemoryEngine().save(
        store=MemoryStore(memory_path),
        ticker=ticker,
        report=report,
    )
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


@portfolio_app.command("analyze")
def portfolio_analyze_command(portfolio_path: Path, ticker: str):
    """Analyze a company in the context of an existing portfolio."""
    try:
        portfolio = Portfolio.from_json_file(portfolio_path)
        target = get_mock_company_portfolio_profile(ticker)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Portfolio analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    analysis = PortfolioIntelligenceEngine().analyze(portfolio=portfolio, target=target)
    console.print(render_portfolio_analysis(analysis))


@watchlist_app.command("analyze")
def watchlist_analyze_command(watchlist_path: Path):
    """Analyze opportunities across a watchlist."""
    provider = MockCompanyAnalysisProvider()
    try:
        watchlist = Watchlist.from_json_file(watchlist_path)
        analysis = WatchlistEngine().analyze(watchlist=watchlist, provider=provider)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        console.print(f"[red]Watchlist analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(render_watchlist_analysis(analysis))
