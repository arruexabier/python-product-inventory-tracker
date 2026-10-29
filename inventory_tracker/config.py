"""Load and validate website-specific scraper settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_SITE_NAME = "Books to Scrape"

DEFAULT_START_URL = (
    "https://books.toscrape.com/catalogue/page-1.html"
)

DEFAULT_SELECTORS = {
    "product_card": "article.product_pod",
    "product_link": "h3 a",
    "product_price": "p.price_color",
    "availability": "p.availability",
    "rating": "p.star-rating",
    "next_page": "li.next a",
    "detail_title": ".product_main h1",
    "detail_rows": "table.table-striped tr",
    "detail_label": "th",
    "detail_value": "td",
    "breadcrumb_links": "ul.breadcrumb li a",
    "description": "#product_description + p",
}

REQUIRED_SELECTORS = {
    "product_card",
    "product_link",
    "product_price",
    "next_page",
    "detail_title",
    "detail_rows",
    "detail_label",
    "detail_value",
}


@dataclass(frozen=True)
class ScraperConfig:
    """Settings needed to scrape one supported website."""

    site_name: str
    start_url: str
    selectors: dict[str, str]


def load_config(path: str | Path) -> ScraperConfig:
    """Read and validate a JSON scraper configuration."""

    config_path = Path(path)

    try:
        data = json.loads(
            config_path.read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise ValueError(
            f"Configuration file not found: {config_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {config_path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"Cannot read configuration file {config_path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "The configuration must be a JSON object."
        )

    site_name = data.get("site_name")
    start_url = data.get("start_url")
    raw_selectors = data.get("selectors")

    if not isinstance(site_name, str) or not site_name.strip():
        raise ValueError(
            "'site_name' must be a non-empty string."
        )

    if not isinstance(start_url, str):
        raise ValueError(
            "'start_url' must be a URL string."
        )

    parsed_url = urlparse(start_url)

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError(
            "'start_url' must be a valid HTTP or HTTPS URL."
        )

    if not isinstance(raw_selectors, dict):
        raise ValueError(
            "'selectors' must be a JSON object."
        )

    unknown_selectors = (
        set(raw_selectors) - set(DEFAULT_SELECTORS)
    )

    if unknown_selectors:
        names = ", ".join(sorted(unknown_selectors))
        raise ValueError(
            f"Unknown selector key(s): {names}"
        )

    selectors: dict[str, str] = {}

    for name in DEFAULT_SELECTORS:
        value = raw_selectors.get(name, "")

        if not isinstance(value, str):
            raise ValueError(
                f"Selector '{name}' must be a string."
            )

        selectors[name] = value.strip()

    missing = [
        name
        for name in REQUIRED_SELECTORS
        if not selectors[name]
    ]

    if missing:
        raise ValueError(
            "Missing required CSS selectors: "
            + ", ".join(sorted(missing))
        )

    return ScraperConfig(
        site_name=site_name.strip(),
        start_url=start_url.strip(),
        selectors=selectors,
    )