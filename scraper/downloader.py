import re
from pathlib import Path
from typing import Optional
from .fetcher import CISAFetcher
from .models import Advisory


async def download_file(fetcher: CISAFetcher, url: str, dest_path: Path) -> Optional[Path]:
    """Download a file from URL to destination. Skip if already exists."""
    if not url:
        return None

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        return dest_path

    try:
        response = await fetcher.get(url.replace(fetcher.base_url, ""))
        dest_path.write_bytes(response.content)
        return dest_path
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None


async def download_stix(fetcher: CISAFetcher, advisory: Advisory, data_dir: Path) -> Optional[str]:
    """Download STIX JSON file."""
    if not advisory.stix_url:
        return None

    stix_dir = data_dir / "stix"
    filename = _get_filename(advisory.stix_url, f"{advisory.slug}.json")
    dest_path = stix_dir / filename

    result = await download_file(fetcher, advisory.stix_url, dest_path)
    if result:
        return str(result.relative_to(data_dir))
    return None


async def download_pdf(fetcher: CISAFetcher, advisory: Advisory, data_dir: Path) -> Optional[str]:
    """Download PDF file."""
    if not advisory.pdf_url:
        return None

    pdf_dir = data_dir / "pdfs"
    filename = _get_filename(advisory.pdf_url, f"{advisory.slug}.pdf")
    dest_path = pdf_dir / filename

    result = await download_file(fetcher, advisory.pdf_url, dest_path)
    if result:
        return str(result.relative_to(data_dir))
    return None


def _get_filename(url: str, fallback: str) -> str:
    """Extract filename from URL or use fallback."""
    match = re.search(r"/([^/?#]+)$", url)
    if match:
        return match.group(1)
    return fallback
