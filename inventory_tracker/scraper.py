"""Scrape the Books to Scrape demo catalogue."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from inventory_tracker.config import (
    DEFAULT_SELECTORS,
    DEFAULT_SITE_NAME,
    DEFAULT_START_URL,
    ScraperConfig,
)

START_URL = DEFAULT_START_URL

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def parse_price(price_text: str) -> float:
    """Convert a displayed price such as '£51.77' to 51.77."""
    match = re.search(r"\d+(?:\.\d{1,2})?", price_text.replace(",", ""))
    if not match:
        raise ValueError(f"Could not parse price from {price_text!r}")
    return round(float(match.group()), 2)


def parse_product_card(
    card: Tag,
    page_url: str,
    scraped_at: str,
    selectors: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Extract a product using configurable CSS selectors."""

    selectors = (
        DEFAULT_SELECTORS if selectors is None else selectors
    )

    link = (
        card.select_one(selectors["product_link"])
        if selectors["product_link"]
        else None
    )

    price_element = (
        card.select_one(selectors["product_price"])
        if selectors["product_price"]
        else None
    )

    availability_element = (
        card.select_one(selectors["availability"])
        if selectors["availability"]
        else None
    )

    rating_element = (
        card.select_one(selectors["rating"])
        if selectors["rating"]
        else None
    )

    if link is None or price_element is None:
        raise ValueError(
            "A product card is missing its title link or price."
        )

    title = (
        link.get("title") or link.get_text(" ", strip=True)
    ).strip()

    product_url = urljoin(
        page_url,
        str(link.get("href", "")),
    )

    availability = (
        availability_element.get_text(" ", strip=True)
        if availability_element is not None
        else "Unknown"
    )

    rating = None

    if rating_element is not None:
        rating_classes = rating_element.get("class", [])

        rating_words = [
            name
            for name in rating_classes
            if name in RATING_MAP
        ]

        if rating_words:
            rating = RATING_MAP[rating_words[0]]

    return {
        "product_url": product_url,
        "title": title,
        "price_gbp": parse_price(
            price_element.get_text(" ", strip=True)
        ),
        "availability": availability,
        "rating": rating,
        "scraped_at": scraped_at,
    }







