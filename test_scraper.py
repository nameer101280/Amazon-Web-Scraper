"""Tests for the Amazon search-results parser, run against saved real HTML."""
import pathlib
import re

import scraper

FIXTURES = pathlib.Path(__file__).parent / "bench" / "fixtures"


def load_fixture(name):
    return (FIXTURES / name).read_bytes()


def test_parse_products_extracts_titles():
    """Every product block on a real page yields a non-empty title.

    Regression guard: the title selector looked for span.a-size-medium,
    but Amazon moved that class onto the h2 itself, so every product was
    dropped and the scrape returned nothing.
    """
    products = scraper.parse_products(load_fixture("usb_hub_p1.html"))

    assert len(products) == 16
    assert all(p["title"] for p in products)
    assert products[0]["title"].startswith("UGREEN USB 3.0 Hub")


def test_parse_products_price_keeps_cents():
    """Price retains its fractional part.

    Regression guard: the old code read only span.a-price-whole, saving
    "8." instead of "8.99" and silently discarding the cents.
    """
    products = scraper.parse_products(load_fixture("usb_hub_p1.html"))
    priced = [p for p in products if p["price"] is not None]

    assert priced, "expected at least one product with a price"
    assert all(re.search(r"\d+\.\d{2}$", p["price"]) for p in priced)


def test_parse_products_keeps_products_that_have_no_price():
    """Sponsored and unavailable listings have no price but are still products.

    Regression guard: the old code dropped the entire product if any single
    field was missing, losing ~21% of real results.
    """
    products = scraper.parse_products(load_fixture("usb_hub_p1.html"))

    assert any(p["price"] is None for p in products)
    assert all(p["title"] for p in products)


def test_parse_products_review_count_is_numeric():
    """total_reviews holds a review count, not prose.

    Regression guard: the old selector span.a-size-base is generic, and its
    first match is now a feature blurb, so this field filled with product
    descriptions such as "2 USB-A 3.2 + USB-C 3.2 ...".
    """
    products = scraper.parse_products(load_fixture("usb_hub_p1.html"))
    counted = [p for p in products if p["total_reviews"] is not None]

    assert counted, "expected at least one product with a review count"
    assert all(p["total_reviews"].isdigit() for p in counted)
    assert products[0]["total_reviews"] == "475"


def test_parse_products_extracts_image_url():
    products = scraper.parse_products(load_fixture("usb_hub_p1.html"))

    assert all(p["image_url"].startswith("https://") for p in products)


def test_scrape_amazon_accepts_a_custom_endpoint_and_page_count():
    """The scrape is steerable at its boundaries so it can be measured.

    Benchmarking against the live site measures rate limiting, not code, so
    the endpoint, page count and politeness delay all have to be injectable.
    """
    from bench.mock_server import MockAmazonServer

    with MockAmazonServer(latency=(0, 0)) as server:
        products = scraper.scrape_amazon(
            "usb hub", base_url=server.base_url, pages=3, delay_range=(0, 0)
        )

    assert server.request_count == 3
    assert len(products) > 0
    assert all(p["title"] for p in products)
