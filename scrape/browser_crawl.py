"""Run Scrapy spiders through a real headless Chromium instead of Scrapy's
downloader.

Shopify's bot protection throttles non-browser clients by IP: from the
production Mac, curl and Scrapy get HTTP 429 on products.json while a real
Chromium page gets 200 from the same IP. So the Shopify spiders run here, on
the host, and every request the spider makes is issued with fetch() from
inside a page on that shop's origin (cookies and browser fingerprint
included). Spider callbacks, items and the DatabasePipeline are reused as-is.

The Docker scrapy runner skips these spiders (see BrowserOnlyMiddleware).

Run:      .venv/bin/python scrape/browser_crawl.py            # all
          .venv/bin/python scrape/browser_crawl.py ofsi kuldi  # some
Dry run:  .venv/bin/python scrape/browser_crawl.py --dry-run ofsi
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import time
import warnings
from collections import deque
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright  # noqa: E402
from scrapy import Request  # noqa: E402
from scrapy.http import Headers  # noqa: E402
from scrapy.responsetypes import responsetypes  # noqa: E402
from scrapy.spiderloader import SpiderLoader  # noqa: E402
from scrapy.utils.project import get_project_settings  # noqa: E402

from scrape.spider_lists import BROWSER_SPIDERS  # noqa: E402

# start_requests() is deprecated in Scrapy 2.13+ but is what the Docker
# image's Scrapy 2.6 understands, so the spiders keep using it.
warnings.filterwarnings("ignore", message=r".*start_requests\(\) method is deprecated.*")

REQUEST_DELAY = 1.0  # seconds between requests to the same shop
RETRY_WAITS = (15, 45, 90)  # back-off on 429/5xx

FETCH_JS = """
async ([url, method, headers, body]) => {
  const r = await fetch(url, {method, headers, body: body || undefined,
                              credentials: 'include', redirect: 'follow'});
  const buf = new Uint8Array(await r.arrayBuffer());
  let bin = '';
  for (let i = 0; i < buf.length; i += 0x8000) {
    bin += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
  }
  return {status: r.status, url: r.url, body: btoa(bin),
          headers: Array.from(r.headers.entries())};
}
"""

# Headers the browser sets itself (or refuses to let scripts set).
SKIP_HEADERS = {"user-agent", "accept-encoding", "cookie", "referer", "host", "content-length"}


class _Stats:
    def __init__(self):
        self.failed = 0

    def get_stats(self):
        return {"downloader/exception_count": self.failed}


class _Crawler:
    def __init__(self):
        self.stats = _Stats()


class BrowserFetcher:
    def __init__(self, context):
        self.page = context.new_page()
        self.origin = None
        self.last = 0.0

    def _ensure_origin(self, url: str):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin != self.origin:
            self.page.goto(origin + "/", wait_until="domcontentloaded", timeout=60000)
            self.origin = origin

    def fetch(self, request: Request):
        self._ensure_origin(request.url)
        headers = {
            k.decode(): b", ".join(v).decode("latin-1")
            for k, v in request.headers.items()
            if k.decode().lower() not in SKIP_HEADERS
        }
        body = request.body.decode("utf-8") if request.body else None
        for attempt, wait in enumerate((0,) + RETRY_WAITS):
            if wait:
                print(f"    retry {attempt} in {wait}s: {request.url}", flush=True)
                time.sleep(wait)
            gap = REQUEST_DELAY - (time.monotonic() - self.last)
            if gap > 0:
                time.sleep(gap)
            self.last = time.monotonic()
            res = self.page.evaluate(FETCH_JS, [request.url, request.method, headers, body])
            if res["status"] != 429 and res["status"] < 500:
                break
        raw_headers = Headers()
        for key, value in res["headers"]:
            raw_headers.appendlist(key, value)
        raw_headers.pop(b"Content-Encoding", None)  # body is already decoded
        content = base64.b64decode(res["body"])
        cls = responsetypes.from_args(headers=raw_headers, url=res["url"], body=content)
        return cls(
            url=res["url"],
            status=res["status"],
            headers=raw_headers,
            body=content,
            request=request,
        )


def crawl(spider_cls, fetcher: BrowserFetcher, dry_run: bool) -> tuple[int, int]:
    from scrape.pipelines import DatabasePipeline

    settings = get_project_settings()
    spider = spider_cls()
    spider.settings = settings
    spider.crawler = _Crawler()

    pipeline = None if dry_run else DatabasePipeline()
    if pipeline:
        pipeline.open_spider(spider)

    queue = deque(spider.start_requests())
    seen: set[str] = set()
    items = 0
    try:
        while queue:
            request = queue.popleft()
            if not request.dont_filter:
                if request.url in seen:
                    continue
                seen.add(request.url)
            try:
                response = fetcher.fetch(request)
            except Exception as exc:  # noqa: BLE001
                print(f"    ! {request.url}: {exc}", flush=True)
                spider.crawler.stats.failed += 1
                continue
            if response.status >= 400:
                print(f"    ! {response.status} {request.url}", flush=True)
                spider.crawler.stats.failed += 1
                continue
            callback = request.callback or spider.parse
            try:
                for out in callback(response, **(request.cb_kwargs or {})) or ():
                    if isinstance(out, Request):
                        queue.append(out)
                    elif out is not None:
                        items += 1
                        if pipeline:
                            pipeline.process_item(dict(out), spider)
                        elif dry_run:
                            print(f"    {out.get('make')} {out.get('name')}: {out.get('price')}")
            except Exception as exc:  # noqa: BLE001
                print(f"    ! callback error on {request.url}: {exc!r}", flush=True)
                spider.crawler.stats.failed += 1
    finally:
        if pipeline:
            pipeline.close_spider(spider)
    return items, spider.crawler.stats.failed


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("spiders", nargs="*", default=sorted(BROWSER_SPIDERS))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    loader = SpiderLoader.from_settings(get_project_settings())
    failed_spiders = []
    with sync_playwright() as p:
        # Full Chromium (not the headless shell): what Shopify scores as a browser.
        browser = p.chromium.launch(headless=True, channel="chromium")
        context = browser.new_context(locale="is-IS")
        fetcher = BrowserFetcher(context)
        for name in args.spiders:
            start = time.monotonic()
            try:
                items, failed = crawl(loader.load(name), fetcher, args.dry_run)
            except Exception as exc:  # noqa: BLE001 - keep going with other shops
                print(f"{name}: crashed: {exc!r}", flush=True)
                failed_spiders.append(name)
                continue
            note = f", {failed} failed requests (kept existing inventory)" if failed else ""
            print(f"{name}: {items} items in {time.monotonic() - start:.0f}s{note}", flush=True)
            if failed:
                failed_spiders.append(name)
        browser.close()
    sys.exit(1 if failed_spiders else 0)


if __name__ == "__main__":
    main()