def parse_product_details(
    html: str,
    selectors: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Extract additional information from a product detail page."""

    selectors = (
        DEFAULT_SELECTORS if selectors is None else selectors
    )

    soup = BeautifulSoup(html, "html.parser")

    # Convert the product information table into a dictionary.
    table_data: dict[str, str] = {}

    rows = (
        soup.select(selectors["detail_rows"])
        if selectors["detail_rows"]
        else []
    )

    for row in rows:
        label = (
            row.select_one(selectors["detail_label"])
            if selectors["detail_label"]
            else None
        )

        value = (
            row.select_one(selectors["detail_value"])
            if selectors["detail_value"]
            else None
        )

        if label is None or value is None:
            continue

        key = (
            label.get_text(" ", strip=True)
            .rstrip(":")
            .casefold()
        )

        table_data[key] = value.get_text(" ", strip=True)

    # Product title.
    title_element = (
        soup.select_one(selectors["detail_title"])
        if selectors["detail_title"]
        else None
    )

    title = (
        title_element.get_text(" ", strip=True)
        if title_element is not None
        else None
    )

    # Category from breadcrumb links.
    breadcrumb_links = (
        soup.select(selectors["breadcrumb_links"])
        if selectors["breadcrumb_links"]
        else []
    )

    category = (
        breadcrumb_links[-1].get_text(" ", strip=True)
        if len(breadcrumb_links) >= 3
        else None
    )

    # Optional product description.
    description_element = (
        soup.select_one(selectors["description"])
        if selectors["description"]
        else None
    )

    description = (
        description_element.get_text(" ", strip=True)
        if description_element is not None
        else None
    )

    # Convert review count into an integer.
    reviews_text = table_data.get("number of reviews") or ""
    reviews_match = re.search(r"\d+", reviews_text)

    review_count = (
        int(reviews_match.group())
        if reviews_match
        else None
    )

    return {
        "title": title,
        "upc": table_data.get("upc"),
        "sku": table_data.get("sku"),
        "brand": table_data.get("brand"),
        "product_type": table_data.get("product type"),
        "price_excl_tax": table_data.get("price (excl. tax)"),
        "price_incl_tax": table_data.get("price (incl. tax)"),
        "tax": table_data.get("tax"),
        "category": category,
        "description": description,
        "review_count": review_count,
    }






def _get_html(
    session: requests.Session,
    url: str,
    timeout: float,
    max_retries: int,
) -> str:
    """Download one page, retrying transient request failures."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            # Do not repeatedly retry ordinary client errors such as 404.
            if isinstance(exc, requests.HTTPError) and exc.response is not None:
                status = exc.response.status_code
                if 400 <= status < 500 and status != 429:
                    break
            if attempt + 1 < max_retries:
                time.sleep(1.0 * (attempt + 1))

    raise RuntimeError(f"Could not download {url}: {last_error}") from last_error


def scrape_catalogue(
    max_pages: int | None = None,
    delay: float = 0.5,
    timeout: float = 20.0,
    max_retries: int = 3,
    config: ScraperConfig | None = None,
) -> tuple[
    list[dict[str, Any]],   #Collected products.
    int,                    #Number of catalogue pages visited.
    int,                    #Number of duplicate products skipped.
    list[dict[str, str]],   #A list of product-detail failures.
]:
    """Scrape catalogue pages, deduplicating products by canonical product URL.

    Returns (products, pages_visited, duplicates_skipped).
    Set max_pages=1 or 2 for a quick initial test.
    """
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    if delay < 0.2:
        raise ValueError("Use a delay of at least 0.2 seconds between pages")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")

    active_config = config or ScraperConfig(
        site_name=DEFAULT_SITE_NAME,
        start_url=START_URL,
        selectors=DEFAULT_SELECTORS,
    )

    selectors = active_config.selectors


    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ProductInventoryTracker/0.1 (educational portfolio project)",
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    detail_failures: list[dict[str, str]] = []
    pages_visited = 0
    duplicates_skipped = 0
    next_url: str | None = active_config.start_url
    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        while next_url and (max_pages is None or pages_visited < max_pages):
            html = _get_html(session, next_url, timeout, max_retries)
            soup = BeautifulSoup(html, "html.parser")
            pages_visited += 1

            cards = soup.select(selectors["product_card"])
            if not cards:
                raise RuntimeError(
                    f"No product cards found on {next_url}. The site layout may have changed."
                )

            for card in cards:
                # Extract the information available on the catalogue page.
                product = parse_product_card(card, next_url, scraped_at, selectors=selectors)
                product_url = product["product_url"]

                # Skip a duplicate before making another HTTP request.
                if product_url in seen_urls:
                    duplicates_skipped += 1
                    continue

                seen_urls.add(product_url)

                # Try to collect additional information from the detail page.
                try:
                    detail_html = _get_html(
                        session,
                        product_url,
                        timeout,
                        max_retries,
                    )

                    details = parse_product_details(detail_html, selectors=selectors)

                    # A missing title suggests that the expected page structure
                    # was not found. Keep the catalogue data and log the failure.
                    if not details.get("title"):
                        raise ValueError(
                            "Could not find the expected product title "
                            "on the detail page."
                        )

                    # Add successful detail fields without replacing valid
                    # catalogue values with None.
                    product.update(
                        {
                            key: value
                            for key, value in details.items()
                            if value is not None
                        }
                    )

                except (RuntimeError, ValueError) as exc:
                    detail_failures.append(
                        {
                            "product_url": product_url,
                            "title": str(product["title"]),
                            "stage": "product_detail",
                            "error": str(exc),
                        }
                    )

                finally:
                    # Respect the configured delay even when the request fails.
                    time.sleep(delay)

                # Keep the product even when the detail-page request failed.
                products.append(product)



            next_page_selector = selectors["next_page"]
            next_link = (
                soup.select_one(next_page_selector)
                if next_page_selector
                else None
            )
            next_url = (
                urljoin(next_url, str(next_link.get("href")))
                if next_link is not None
                else None
            )

    finally:
        session.close()

    return products, pages_visited, duplicates_skipped, detail_failures
