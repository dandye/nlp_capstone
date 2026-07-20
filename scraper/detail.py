import re
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .fetcher import CISAFetcher
from .models import Advisory, AdvisoryStub, CVERef


async def fetch_detail(fetcher: CISAFetcher, stub: AdvisoryStub) -> Advisory:
    """Fetch and parse an advisory detail page."""
    response = await fetcher.get(stub.url.replace(fetcher.base_url, ""))
    soup = BeautifulSoup(response.text, "lxml")

    title = _extract_title(soup)
    advisory_type = _extract_type(soup)
    alert_code = _extract_alert_code(soup)
    release_date = _extract_release_date(soup) or stub.release_date
    body_html = _extract_body_html(soup)
    body_text = _extract_body_text(soup)
    cves = _extract_cves(soup)
    stix_url = _extract_stix_url(soup, fetcher.base_url)
    pdf_url = _extract_pdf_url(soup, fetcher.base_url)

    return Advisory(
        slug=stub.slug,
        url=stub.url,
        title=title or stub.title,
        advisory_type=advisory_type or stub.advisory_type,
        alert_code=alert_code,
        release_date=release_date,
        body_html=body_html,
        body_text=body_text,
        cves=cves,
        stix_url=stix_url,
        pdf_url=pdf_url,
    )


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    elem = soup.find("h1", class_="c-page-title__title")
    if elem:
        span = elem.find("span")
        return span.get_text(strip=True) if span else elem.get_text(strip=True)
    return None


def _extract_type(soup: BeautifulSoup) -> Optional[str]:
    elem = soup.find("div", class_="c-page-title__meta")
    return elem.get_text(strip=True) if elem else None


def _extract_alert_code(soup: BeautifulSoup) -> Optional[str]:
    elem = soup.find("div", class_="c-field--name-field-alert-code")
    if elem:
        content = elem.find("div", class_="c-field__content")
        return content.get_text(strip=True) if content else None
    return None


def _extract_release_date(soup: BeautifulSoup) -> Optional[str]:
    elem = soup.find("div", class_="c-field--name-field-release-date")
    if elem:
        time = elem.find("time")
        return time.get("datetime") if time else None
    return None


def _extract_body_html(soup: BeautifulSoup) -> Optional[str]:
    elem = soup.find("div", class_="c-field--name-body")
    if elem:
        content = elem.find("div", class_="c-field__content")
        return str(content) if content else None
    return None


def _extract_body_text(soup: BeautifulSoup) -> Optional[str]:
    elem = soup.find("div", class_="c-field--name-body")
    if elem:
        content = elem.find("div", class_="c-field__content")
        return content.get_text(separator="\n", strip=True) if content else None
    return None


def _extract_cves(soup: BeautifulSoup) -> list[CVERef]:
    """Extract CVE IDs and severity from advisory body."""
    cves = []
    seen = set()

    elem = soup.find("div", class_="c-field--name-body")
    if not elem:
        return cves

    for link in elem.find_all("a"):
        href = link.get("href", "")
        title = link.get("title", "")

        if "cve.org" in href or "CVE-" in href:
            cve_match = re.search(r"(CVE-\d{4}-\d{4,})", href + " " + link.get_text())
            if cve_match:
                cve_id = cve_match.group(1)
                if cve_id not in seen:
                    severity = _parse_severity(title)
                    cves.append(CVERef(cve_id=cve_id, severity=severity))
                    seen.add(cve_id)

        if "CVE-" in title:
            cve_match = re.search(r"(CVE-\d{4}-\d{4,})", title)
            if cve_match:
                cve_id = cve_match.group(1)
                if cve_id not in seen:
                    severity = _parse_severity(title)
                    cves.append(CVERef(cve_id=cve_id, severity=severity))
                    seen.add(cve_id)

    return cves


def _parse_severity(text: str) -> Optional[str]:
    """Extract severity band from text like 'CVE-XXXX - Critical'."""
    match = re.search(r"(Critical|High|Medium|Low)", text)
    return match.group(1) if match else None


def _extract_stix_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Find STIX JSON download link."""
    for link in soup.find_all("a", class_="c-file__link"):
        href = link.get("href", "")
        if href.endswith(".json") and "stix" in href.lower():
            return urljoin(base_url, href)
    return None


def _extract_pdf_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Find PDF download link."""
    for link in soup.find_all("a", class_="c-file__link"):
        href = link.get("href", "")
        if href.endswith(".pdf"):
            return urljoin(base_url, href)
    return None
