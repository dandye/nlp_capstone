"""
Scrape CISA Alerts (advisory_type=93) into a per-advisory directory bundle.

Each advisory gets its own directory:
    data/alerts/{slug}/
        meta.json          — url, title, type, alert_code, release_date, stix_url, pdf_url
        {filename}.pdf     — if available
        {filename}.stix.json — if available

Usage:
    python -m scraper.alerts               # all pages
    python -m scraper.alerts --pages 0-5   # first 5 pages (test)
    python -m scraper.alerts --concurrency 5
    python -m scraper.alerts --data-dir /other/path
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Optional

from .detail import fetch_detail
from .downloader import download_file
from .fetcher import CISAFetcher
from .listing import paginate

def _make_filter(type_id: int) -> str:
    return f"f%5B0%5D=advisory_type%3A{type_id}"


def _filename_from_url(url: str, fallback: str) -> str:
    match = re.search(r"/([^/?#]+)$", url)
    return match.group(1) if match else fallback


async def process_advisory(fetcher: CISAFetcher, stub, alerts_dir: Path) -> str:
    slug_dir = alerts_dir / stub.slug

    # Skip if already done
    if (slug_dir / "meta.json").exists():
        return f"SKIP {stub.slug}"

    try:
        advisory = await fetch_detail(fetcher, stub)

        slug_dir.mkdir(parents=True, exist_ok=True)

        # Download PDF
        if advisory.pdf_url:
            pdf_filename = _filename_from_url(advisory.pdf_url, f"{stub.slug}.pdf")
            await download_file(fetcher, advisory.pdf_url, slug_dir / pdf_filename)

        # Download STIX
        if advisory.stix_url:
            stix_filename = _filename_from_url(advisory.stix_url, f"{stub.slug}.stix.json")
            await download_file(fetcher, advisory.stix_url, slug_dir / stix_filename)

        # Write meta.json
        meta = {
            "url": advisory.url,
            "title": advisory.title,
            "advisory_type": advisory.advisory_type,
            "alert_code": advisory.alert_code,
            "release_date": advisory.release_date,
            "stix_url": advisory.stix_url,
            "pdf_url": advisory.pdf_url,
        }
        (slug_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        return f"OK  {stub.slug} — {advisory.title}"

    except Exception as e:
        return f"ERR {stub.slug}: {e}"


async def run(start_page: int, end_page: Optional[int], data_dir: Path, concurrency: int, type_id: int) -> None:
    alerts_dir = data_dir / "alerts"
    alerts_dir.mkdir(parents=True, exist_ok=True)
    extra_params = _make_filter(type_id)

    async with CISAFetcher(concurrency=concurrency) as fetcher:
        print(f"Paginating advisory_type={type_id}, pages {start_page}–{end_page or 'end'}...")
        stubs = await paginate(fetcher, start_page, end_page, extra_params=extra_params)

        # Deduplicate by slug (CISA listing can return the same slug multiple times)
        seen: set = set()
        unique_stubs = []
        for s in stubs:
            if s.slug not in seen:
                seen.add(s.slug)
                unique_stubs.append(s)
        stubs = unique_stubs

        print(f"Found {len(stubs)} unique advisories. Processing...\n")

        sem = asyncio.Semaphore(concurrency)

        async def bounded(stub):
            async with sem:
                result = await process_advisory(fetcher, stub, alerts_dir)
                print(result)

        await asyncio.gather(*[bounded(stub) for stub in stubs])

    total = sum(1 for _ in alerts_dir.iterdir() if (alerts_dir / _.name / "meta.json").exists())
    print(f"\nDone. {total} advisories in {alerts_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape CISA Alerts into per-advisory directories.")
    parser.add_argument("--pages", metavar="START-END", help="Page range, e.g. 0-10")
    parser.add_argument("--data-dir", default="data", help="Root data directory (default: ./data)")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel detail fetches (default: 3)")
    parser.add_argument("--type", type=int, default=65, dest="type_id",
                        help="Advisory type ID (default: 65 = Analysis Report; 93 = Alert)")
    args = parser.parse_args()

    start_page, end_page = 0, None
    if args.pages:
        parts = args.pages.split("-")
        start_page = int(parts[0])
        end_page = int(parts[1]) + 1 if len(parts) > 1 else start_page + 1

    asyncio.run(run(start_page, end_page, Path(args.data_dir), args.concurrency, args.type_id))


if __name__ == "__main__":
    main()
