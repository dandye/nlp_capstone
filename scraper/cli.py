import asyncio
import click
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

from .fetcher import CISAFetcher
from .listing import paginate
from .detail import fetch_detail
from .downloader import download_stix, download_pdf
from .pdf_extract import extract_pdf_text
from .db import init_db, advisory_exists, upsert_advisory, upsert_cves
from .models import Advisory

console = Console()


@click.command()
@click.option("--full", is_flag=True, help="Scrape all pages")
@click.option("--since", type=str, help="Only scrape advisories released on or after DATE (YYYY-MM-DD)")
@click.option("--pages", type=str, help="Scrape specific page range (e.g., 0-10)")
@click.option("--force", is_flag=True, help="Re-scrape even if advisory already in DB")
@click.option("--data-dir", type=click.Path(), default="./data", help="Directory for DB and downloads")
@click.option("--concurrency", type=int, default=3, help="Parallel detail page fetches")
def main(full: bool, since: str, pages: str, force: bool, data_dir: str, concurrency: int):
    """Scrape CISA cybersecurity advisories."""
    data_dir_path = Path(data_dir)
    asyncio.run(_main_async(full, since, pages, force, data_dir_path, concurrency))


async def _main_async(
    full: bool,
    since: str,
    pages: str,
    force: bool,
    data_dir: Path,
    concurrency: int,
):
    """Async main function."""
    db_path = data_dir / "advisories.db"
    conn = init_db(db_path)

    start_page = 0
    end_page = None
    since_date = None

    if since:
        try:
            since_date = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            return

    if pages:
        try:
            parts = pages.split("-")
            start_page = int(parts[0])
            end_page = int(parts[1]) + 1 if len(parts) > 1 else None
        except ValueError:
            console.print("[red]Invalid page range format. Use START-END (e.g., 0-10)[/red]")
            return

    async with CISAFetcher(concurrency=concurrency) as fetcher:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            stubs_task = progress.add_task("Fetching listing pages...", total=None)

            stubs = await paginate(fetcher, start_page, end_page)
            progress.update(stubs_task, total=len(stubs), completed=len(stubs))
            progress.update(stubs_task, description="Processing advisories...")

            count = 0
            skipped = 0
            for stub in stubs:
                if since_date:
                    try:
                        stub_date = datetime.fromisoformat(stub.release_date.replace("Z", "+00:00"))
                        if stub_date < since_date:
                            skipped += 1
                            continue
                    except (ValueError, TypeError, AttributeError):
                        pass

                if not force and advisory_exists(conn, stub.slug):
                    skipped += 1
                    continue

                try:
                    advisory = await fetch_detail(fetcher, stub)

                    if advisory.pdf_url:
                        pdf_path = await download_pdf(fetcher, advisory, data_dir)
                        if pdf_path:
                            advisory.pdf_path = pdf_path
                            pdf_full_path = data_dir / pdf_path
                            advisory.pdf_text = extract_pdf_text(pdf_full_path)

                    if advisory.stix_url:
                        stix_path = await download_stix(fetcher, advisory, data_dir)
                        if stix_path:
                            advisory.stix_path = stix_path

                    upsert_advisory(conn, advisory)
                    if advisory.cves:
                        upsert_cves(conn, advisory.slug, advisory.cves)

                    count += 1
                    progress.update(stubs_task, completed=skipped + count)

                except Exception as e:
                    console.print(f"[red]Error processing {stub.slug}: {e}[/red]")
                    skipped += 1

            console.print(f"\n[green]Scraped {count} advisories, skipped {skipped}[/green]")


if __name__ == "__main__":
    main()
