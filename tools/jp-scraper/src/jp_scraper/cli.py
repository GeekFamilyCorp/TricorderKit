from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from jp_scraper.storage.config import load_sources
from jp_scraper.collectors.router import run_source, run_url
from jp_scraper.storage.delta import build_delta
from jp_scraper.reports.summary import build_summary
from jp_scraper.reports.audit import audit_sources

app = typer.Typer(help="Open source web scraper optimized for low-token agent workflows.")
sources_app = typer.Typer()
scrape_app = typer.Typer()
delta_app = typer.Typer()
report_app = typer.Typer()
app.add_typer(sources_app, name="sources")
app.add_typer(scrape_app, name="scrape")
app.add_typer(delta_app, name="delta")
app.add_typer(report_app, name="report")

console = Console()


@sources_app.command("audit")
def sources_audit(config: Optional[Path] = typer.Option(None, help="Path to sources.yaml (default: bundled)")):
    """Audit configured sources and write a compact report."""
    report = audit_sources(config)
    console.print(report)


@scrape_app.command("source")
def scrape_source(
    source: str,
    mode: str = typer.Option("auto", help="auto|rss|http|trafilatura|playwright"),
    config: Optional[Path] = typer.Option(None, help="Path to sources.yaml (default: bundled)"),
    selectors: Optional[Path] = typer.Option(None, help="Path to selectors.yaml (default: bundled)"),
    out: Path = Path("runs"),
):
    """Scrape one configured source and produce JSONL + summary-ready artifacts."""
    run_dir = run_source(source_id=source, mode=mode, config_path=config, selectors_path=selectors, out_root=out)
    console.print(f"[green]Run completed:[/green] {run_dir}")


@scrape_app.command("url")
def scrape_url(
    url: str,
    mode: str = typer.Option("trafilatura", help="http|trafilatura"),
    out: Path = Path("runs"),
):
    """Scrape one URL without adding it to sources.yaml."""
    run_dir = run_url(url=url, mode=mode, out_root=out)
    console.print(f"[green]URL run completed:[/green] {run_dir}")


@delta_app.command("build")
def delta_build(source: str, runs: Path = Path("runs")):
    """Build delta for the latest run of a source."""
    delta_path = build_delta(source, runs)
    console.print(f"[green]Delta written:[/green] {delta_path}")


@report_app.command("summary")
def report_summary(source: str, runs: Path = Path("runs")):
    """Build a short Markdown summary for agents."""
    summary_path = build_summary(source, runs)
    console.print(f"[green]Summary written:[/green] {summary_path}")


if __name__ == "__main__":
    app()
