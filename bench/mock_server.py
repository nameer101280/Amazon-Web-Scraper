"""A local stand-in for Amazon's search endpoint.

Replays saved real result pages with a configurable per-request delay, so
benchmarks measure the scraper rather than Amazon's mood. Running against
the real site makes timings depend on rate limiting, geography and time of
day, which is not reproducible for anyone reading the results.
"""
import http.server
import pathlib
import random
import threading
import time
import urllib.parse

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def load_fixtures():
    pages = sorted(FIXTURES.glob("*.html"))
    if not pages:
        raise FileNotFoundError(f"no fixtures in {FIXTURES}")
    return [p.read_bytes() for p in pages]


class MockAmazonServer:
    """Serves /s?k=<query>&page=<n> from saved fixtures.

    latency simulates round-trip time. Pass a (low, high) tuple to vary it,
    which is closer to a real network than a fixed figure.
    """

    def __init__(self, latency=(0.20, 0.40), host="127.0.0.1", port=0):
        self.latency = latency
        self._bodies = load_fixtures()
        self.request_count = 0
        self._lock = threading.Lock()

        bodies, lock, latency_range = self._bodies, self._lock, latency
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if not parsed.path.startswith("/s"):
                    self.send_error(404)
                    return
                query = urllib.parse.parse_qs(parsed.query)
                page = int(query.get("page", ["1"])[0])

                low, high = latency_range
                time.sleep(random.uniform(low, high))

                with lock:
                    outer.request_count += 1
                body = bodies[(page - 1) % len(bodies)]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass  # keep benchmark output clean

        self._server = http.server.ThreadingHTTPServer((host, port), Handler)
        self.port = self._server.server_address[1]
        self.base_url = f"http://{host}:{self.port}/s"

    def __enter__(self):
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
        return False


if __name__ == "__main__":
    with MockAmazonServer() as server:
        print(f"Serving {len(server._bodies)} fixtures at {server.base_url}")
        print("Ctrl-C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
