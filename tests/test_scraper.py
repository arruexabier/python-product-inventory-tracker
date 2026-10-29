import unittest

from bs4 import BeautifulSoup

from unittest.mock import patch

from inventory_tracker.scraper import (
    START_URL,
    parse_product_card,
    parse_price,
    parse_product_details,
    scrape_catalogue,
)

class ParsePriceTests(unittest.TestCase):
    def test_parse_pounds_and_pence(self):
        self.assertEqual(parse_price("£51.77"), 51.77)

    def test_rejects_missing_price(self):
        with self.assertRaises(ValueError):
            parse_price("price unavailable")


class ParseProductCardTests(unittest.TestCase):
    def test_extracts_product_fields(self):
        html = '''
        <article class="product_pod">
          <p class="star-rating Four"></p>
          <h3><a href="sample-book_123/index.html" title="A Sample Book">A Sample...</a></h3>
          <p class="price_color">£12.50</p>
          <p class="instock availability"><i class="icon-ok"></i> In stock (7 available)</p>
        </article>
        '''
        card = BeautifulSoup(html, "html.parser").select_one("article.product_pod")
        product = parse_product_card(
            card,
            "https://books.toscrape.com/catalogue/page-1.html",
            "2026-10-29T10:00:00+00:00",
        )
        self.assertEqual(product["title"], "A Sample Book")
        self.assertEqual(product["price_gbp"], 12.5)
        self.assertEqual(product["availability"], "In stock (7 available)")
        self.assertEqual(product["rating"], 4)
        self.assertEqual(
            product["product_url"],
            "https://books.toscrape.com/catalogue/sample-book_123/index.html",
        )



class ParseProductDetailsTests(unittest.TestCase):
    def test_extracts_product_details(self):
        html = """
        <ul class="breadcrumb">
            <li><a href="/">Home</a></li>
            <li><a href="/books/">Books</a></li>
            <li><a href="/books/poetry/">Poetry</a></li>
            <li class="active">A Sample Book</li>
        </ul>

        <div class="product_main">
            <h1>A Sample Book</h1>
        </div>

        <div id="product_description">
            <h2>Product Description</h2>
        </div>
        <p>A useful description for testing.</p>

        <table class="table table-striped">
            <tr><th>UPC</th><td>abc123</td></tr>
            <tr><th>Product Type</th><td>Books</td></tr>
            <tr><th>Price (excl. tax)</th><td>£10.00</td></tr>
            <tr><th>Price (incl. tax)</th><td>£12.00</td></tr>
            <tr><th>Tax</th><td>£2.00</td></tr>
            <tr><th>Number of reviews</th><td>3</td></tr>
        </table>
        """

        details = parse_product_details(html)

        self.assertEqual(details["title"], "A Sample Book")
        self.assertEqual(details["upc"], "abc123")
        self.assertEqual(details["category"], "Poetry")
        self.assertEqual(details["product_type"], "Books")
        self.assertEqual(details["price_excl_tax"], "£10.00")
        self.assertEqual(details["price_incl_tax"], "£12.00")
        self.assertEqual(details["tax"], "£2.00")
        self.assertEqual(details["review_count"], 3)
        self.assertEqual(
            details["description"],
            "A useful description for testing.",
        )

        # This demo site does not provide these fields.
        self.assertIsNone(details["sku"])
        self.assertIsNone(details["brand"])

    def test_missing_optional_fields_do_not_raise_errors(self):
        html = """
        <html>
            <body>
                <div class="product_main">
                    <h1>Sample Book</h1>
                </div>
            </body>
        </html>
        """

        details = parse_product_details(html)

        self.assertEqual(details["title"], "Sample Book")
        self.assertIsNone(details["upc"])
        self.assertIsNone(details["category"])
        self.assertIsNone(details["review_count"])




class ScrapeResilienceTests(unittest.TestCase):
    def test_detail_failure_keeps_catalogue_product(self):
        catalogue_html = """
        <article class="product_pod">
            <p class="star-rating Three"></p>
            <h3>
                <a href="sample-book_123/index.html"
                   title="A Sample Book">A Sample Book</a>
            </h3>
            <p class="price_color">£12.50</p>
            <p class="availability">In stock</p>
        </article>
        """

        def fake_get_html(session, url, timeout, max_retries):
            if url == START_URL:
                return catalogue_html

            raise RuntimeError("Simulated detail-page failure")

        with patch(
            "inventory_tracker.scraper._get_html",
            side_effect=fake_get_html,
        ):
            products, pages, duplicates, failures = scrape_catalogue(
                max_pages=1,
                delay=0.2,
            )

        self.assertEqual(pages, 1)
        self.assertEqual(duplicates, 0)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["title"], "A Sample Book")
        self.assertEqual(products[0]["price_gbp"], 12.5)

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["title"], "A Sample Book")
        self.assertEqual(failures[0]["stage"], "product_detail")




if __name__ == "__main__":
    unittest.main()
