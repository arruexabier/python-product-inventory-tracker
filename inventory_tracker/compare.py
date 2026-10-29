"""Compare two inventory snapshots and describe changes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

CHANGE_FIELDS = [
    "change_type",
    "product_url",
    "title",
    "old_price_gbp",
    "new_price_gbp",
    "old_availability",
    "new_availability",
    "detected_at",
]


def _price(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _index(products: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for product in products:
        url = str(product.get("product_url", "")).strip()
        if url:
            indexed[url] = product
    return indexed


def compare_snapshots(
    previous: Iterable[dict[str, Any]],
    current: Iterable[dict[str, Any]],
    detected_at: str | None = None,
) -> list[dict[str, Any]]:
    """Return one row per detected change.

    A product with both a price and availability change produces two rows. Product
    URLs are used as stable identifiers for this demo catalogue.
    """
    old_by_url = _index(previous)
    new_by_url = _index(current)
    timestamp = detected_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    changes: list[dict[str, Any]] = []

    def add_change(
        kind: str,
        url: str,
        title: str,
        old_price: Any = "",
        new_price: Any = "",
        old_stock: Any = "",
        new_stock: Any = "",
    ) -> None:
        changes.append(
            {
                "change_type": kind,
                "product_url": url,
                "title": title,
                "old_price_gbp": "" if old_price is None else old_price,
                "new_price_gbp": "" if new_price is None else new_price,
                "old_availability": "" if old_stock is None else old_stock,
                "new_availability": "" if new_stock is None else new_stock,
                "detected_at": timestamp,
            }
        )

    for url in sorted(new_by_url.keys() - old_by_url.keys()):
        product = new_by_url[url]
        add_change(
            "new_product", url, product.get("title", ""),
            new_price=product.get("price_gbp", ""),
            new_stock=product.get("availability", ""),
        )

    for url in sorted(old_by_url.keys() - new_by_url.keys()):
        product = old_by_url[url]
        add_change(
            "removed_product", url, product.get("title", ""),
            old_price=product.get("price_gbp", ""),
            old_stock=product.get("availability", ""),
        )

    for url in sorted(old_by_url.keys() & new_by_url.keys()):
        old = old_by_url[url]
        new = new_by_url[url]
        title = new.get("title") or old.get("title", "")
        old_price = _price(old.get("price_gbp"))
        new_price = _price(new.get("price_gbp"))
        old_stock = str(old.get("availability", "")).strip()
        new_stock = str(new.get("availability", "")).strip()

        if old_price != new_price:
            add_change(
                "price_changed", url, title,
                old_price=old.get("price_gbp", ""),
                new_price=new.get("price_gbp", ""),
                old_stock=old_stock,
                new_stock=new_stock,
            )
        if old_stock != new_stock:
            add_change(
                "availability_changed", url, title,
                old_price=old.get("price_gbp", ""),
                new_price=new.get("price_gbp", ""),
                old_stock=old_stock,
                new_stock=new_stock,
            )

    return changes
