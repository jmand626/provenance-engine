"""Scrape ALEC model legislation and load it into PostgreSQL."""

from __future__ import annotations

import argparse
import logging
import os
import re
from collections import deque
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

import psycopg2
from bs4 import BeautifulSoup, Tag
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor
from requests import Session
from requests.exceptions import RequestException


ALEC_NAME = "American Legislative Exchange Council"
ALEC_IDEOLOGY = "Conservative"
ALEC_TYPE = "Think Tank"
DEFAULT_BASE_URL = "https://alec.org/model-policy/"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_PAGES = 100

LOGGER = logging.getLogger(__name__)
WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
PARAGRAPH_BREAK_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class PolicyDocument:
    """A model policy page prepared for database insertion."""

    title: str
    source_url: str
    raw_text: str


def configure_logging() -> None:
    """Configure process-level logging for command-line execution."""

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_database_connection() -> PgConnection:
    """Create a PostgreSQL connection from environment variables."""

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "provenance"),
        user=os.getenv("DB_USER", "provenance"),
        password=os.getenv("DB_PASSWORD", "provenance"),
    )


def ensure_alec_organization(conn: PgConnection) -> str:
    """Return ALEC's organization UUID, inserting the row when needed."""

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM organizations WHERE name = %s",
            (ALEC_NAME,),
        )
        existing = cursor.fetchone()
        if existing:
            return str(existing["id"])

        cursor.execute(
            """
            INSERT INTO organizations (name, ideology, organization_type, website_url)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (ALEC_NAME, ALEC_IDEOLOGY, ALEC_TYPE, "https://alec.org/"),
        )
        inserted = cursor.fetchone()
        conn.commit()
        LOGGER.info("Inserted organization row for ALEC")
        return str(inserted["id"])


def normalize_url(url: str) -> str:
    """Normalize URLs enough to deduplicate crawler discoveries."""

    without_fragment, _fragment = urldefrag(url)
    parsed = urlparse(without_fragment)
    normalized_path = parsed.path.rstrip("/") or "/"
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            "",
            parsed.query,
            "",
        )
    )


def is_same_domain(url: str, base_url: str) -> bool:
    """Return whether ``url`` is on the same host as ``base_url``."""

    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def is_policy_url(url: str) -> bool:
    """Return whether a URL looks like an ALEC model policy detail page."""

    parsed = urlparse(url)
    return "model-policy" in parsed.path.lower()


def should_follow_url(url: str) -> bool:
    """Return whether a same-site link is worth crawling for policy discovery."""

    path = urlparse(url).path.lower()
    return "model-policy" in path or "task-force" in path or "model-policies" in path


def fetch_soup(session: Session, url: str, timeout_seconds: int) -> BeautifulSoup:
    """Fetch a URL and parse the response as HTML."""

    response = session.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def discover_policy_urls(
    base_url: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Crawl ALEC listing/task-force pages and collect model policy URLs."""

    session = Session()
    session.headers.update(
        {
            "User-Agent": (
                "ProvenanceEngine/0.1 "
                "(research crawler; contact: local-development@example.invalid)"
            )
        }
    )

    normalized_base_url = normalize_url(base_url)
    queue: deque[str] = deque([normalized_base_url])
    visited: set[str] = set()
    policy_urls: set[str] = set()

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        if current_url in visited:
            continue

        visited.add(current_url)
        try:
            soup = fetch_soup(session, current_url, timeout_seconds)
        except RequestException as exc:
            LOGGER.warning("Failed to fetch discovery page %s: %s", current_url, exc)
            continue

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if not href:
                continue

            absolute_url = normalize_url(urljoin(current_url, href))
            if not is_same_domain(absolute_url, normalized_base_url):
                continue

            if is_policy_url(absolute_url):
                policy_urls.add(absolute_url)

            if should_follow_url(absolute_url) and absolute_url not in visited:
                queue.append(absolute_url)

    LOGGER.info("Discovered %s policy URLs from %s", len(policy_urls), base_url)
    return sorted(policy_urls)


def clean_text_blocks(text_blocks: Iterable[str]) -> str:
    """Normalize whitespace while preserving paragraph separation."""

    paragraphs = []
    for block in text_blocks:
        cleaned = WHITESPACE_RE.sub(" ", block).strip()
        if cleaned:
            paragraphs.append(cleaned)

    return PARAGRAPH_BREAK_RE.sub("\n\n", "\n\n".join(paragraphs)).strip()


def find_content_container(soup: BeautifulSoup) -> Tag | None:
    """Find the most likely primary content container on an ALEC page."""

    article = soup.find("article")
    if isinstance(article, Tag):
        return article

    entry_content = soup.find("div", class_="entry-content")
    if isinstance(entry_content, Tag):
        return entry_content

    main_content = soup.find("main")
    if isinstance(main_content, Tag):
        return main_content

    body = soup.find("body")
    return body if isinstance(body, Tag) else None


def extract_title(soup: BeautifulSoup, source_url: str) -> str:
    """Extract a page title, falling back to the URL slug."""

    heading = soup.find("h1")
    if heading:
        title = heading.get_text(" ", strip=True)
        if title:
            return title[:500]

    if soup.title and soup.title.string:
        return soup.title.string.strip()[:500]

    slug = urlparse(source_url).path.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()[:500] or "Untitled ALEC Model Policy"


def extract_policy_document(
    session: Session,
    source_url: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> PolicyDocument | None:
    """Fetch and extract a single ALEC model policy document."""

    try:
        soup = fetch_soup(session, source_url, timeout_seconds)
    except RequestException as exc:
        LOGGER.warning("Failed to fetch policy page %s: %s", source_url, exc)
        return None

    container = find_content_container(soup)
    if container is None:
        LOGGER.warning("No content container found for %s", source_url)
        return None

    for removable in container.find_all(["script", "style", "noscript", "form"]):
        removable.decompose()

    text_blocks = [
        element.get_text(" ", strip=True)
        for element in container.find_all(["h2", "h3", "h4", "p", "li", "blockquote"])
    ]
    raw_text = clean_text_blocks(text_blocks)
    if not raw_text:
        raw_text = clean_text_blocks([container.get_text("\n\n", strip=True)])

    if not raw_text:
        LOGGER.warning("No extractable policy text found for %s", source_url)
        return None

    return PolicyDocument(
        title=extract_title(soup, source_url),
        source_url=source_url,
        raw_text=raw_text,
    )


def source_url_exists(conn: PgConnection, source_url: str) -> bool:
    """Return whether a model legislation row already exists for a URL."""

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM model_legislation WHERE source_url = %s LIMIT 1",
            (source_url,),
        )
        return cursor.fetchone() is not None


def insert_policy_document(
    conn: PgConnection,
    organization_id: str,
    document: PolicyDocument,
) -> bool:
    """Insert a policy document when its source URL is not already present."""

    if source_url_exists(conn, document.source_url):
        LOGGER.info("Skipping existing policy: %s", document.source_url)
        return False

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO model_legislation (
                organization_id,
                title,
                source_url,
                raw_text
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                organization_id,
                document.title,
                document.source_url,
                document.raw_text,
            ),
        )
        conn.commit()
        LOGGER.info("Inserted policy: %s", document.title)
        return True


