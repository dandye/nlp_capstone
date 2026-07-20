import asyncio
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .fetcher import CISAFetcher
from .models import AdvisoryStub


async def fetch_listing_page(fetcher: CISAFetcher, page_num: int, extra_params: str = "") -> list[AdvisoryStub]:
    """Fetch a single listing page and extract advisory stubs."""
    prefix = f"{extra_params}&" if extra_params else ""
    path = f"/news-events/cybersecurity-advisories?{prefix}page={page_num}"
    response = await fetcher.get(path)
    soup = BeautifulSoup(response.text, "lxml")

    stubs = []
    for article in soup.find_all("article", class_="c-teaser--horizontal"):
        try:
            title_link = article.find("h3", class_="c-teaser__title").find("a")
            if not title_link:
                continue

            href = title_link.get("href", "").strip()
            if not href:
                continue

            slug = href.strip("/").split("/")[-1]
            url = urljoin(fetcher.base_url, href)
            title = title_link.find("span").get_text(strip=True) if title_link.find("span") else title_link.get_text(strip=True)

            date_elem = article.find("div", class_="c-teaser__date")
            release_date = date_elem.find("time").get("datetime") if date_elem and date_elem.find("time") else None

            type_elem = article.find("div", class_="c-teaser__meta")
            advisory_type = type_elem.get_text(strip=True) if type_elem else None

            stubs.append(AdvisoryStub(
                slug=slug,
                url=url,
                title=title,
                release_date=release_date,
                advisory_type=advisory_type,
            ))
        except (AttributeError, IndexError):
            continue

    return stubs


async def detect_last_page(fetcher: CISAFetcher, extra_params: str = "") -> int:
    """Detect the total number of pages."""
    prefix = f"{extra_params}&" if extra_params else ""
    response = await fetcher.get(f"/news-events/cybersecurity-advisories?{prefix}page=0")
    soup = BeautifulSoup(response.text, "lxml")

    pager = soup.find("nav", class_="c-pager")
    if not pager:
        return 0

    last_link = pager.find("a", class_="c-pager__link--last")
    if not last_link:
        return 0

    href = last_link.get("href", "")
    if "page=" in href:
        return int(href.split("page=")[-1]) + 1

    return 0


async def paginate(
    fetcher: CISAFetcher,
    start_page: int = 0,
    end_page: Optional[int] = None,
    extra_params: str = "",
) -> list[AdvisoryStub]:
    """Paginate through listing pages and yield stubs."""
    if end_page is None:
        end_page = await detect_last_page(fetcher, extra_params)

    all_stubs = []
    for page_num in range(start_page, end_page):
        stubs = await fetch_listing_page(fetcher, page_num, extra_params)
        all_stubs.extend(stubs)

    return all_stubs
