"""Tests for bot-challenge detection and retry behaviour."""
import pathlib

import pytest

import scraper

FIXTURES = pathlib.Path(__file__).parent / "bench" / "fixtures"


def test_detects_the_bot_challenge_page():
    """A challenge page is recognised despite arriving as HTTP 200.

    Amazon answers a suspected bot with an Akamai bm-verify interstitial at
    status 200, so raise_for_status() sees nothing wrong. Without this check
    the scraper reports a clean run and saves an empty file.
    """
    html = (FIXTURES / "bot_check.html").read_bytes()

    assert scraper.is_bot_check(html) is True


def test_does_not_flag_a_real_results_page():
    """A genuine results page must not be mistaken for a challenge."""
    html = (FIXTURES / "usb_hub_p1.html").read_bytes()

    assert scraper.is_bot_check(html) is False


def test_sequential_scrape_reports_a_block_rather_than_no_results():
    """Being blocked is distinguishable from a search returning nothing.

    "No product blocks found" reads as "Amazon has no laptops". The caller
    needs to know the request was refused.
    """
    from bench.mock_server import MockAmazonServer

    with MockAmazonServer(latency=(0, 0)) as server:
        server.bot_check_pages = {1, 2, 3}
        with pytest.raises(scraper.BotCheckError):
            scraper.scrape_amazon(
                "usb hub", base_url=server.base_url, pages=3, delay_range=(0, 0)
            )


def test_async_retries_a_transient_failure_and_recovers():
    """A 503 is retried, so a blip costs latency rather than a page.

    The mock fails a page for the first attempt only; a working retry turns
    that into a complete scrape.
    """
    import asyncio

    import async_scraper
    from bench.mock_server import MockAmazonServer

    with MockAmazonServer(latency=(0, 0)) as server:
        server.fail_pages = {2}
        server.fail_once = True  # clear fail_pages after the first hit
        products = asyncio.run(async_scraper.scrape_amazon_async(
            "usb hub", base_url=server.base_url, pages=4,
            concurrency=2, delay_range=(0, 0), max_attempts=3,
        ))

    assert server.request_count == 5  # 4 pages + 1 retry
    assert len(products) > 0


def test_a_bot_check_is_never_retried():
    """Retrying a challenge immediately makes the block worse.

    Transient server errors deserve another attempt; being told to prove you
    are human does not.
    """
    import asyncio

    import async_scraper
    from bench.mock_server import MockAmazonServer

    with MockAmazonServer(latency=(0, 0)) as server:
        server.bot_check_pages = {1, 2}
        # every page refused, so the scrape reports a block rather than
        # returning an empty list that looks like a successful empty search
        with pytest.raises(scraper.BotCheckError):
            asyncio.run(async_scraper.scrape_amazon_async(
                "usb hub", base_url=server.base_url, pages=2,
                concurrency=2, delay_range=(0, 0), max_attempts=3,
            ))

    assert server.request_count == 2  # one attempt each, no retries
