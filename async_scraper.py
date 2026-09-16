"""Concurrent fetch layer for the Amazon scraper.

Only downloading changes here. Pages are parsed by scraper.parse_products,
the same function the sequential version uses, so the two produce identical
output and a benchmark between them measures the fetch layer alone.

Concurrency is bounded by a semaphore. Unbounded, twenty requests leave at
once, which reads as an attack and gets the client served a bot-verification
page instead of results.
"""
import asyncio
import logging
import random

import httpx

from scraper import (AMAZON_SEARCH_URL, BotCheckError, is_bot_check,
                     parse_products, user_agents as USER_AGENTS)

logging.basicConfig(filename="scraper.log", level=logging.ERROR)

DEFAULT_CONCURRENCY = 5
REQUEST_TIMEOUT = 20.0
DEFAULT_MAX_ATTEMPTS = 3
BOT_CHECK = object()  # sentinel: page was refused, not merely empty
BACKOFF_BASE = 0.5  # seconds; doubles each attempt


def _headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
    }


async def fetch_page(client, semaphore, base_url, query, page, delay_range,
                     max_attempts=DEFAULT_MAX_ATTEMPTS):
    """Fetch one page. Returns (page, html) or (page, None) on failure.

    Failures are contained here rather than raised, so one bad page cannot
    abandon the other nineteen the way the sequential version does.

    Transient errors are retried with exponential backoff. A bot challenge is
    not: it means the rate is already too high, and retrying compounds it.
    """
    async with semaphore:
        if delay_range[1] > 0:
            await asyncio.sleep(random.uniform(*delay_range))

        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.get(
                    base_url,
                    params={"k": query, "ref": "nb_sb_noss_1", "page": page},
                    headers=_headers(),
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                if attempt == max_attempts:
                    logging.error(
                        f"Page {page} failed after {attempt} attempts: {exc}")
                    return page, None
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                logging.error(
                    f"Page {page} attempt {attempt}/{max_attempts} failed "
                    f"({exc}); retrying in {backoff:.1f}s")
                await asyncio.sleep(backoff)
                continue

            if is_bot_check(response.content):
                logging.error(
                    f"Page {page} returned a bot-verification challenge "
                    f"({len(response.content)} bytes); not retrying")
                return page, BOT_CHECK
            return page, response.content


async def scrape_amazon_async(
    query,
    base_url=AMAZON_SEARCH_URL,
    pages=20,
    concurrency=DEFAULT_CONCURRENCY,
    delay_range=(1, 3),
    max_attempts=DEFAULT_MAX_ATTEMPTS,
):
    """Scrape `pages` of results, at most `concurrency` requests in flight.

    Results are ordered by page number so output matches the sequential
    version exactly, regardless of the order replies arrive in.
    """
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [
            fetch_page(client, semaphore, base_url, query, page, delay_range,
                       max_attempts)
            for page in range(1, pages + 1)
        ]
        responses = await asyncio.gather(*tasks)

    products = []
    blocked = 0
    for page, html in sorted(responses, key=lambda r: r[0]):
        if html is BOT_CHECK:
            blocked += 1
            continue
        if html is None:
            continue
        page_products = parse_products(html)
        if not page_products:
            print(f"No product blocks found on page {page} for query '{query}'")
        else:
            print(f"Number of products found on page {page}: {len(page_products)}")
            products.extend(page_products)

    if blocked:
        print(f"WARNING: {blocked}/{pages} pages returned a bot-verification "
              f"challenge. This is rate limiting, not an empty result set.")
        if not products:
            raise BotCheckError(
                f"All {blocked} requested pages were refused with a "
                f"bot-verification challenge - wait before retrying."
            )
    return products


if __name__ == "__main__":
    import data_saver

    search = input("Enter your search query: ")
    scraped = asyncio.run(scrape_amazon_async(search))
    if scraped:
        data_saver.save_data_to_json(scraped, f"{search}.json")
    else:
        print("No data scraped.")
