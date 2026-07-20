import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime
from .models import Advisory, CVERef


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS advisories (
            slug TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            advisory_type TEXT,
            alert_code TEXT,
            release_date TEXT,
            body_html TEXT,
            body_text TEXT,
            stix_path TEXT,
            pdf_path TEXT,
            pdf_text TEXT,
            last_scraped TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cves (
            advisory_slug TEXT NOT NULL,
            cve_id TEXT NOT NULL,
            severity TEXT,
            PRIMARY KEY (advisory_slug, cve_id)
        )
    """)

    conn.commit()
    return conn


def advisory_exists(conn: sqlite3.Connection, slug: str) -> bool:
    cursor = conn.execute("SELECT 1 FROM advisories WHERE slug = ?", (slug,))
    return cursor.fetchone() is not None


def upsert_advisory(conn: sqlite3.Connection, advisory: Advisory) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    conn.execute("""
        INSERT OR REPLACE INTO advisories
        (slug, url, title, advisory_type, alert_code, release_date, body_html, body_text, stix_path, pdf_path, pdf_text, last_scraped)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        advisory.slug,
        advisory.url,
        advisory.title,
        advisory.advisory_type,
        advisory.alert_code,
        advisory.release_date,
        advisory.body_html,
        advisory.body_text,
        advisory.stix_path,
        advisory.pdf_path,
        advisory.pdf_text,
        now,
    ))
    conn.commit()


def upsert_cves(conn: sqlite3.Connection, slug: str, cves: list[CVERef]) -> None:
    conn.executemany("""
        INSERT OR IGNORE INTO cves (advisory_slug, cve_id, severity)
        VALUES (?, ?, ?)
    """, [(slug, cve.cve_id, cve.severity) for cve in cves])
    conn.commit()


def get_advisory(conn: sqlite3.Connection, slug: str) -> Optional[dict]:
    cursor = conn.execute("SELECT * FROM advisories WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


def list_advisories(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> list[dict]:
    cursor = conn.execute("SELECT * FROM advisories LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]
