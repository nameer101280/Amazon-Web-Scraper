"""Before/after comparison: sequential fetch layer vs bounded-concurrency.

Sweeps the concurrency cap and measures each against the same mock server and
the same parser, so the fetch layer is the only thing that differs.

Timings use no deliberate delay on either side. A per-page sleep is a pacing
policy, not fetch-layer work, and it does not carry over to a concurrent
design unchanged - see the note in the comparison report.
"""
import argparse
import asyncio
import contextlib
import io
import json
import pathlib
import statistics
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import async_scraper  # noqa: E402
import scraper  # noqa: E402
from bench.mock_server import MockAmazonServer  # noqa: E402

RESULTS_DIR = pathlib.Path(__file__).parent / "results"
DEFAULT_LATENCY = (0.70, 1.10)
DEFAULT_CAPS = [1, 3, 5, 10, 20]


def time_once(runner, latency, pages):
    """Run one scrape against a fresh server. Returns (seconds, products, server)."""
    with MockAmazonServer(latency=latency) as server:
        with contextlib.redirect_stdout(io.StringIO()):
            start = time.perf_counter()
            products = runner(server.base_url)
            elapsed = time.perf_counter() - start
        return elapsed, products, server


def measure(label, runner, latency, pages, repeats):
    times, counts, peaks, requests = [], [], [], []
    for _ in range(repeats):
        elapsed, products, server = time_once(runner, latency, pages)
        times.append(elapsed)
        counts.append(len(products))
        peaks.append(server.max_in_flight)
        requests.append(server.request_count)

    return {
        "label": label,
        "pages": pages,
        "repeats": repeats,
        "mean_seconds": round(statistics.mean(times), 3),
        "median_seconds": round(statistics.median(times), 3),
        "min_seconds": round(min(times), 3),
        "max_seconds": round(max(times), 3),
        "pages_per_second": round(pages / statistics.mean(times), 2),
        "products": counts[0],
        "products_consistent": len(set(counts)) == 1,
        "peak_in_flight": max(peaks),
        "requests_made": requests[0],
        "failed_requests": pages - requests[0],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", default="usb hub")
    ap.add_argument("--pages", type=int, default=20)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--caps", type=int, nargs="+", default=DEFAULT_CAPS)
    ap.add_argument("--latency", type=float, nargs=2, default=DEFAULT_LATENCY)
    ap.add_argument("--out", default="comparison.json")
    args = ap.parse_args()

    latency, pages = tuple(args.latency), args.pages
    print("Fetch layer comparison - sequential vs bounded concurrency")
    print(f"  query={args.query!r} pages={pages} repeats={args.repeats} "
          f"latency={latency[0]:.2f}-{latency[1]:.2f}s  no deliberate delay\n")

    print("  measuring sequential baseline ...")
    baseline = measure(
        "sequential (requests)",
        lambda url: scraper.scrape_amazon(
            args.query, base_url=url, pages=pages, delay_range=(0, 0)),
        latency, pages, args.repeats)
    results = [baseline]

    for cap in args.caps:
        print(f"  measuring async, cap={cap} ...")
        results.append(measure(
            f"async cap={cap}",
            lambda url, c=cap: asyncio.run(async_scraper.scrape_amazon_async(
                args.query, base_url=url, pages=pages,
                concurrency=c, delay_range=(0, 0))),
            latency, pages, args.repeats))

    base = baseline["mean_seconds"]
    for r in results:
        r["speedup_vs_sequential"] = round(base / r["mean_seconds"], 2)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / args.out
    out_path.write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0],
        "server_latency": list(latency),
        "results": results,
    }, indent=2))

    print(f"\n  {'configuration':24}{'mean':>9}{'speedup':>10}{'pages/s':>10}"
          f"{'peak':>7}{'products':>10}{'failed':>8}")
    print("  " + "-" * 78)
    for r in results:
        flag = "" if r["products_consistent"] else "  <-- INCONSISTENT"
        print(f"  {r['label']:24}{r['mean_seconds']:8.2f}s{r['speedup_vs_sequential']:9.2f}x"
              f"{r['pages_per_second']:10.2f}{r['peak_in_flight']:7}"
              f"{r['products']:10}{r['failed_requests']:8}{flag}")

    wrong = [r for r in results if r["products"] != baseline["products"]]
    print()
    if wrong:
        print(f"  WARNING: {len(wrong)} configuration(s) returned a different "
              f"product count than the sequential baseline.")
    else:
        print(f"  All configurations returned {baseline['products']} products - "
              f"output is identical across every concurrency level.")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