def scrape_and_insert_alec_policies(
    base_url: str,
    max_pages: int,
    timeout_seconds: int,
) -> int:
    """Discover, extract, and insert ALEC model policy pages."""

    policy_urls = discover_policy_urls(
        base_url=base_url,
        max_pages=max_pages,
        timeout_seconds=timeout_seconds,
    )

    inserted_count = 0
    session = Session()
    session.headers.update(
        {
            "User-Agent": (
                "ProvenanceEngine/0.1 "
                "(research crawler; contact: local-development@example.invalid)"
            )
        }
    )

    with get_database_connection() as conn:
        organization_id = ensure_alec_organization(conn)
        for policy_url in policy_urls:
            try:
                document = extract_policy_document(session, policy_url, timeout_seconds)
                if document is None:
                    continue

                if insert_policy_document(conn, organization_id, document):
                    inserted_count += 1
            except Exception:
                conn.rollback()
                LOGGER.exception("Failed to process policy URL: %s", policy_url)

    LOGGER.info("Inserted %s new ALEC policies", inserted_count)
    return inserted_count


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Scrape ALEC model policies into the Provenance Engine database."
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("ALEC_BASE_URL", DEFAULT_BASE_URL),
        help="ALEC model policies or task-force listing URL to crawl.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=int(os.getenv("ALEC_MAX_PAGES", str(DEFAULT_MAX_PAGES))),
        help="Maximum discovery pages to crawl before stopping.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=int(os.getenv("REQUEST_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
        help="HTTP request timeout in seconds.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the ALEC scraper from the command line."""

    configure_logging()
    args = parse_args()
    scrape_and_insert_alec_policies(
        base_url=args.base_url,
        max_pages=args.max_pages,
        timeout_seconds=args.timeout_seconds,
    )


if __name__ == "__main__":
    main()
