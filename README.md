# Product Inventory Tracker

A configurable Python web-scraping portfolio project that collects product information from a practice e-commerce catalogue, exports inventory to CSV and Excel, and compares runs to identify inventory changes.

> **Demo project, not paid client work.** The default target is [Books to Scrape](https://books.toscrape.com/), a fictional bookstore built for scraping practice. Its prices and ratings are demonstration data, not real market information. This project demonstrates a reusable scraping workflow; it is not a universal scraper that works with every online shop without adaptation.

## Features

- **Catalogue crawling:** Follows pagination to collect products across the configured catalogue.
- **Product data extraction:** Collects product URLs, titles, displayed prices, availability, ratings and scrape timestamps from catalogue pages. It visits product-detail pages to retrieve additional fields when available, such as UPC, product type, tax-inclusive and tax-exclusive prices, tax, category, description and review count.
- **Configurable selectors:** Reads the starting URL and CSS selectors from `config.json`, so website-specific settings do not have to be edited directly in the scraper source.
- **Deduplication:** Uses product URLs to avoid duplicate records and identify products across inventory snapshots.
- **Request resilience:** Uses request timeouts, limited retries, a descriptive User-Agent and delays between requests. If a product-detail page fails, the catalogue information for that product is retained and the failure is recorded.
- **CSV and Excel export:** Produces CSV files and formatted `.xlsx` workbooks with filters, frozen header rows and clickable product links.
- **Inventory change tracking:** Compares complete inventory snapshots to identify new products, removed products, price changes and availability changes.
- **Preview runs:** Runs limited with `--max-pages` produce preview files without replacing the current full inventory or creating a historical baseline.
- **Automated tests:** Tests cover parsing, configuration validation, snapshot comparisons, error handling and Excel export.
- **Cross-platform launch scripts:** Includes launch scripts for Windows and macOS/Linux.
- **Requirements:** Python 3.10 or newer.

## Quick start

### Requirements

- Python 3.10 or newer
- Internet access to retrieve the public demo website

### Windows (PowerShell)

Open a terminal in the project root, the folder containing `main.py` and `config.json`, and run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run a small preview first:

```powershell
python main.py run --max-pages 2
```

Run the complete catalogue:

```powershell
python main.py run
```

You can also double-click `run_windows.bat` for a full run. To pass command-line options through the launcher, use:

```powershell
.\run_windows.bat --max-pages 2
```

If PowerShell blocks environment activation, use `run_windows.bat` after setup or invoke the environment's Python directly:

```powershell
.venv\Scripts\python.exe main.py run --max-pages 2
```

### macOS / Linux

From the project root:

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh --max-pages 2
```

Remove `--max-pages 2` for a complete run. The launcher creates the virtual environment and installs dependencies on first use.

### Run the tests

Activate the project's virtual environment first, then run:

```powershell
python -m unittest discover -s tests -v
```

The unit tests use controlled examples for parsing, comparison, resilience and export checks. Passing the unit tests does not replace an end-to-end test against the live practice website.

## Configuration

The default configuration is stored in `config.json` in the project root. It defines the website name, starting URL and CSS selectors used to locate catalogue cards, product links, prices, pagination and product-detail elements.

Example:

```json
{
  "site_name": "Books to Scrape",
  "start_url": "https://books.toscrape.com/catalogue/page-1.html",
  "selectors": {
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
    "description": "#product_description + p"
  }
}
```

The configuration can be specified explicitly:

```powershell
python main.py run --config config.json --max-pages 2
```

Configuration makes the project easier to adapt to websites with compatible HTML structures. It does not guarantee compatibility with every e-commerce platform. Different field labels, unusual pagination, JavaScript-rendered content, authentication or other site-specific behaviour may require changes to the parsing logic or a different scraping approach.

## Output files

Generated files are written under `data/`.

### Preview run (`--max-pages 2`)

```text
data/
├── preview_inventory.csv
├── preview_inventory.xlsx
└── reports/
    └── detail_failures_<timestamp>.csv  # Only if detail pages fail
```

Preview runs are intended for testing. They do not update the current full inventory or create a full-inventory snapshot.

### Full run

```text
data/
├── current_inventory.csv
├── current_inventory.xlsx
├── snapshots/
│   └── inventory_<timestamp>.csv
└── reports/
    ├── changes_<timestamp>.csv
    ├── changes_<timestamp>.xlsx
    └── detail_failures_<timestamp>.csv  # Only if detail pages fail
```

The first complete run establishes a baseline. Later complete runs compare the current inventory against the preceding saved snapshot. A change report may contain no changes if the practice catalogue has remained the same between runs.

A failed product-detail request is recorded in the failure report, while available catalogue data is retained. A failed catalogue-page crawl stops the run rather than treating an incomplete crawl as a complete inventory.

## Data fields

The inventory export includes these fields when available:

| Field | Description |
|---|---|
| `product_url` | Product detail URL; used for deduplication and comparison |
| `title` | Product title |
| `upc` | UPC identifier supplied by the demo website |
| `sku` | SKU, when the target website provides one |
| `brand` | Brand, when the target website provides one |
| `price_gbp` | Displayed catalogue price as a number in GBP |
| `price_excl_tax` | Detail-page price excluding tax, when available |
| `price_incl_tax` | Detail-page price including tax, when available |
| `tax` | Tax information supplied by the detail page |
| `availability` | Availability text from the catalogue page |
| `rating` | Demo rating from 1 to 5, when available |
| `category` | Product category, when available |
| `product_type` | Product type supplied by the detail page |
| `review_count` | Number of reviews, when available |
| `description` | Product description, when available |
| `scraped_at` | Timestamp associated with the scrape |

Missing fields are left blank rather than fabricated. Books to Scrape provides a UPC rather than a retailer SKU, and it does not expose a normal brand field in the extracted product information. Therefore, the `sku` and `brand` columns may be empty for the default target.

## Project structure

```text
product_inventory_tracker/
├── config.json                   # Website URL and CSS selectors
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── run_windows.bat               # Windows launcher
├── run_mac_linux.sh              # macOS/Linux launcher
├── inventory_tracker/
│   ├── config.py                 # Configuration loading and validation
│   ├── scraper.py                # HTTP requests, parsing and pagination
│   ├── compare.py                # Snapshot comparison
│   └── cli.py                    # Commands and output files
├── tests/
│   ├── test_config.py
│   ├── test_compare.py
│   ├── test_exports.py
│   └── test_scraper.py
└── data/                         # Generated inventory and reports
```

## Technical approach

- **Requests:** Downloads HTML pages.
- **Beautiful Soup:** Parses HTML and extracts fields using CSS selectors.
- **Python standard library:** Handles CSV files, timestamps, URL resolution and much of the application workflow.
- **openpyxl:** Creates formatted Excel workbooks.
- **unittest:** Runs the automated test suite.

The current implementation uses conventional HTTP requests and HTML parsing. It does not use Scrapy, Selenium or Playwright. Browser automation may be appropriate for a future target that requires JavaScript rendering, but only after inspecting the target and checking permitted access methods.

## Limitations and responsible use

This is a portfolio project and a starting point for site-specific work, not a guarantee of production reliability or compatibility with arbitrary websites. Real shops have different HTML structures and may render data using JavaScript, require authentication, impose rate limits or restrict automated access.

Before adapting the scraper to a real website:

1. Check the site's terms, robots.txt guidance, applicable law and data-access policy.
2. Prefer an official API or authorised export where available.
3. Agree with the client on target pages, fields, volume, update frequency and output format.
4. Keep request rates reasonable and do not bypass authentication, access controls or anti-bot protections.
5. Test pagination and field selectors, and confirm that a crawl is complete before relying on product-removal reports.

This repository is a personal portfolio project, not a claim of previous paid client delivery. It demonstrates a reusable workflow that can be adapted after the target website and requirements are understood.