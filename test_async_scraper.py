"""Tests for the concurrent fetch layer."""
import asyncio

import pytest

import async_scraper
import scraper
from bench.mock_server import MockAmazonServer


def test_async_returns_identical_results_to_sequential():
    """Concurrency must not change what gets scraped.

    The two fetch layers share one parser, so any difference in output is a
    bug in the concurrent version, not a trade-off. This is what makes the
    before/after benchmark a fair comparison.
    """
    with MockAmazonServer(latency=(0, 0)) as server:
        sequential = scraper.scrape_amazon(
            "usb hub", base_url=server.base_url, pages=10, delay_range=(0, 0)
        )
    with MockAmazonServer(latency=(0, 0)) as server:
        concurrent = asyncio.run(async_scraper.scrape_amazon_async(
            "usb hub", base_url=server.base_url, pages=10,
            concurrency=5, delay_range=(0, 0),
        ))

    assert len(concurrent) == len(sequential)
    assert concurrent == sequential


@pytest.mark.parametrize("cap", [1, 3, 5])
def test_concurrency_never_exceeds_the_cap(cap):
    """The semaphore actually bounds in-flight requests.

    The server records a high-water mark of simultaneous requests. Without a
    working bound this reaches the page count, which is what trips bot
    protection.
    """
    with MockAmazonServer(latency=(0.05, 0.08)) as server:
        asyncio.run(async_scraper.scrape_amazon_async(
            "usb hub", base_url=server.base_url, pages=12,
            concurrency=cap, delay_range=(0, 0),
        ))

    assert server.max_in_flight <= cap
    assert server.request_count == 12


def test_one_failing_page_does_not_lose_the_others():
    """A failed page costs that page only.

    The sequential version raises out of the whole loop on the first bad
    response, abandoning every page after it.
    """
    with MockAmazonServer(latency=(0, 0)) as server:
        server.fail_pages = {3, 7}
        products = asyncio.run(async_scraper.scrape_amazon_async(
            "usb hub", base_url=server.base_url, pages=10,
            concurrency=5, delay_range=(0, 0), max_attempts=3,
        ))

    with MockAmazonServer(latency=(0, 0)) as clean:
        everything = asyncio.run(async_scraper.scrape_amazon_async(
            "usb hub", base_url=clean.base_url, pages=10,
            concurrency=5, delay_range=(0, 0),
        ))

    assert 0 < len(products) < len(everything)
    # 10 pages, plus 2 extra attempts each for the two that keep failing
    assert server.request_count == 10 + 2 * (3 - 1)
