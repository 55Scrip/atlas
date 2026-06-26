import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.comparison import ComparisonEngine, render_comparison_result
from atlas.analysis.portfolio import (
    Portfolio,
    PortfolioIntelligenceEngine,
    get_mock_company_portfolio_profile,
    render_portfolio_analysis,
)
from atlas.analysis.report import build_investment_report, render_investment_report
from atlas.services.database_service import init_database
from atlas.services.company_service import add_company, list_companies
from atlas.services.financial_import_service import import_financials

app = typer.Typer(help="Atlas investment research platform")
portfolio_app = typer.Typer(help="Portfolio intelligence commands")
app.add_typer(portfolio_app, name="portfolio")
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
