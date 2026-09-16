# Amazon Web Scraper

Scrapes product listings from Amazon search results — title, price, review count and image URL — and writes them to JSON.

Two fetch layers are included: the original sequential one, and a concurrent one bounded by a semaphore. Both share the same parser, so they return identical output and can be benchmarked against each other.

**Concurrency is roughly 4× faster at a cap of 5** — see [Benchmarks](#benchmarks).

## Before and after

| | Before | After |
|---|---|---|
| Products extracted | **0** — stale selectors dropped every product | 344 per 20 pages |
| 20 pages, no deliberate delay | 19.68s, one page at a time | **4.64s**, up to 5 at a time |
| Price | `"8."` — cents dropped | `"EUR 34.64"` |
| Listings without a price | discarded (~21% of results) | kept, `price: null` |
| One page fails | rest of the scrape abandoned | only that page lost, after 3 attempts |
| Blocked by Amazon | empty file saved, reported as success | `BotCheckError` raised |
| Tests | none | 16 |
| Install | no dependency list | `requirements.txt` |

The "before" timing is the original sequential fetch layer *after* the selector repair — with zero products extracted there was nothing meaningful to time.

## Install

Requires Python 3.10 or newer — the minimum declared by `requests`, `pytest` and other dependencies. Tested on 3.14.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Use

**Concurrent scrape** (recommended):

```bash
python async_scraper.py
```

**Sequential scrape** — the original, kept for comparison:

```bash
python scraper.py
```

Both prompt for a search query and write results to `data/<query>.json`.

**Batch mode** — reads every query in [user_queries.json](user_queries.json):

```bash
python main.py
```

Note that batch mode is 10 queries × 20 pages = 200 requests. Amazon is likely to start refusing partway through.

### From Python

```python
import asyncio
from async_scraper import scrape_amazon_async

products = asyncio.run(scrape_amazon_async("headphones", pages=20, concurrency=5))
```

| Argument | Default | Meaning |
|---|---|---|
| `pages` | 20 | result pages to fetch |
| `concurrency` | 5 | maximum requests in flight |
| `delay_range` | `(1, 3)` | seconds to pause before each request |
| `max_attempts` | 3 | tries per page before giving up |

## Output

```json
{
  "title": "UGREEN USB 3.0 Hub, 4 Ports USB A Splitter",
  "price": "EUR 34.64",
  "total_reviews": "23588",
  "image_url": "https://m.media-amazon.com/images/I/61CFiwFj3KL._AC_UY218_.jpg"
}
```

`price` and `total_reviews` may be `null`. About 21% of real listings — sponsored and unavailable items — carry no price, and those products are kept rather than discarded.

Prices arrive in whatever currency Amazon serves your location, so the symbol is stored as part of the string rather than assumed.

## Benchmarks

20 pages, 3 runs each, against a local server replaying saved real result pages. No deliberate delay on either side.

| Configuration | Mean | Speedup | Products |
|---|---|---|---|
| Sequential (`requests`) | 19.68s | 1.00× | 344 |
| async, cap = 1 | 18.85s | 1.04× | 344 |
| async, cap = 3 | 7.19s | 2.74× | 344 |
| **async, cap = 5** | **4.64s** | **4.24×** | 344 |
| async, cap = 10 | 2.89s | 6.82× | 344 |
| async, cap = 20 | 1.94s | 10.15× | 344 |

The `cap = 1` row is the control: async with a cap of one matches the sequential version, showing the gain comes from concurrency rather than from `httpx` being a faster library than `requests`.

Run-to-run spread was under 1s for sequential and under 0.1s at cap 5, so the cap-5 speedup falls between 4.1× and 4.4× across all runs. A single live check against amazon.com at cap 5 took 5.68s for 20 pages (336 products, no failures); live pages differ from the saved ones, hence the different count.

Reproduce:

```bash
python bench/compare.py
python bench/benchmark.py
```

Neither needs network access. Timings against the live site depend on IP and time of day, so they are not reproducible — hence the local replay server.

## Tests

```bash
python -m pytest -q          # 16 tests
```

No network access required; tests run against saved HTML.

## How it handles trouble

**Bot challenges.** Amazon answers a suspected bot with an Akamai `bm-verify` interstitial at **HTTP 200** — about 2 KB where a real page is ~900 KB, containing no products. Status codes cannot detect this, so the body is inspected for challenge markers. A challenge is reported as a `BotCheckError` rather than recorded as an empty result, and is **never retried**: it means the request rate is already too high.

**Transient failures** — timeouts, connection errors, 5xx — are retried up to `max_attempts` with exponential backoff (0.5s, 1s, 2s).

**Per-page isolation.** In the concurrent layer each page owns its failure, so one bad response costs that page alone. The sequential layer stops at the first error, which is the behaviour it has always had.

**Why bound concurrency.** Unbounded, all 20 requests leave at once, which is what triggers the challenge above. A cap of 20 is only 2.7s faster than a cap of 5 while quadrupling the request rate — a bad trade.

## Layout

```
scraper.py            sequential fetch + the shared parser (parse_products)
async_scraper.py      concurrent fetch, bounded by a semaphore
main.py               batch runner over user_queries.json
query_reader.py       reads the query list
data_saver.py         writes JSON to data/
bench/
  mock_server.py      replays saved pages at a calibrated latency
  benchmark.py        times the sequential layer
  compare.py          sweeps the concurrency cap, sequential vs async
  fixtures/           saved real result pages, plus a challenge sample
test_scraper.py       parser tests
test_async_scraper.py concurrency and equivalence tests
test_bot_check.py     challenge detection and retry tests
```

## Caveats

Amazon's terms prohibit scraping search results, and their markup changes without notice — the selectors here are the part most likely to break. If output suddenly drops to zero, run the tests first; they check the selectors against saved HTML and will point at the broken field.
