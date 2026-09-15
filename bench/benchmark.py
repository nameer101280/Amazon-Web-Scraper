"""Benchmark harness for the scraper's fetch layer.

Runs a scrape against the local mock server and records wall time, throughput
and how many products came back. Results are written to bench/results/ as JSON
so later runs can be compared against them.

Two delay settings are measured, because they answer different questions:

  polite  - keeps the 1-3s pause between pages, so the figure reflects what a
            real scrape costs today.
  nodelay - removes the pause, isolating the fetch layer itself. This is the
            number that a concurrency change can actually move.
"""
import argparse
import json
import pathlib
import statistics
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import scraper  # noqa: E402
from bench.mock_server import MockAmazonServer  # noqa: E402

RESULTS_DIR = pathlib.Path(__file__).parent / "results"
# Calibrated against live amazon.com: un-throttled full pages measured
# 0.90-0.96s round trip on 2026-09-15.
DEFAULT_LATENCY = (0.70, 1.10)


def run_sequential(base_url, query, pages, delay_range):
    """One timed sequential scrape. Returns (elapsed_seconds, products)."""
    start = time.perf_counter()
    products = scraper.scrape_amazon(
        query, base_url=base_url, pages=pages, delay_range=delay_range
    )
    return time.perf_counter() - start, products


def measure(label, delay_range, query, pages, repeats, latency, quiet=True):
    """Run one configuration `repeats` times and summarise the timings."""
    times, counts, requests = [], [], []
    for i in range(repeats):
        with MockAmazonServer(latency=latency) as server:
            if quiet:
                buf, sys.stdout = sys.stdout, open("/dev/null", "w")
            try:
                elapsed, products = run_sequential(
                    server.base_url, query, pages, delay_range
                )
            finally:
                if quiet:
                    sys.stdout.close()
                    sys.stdout = buf
            times.append(elapsed)
            counts.append(len(products))
            requests.append(server.request_count)
        print(f"    run {i + 1}/{repeats}: {elapsed:6.2f}s  "
              f"{len(products):4} products  {server.request_count} requests")

    return {
        "label": label,
        "mode": "sequential",
        "pages": pages,
        "repeats": repeats,
        "delay_range": list(delay_range),
        "server_latency": list(latency),
        "mean_seconds": round(statistics.mean(times), 3),
        "median_seconds": round(statistics.median(times), 3),
        "min_seconds": round(min(times), 3),
        "max_seconds": round(max(times), 3),
        "pages_per_second": round(pages / statistics.mean(times), 2),
        "products": counts[0],
        "requests_made": requests[0],
        "failed_requests": pages - requests[0],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", default="usb hub")
    ap.add_argument("--pages", type=int, default=20)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--latency", type=float, nargs=2, default=DEFAULT_LATENCY,
                    metavar=("LOW", "HIGH"))
    ap.add_argument("--out", default="baseline_sequential.json")
    args = ap.parse_args()

    latency = tuple(args.latency)
    print(f"Baseline benchmark - sequential fetch layer")
    print(f"  query={args.query!r} pages={args.pages} repeats={args.repeats} "
          f"server latency={latency[0]:.2f}-{latency[1]:.2f}s\n")

    results = []
    for label, delay_range in [
        ("polite (1-3s between pages)", (1, 3)),
        ("nodelay (fetch layer only)", (0, 0)),
    ]:
        print(f"  {label}")
        results.append(measure(label, delay_range, args.query, args.pages,
                               args.repeats, latency))
        print()

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / args.out
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0],
        "configurations": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"{'configuration':32} {'mean':>8} {'median':>8} {'pages/s':>9} {'products':>9}")
    print("  " + "-" * 68)
    for r in results:
        print(f"  {r['label']:30} {r['mean_seconds']:7.2f}s {r['median_seconds']:7.2f}s "
              f"{r['pages_per_second']:9.2f} {r['products']:9}")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
