"""
Stormur e-bike scraper (Mondraker) using Playwright.

stormur.is blocks plain HTTP clients (403), so this uses Scrapling/Playwright
like the other JS-rendered shops.

Run dry:  python scrape/scrapling_spiders/stormur.py --dry-run
Run live: python scrape/scrapling_spiders/stormur.py
"""
import re
import argparse
from playwright.sync_api import sync_playwright

from base import ScraplingPipeline


SPIDER_NAME = "stormur"

# Only e-bike categories — skip regular MTB / kids / accessories.
START_URLS = [
    "https://stormur.is/voruflokkar/reidhjol/fulldempud-rafmagnshjol/",
    "https://stormur.is/voruflokkar/reidhjol/fulldempud-lett-rafmagnshjol/",
    "https://stormur.is/voruflokkar/reidhjol/rafmagns-hardtail-og-borgarhjol/",
    "https://stormur.is/voruflokkar/reidhjol/rafmagnsbarnahjol/",
]

# Categories here are already filtered to e-bikes only; the floor just guards
# against weirdness. Kids e-bikes can go below 100k on sale.
MIN_PRICE = 50_000


def _highest_res(srcset: str | None) -> str | None:
    if not srcset:
        return None
    best_url, best_w = None, -1
    for part in srcset.split(","):
        bits = part.strip().split()
        if len(bits) < 2:
            continue
        url, w = bits[0], bits[1]
        m = re.match(r"(\d+)w", w)
        if not m:
            continue
        wi = int(m.group(1))
        if wi > best_w:
            best_w, best_url = wi, url
    return best_url


def scrape_category(page, url: str) -> list[dict]:
    page.goto(url, timeout=60000)
    page.wait_for_load_state("networkidle", timeout=45000)

    cards = page.eval_on_selector_all(
        'a[href*="/vorur/"]',
        """els => {
          const seen = new Set();
          const out = [];
          for (const e of els) {
            if (seen.has(e.href)) continue;
            seen.add(e.href);
            // walk up until we find a container that includes the price text
            let cur = e;
            for (let i = 0; i < 8 && cur; i++) {
              if (cur.innerText && cur.innerText.includes('kr')) break;
              cur = cur.parentElement;
            }
            const img = cur ? cur.querySelector('img') : null;
            out.push({
              href: e.href,
              text: cur ? cur.innerText : '',
              imgSrc: img ? img.src : null,
              imgSrcset: img ? img.srcset : null,
            });
          }
          return out;
        }""",
    )

    items: list[dict] = []
    for c in cards:
        href = c["href"]
        text = (c["text"] or "").strip()
        if not text or "kr" not in text:
            continue

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Format: NAME / MAKE / PRICE kr. / [size variants...]
        if len(lines) < 3:
            continue
        name, make = lines[0], lines[1]

        # A card may show multiple prices (regular + sale). Collect them and
        # use the lowest, which matches what the customer actually pays.
        price_nums: list[int] = []
        for l in lines:
            if "kr" not in l:
                continue
            for m in re.finditer(r"[\d\.]+", l):
                digits = m.group(0).replace(".", "")
                if digits.isdigit():
                    price_nums.append(int(digits))
        if not price_nums:
            continue
        price = min(price_nums)
        if price < MIN_PRICE:
            continue

        image_url = _highest_res(c.get("imgSrcset")) or c.get("imgSrc")
        if image_url and image_url.startswith("data:"):
            image_url = _highest_res(c.get("imgSrcset"))
        # Strip Stormur's cdn proxy wrapper, keep the original upload URL.
        if image_url:
            m = re.search(r"u:(https?://[^\s]+)$", image_url)
            if m:
                image_url = m.group(1)

        # SKU = product slug.
        sku = href.rstrip("/").rsplit("/", 1)[-1]

        # Drop make duplicated in name.
        if make and name.lower().startswith(make.lower()):
            name = name[len(make):].strip()

        items.append(
            {
                "sku": sku,
                "name": name.title() if name.isupper() else name,
                "make": make,
                "price": price,
                "file_urls": [image_url] if image_url else [],
                "scrape_url": href,
                "classification": "bike_b",
            }
        )

    print(f"  {url} -> {len(items)} items")
    return items


def run(dry_run: bool = False):
    pipeline = ScraplingPipeline(SPIDER_NAME, dry_run=dry_run)
    pipeline.open()

    all_items: list[dict] = []
    seen_skus: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in START_URLS:
            for item in scrape_category(page, url):
                if item["sku"] in seen_skus:
                    continue
                seen_skus.add(item["sku"])
                all_items.append(item)
        browser.close()

    print(f"\nProcessing {len(all_items)} items...")
    for item in all_items:
        pipeline.process_item(item)

    pipeline.close()
    print(f"\nDone! Scraped {len(all_items)} e-bikes from {SPIDER_NAME}")
    return all_items


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Stormur e-bikes")
    parser.add_argument("--dry-run", action="store_true", help="Run without database")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
