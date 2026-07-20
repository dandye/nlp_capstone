from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class CVERef:
    cve_id: str
    severity: Optional[str] = None


@dataclass
class AdvisoryStub:
    slug: str
    url: str
    title: str
    release_date: Optional[str]
    advisory_type: str


@dataclass
class Advisory:
    slug: str
    url: str
    title: str
    advisory_type: str
    alert_code: Optional[str]
    release_date: Optional[str]
    body_html: Optional[str]
    body_text: Optional[str]
    cves: list[CVERef]
    stix_url: Optional[str] = None
    pdf_url: Optional[str] = None
    stix_path: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_text: Optional[str] = None
    last_scraped: Optional[str] = None
