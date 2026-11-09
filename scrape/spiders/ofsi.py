import json

import scrapy


class OfsiSpider(scrapy.Spider):
    """Ofsi (Orbea) via Shopify /products.json: one request per collection.

    SKU stays the product handle so rows created by the older HTML and
    Playwright scrapers keep their identity.
    """

    name = "ofsi"
    site_url = "https://ofsi.is"

    COLLECTIONS = [
        "gain-rafmagnsgotuhjol",
        "vibe-rafmagnsborgarhjol",
        "kemen-rafmagnsborgarhjol-eldri-argerd",
        "kemen-tour-rafmagnsborgarhjol",
        "kemen-adv-rafmagnsborgarhjol",
        "diem-rafmagnsborgarhjol",
        "urrun-rafmagnsfjallahjol-eldri-argerd",
        "urrun-rafmagnsfjallahjol",
        "rise-rafmagnsfjallahjol-eldri-argerd",
        "rise-sl-fulldempad-rafmagnsfjallahjol",
        "rise-lt-fulldempad-rafmagnsfjallahjol",
        "wild-rafmagnsfjallahjol-eldri-argerd",
        "wild-fulldempad-rafmagnsfjallahjol",
        "wild-lt-fulldempad-rafmagnsfjallahjol",
        "wild-tr-fulldempad-rafmagnsfjallahjol",
        "denna-rafmagnsmalarhjol",
        "muga-fulldempad-rafmagnsborgarhjol",
        "carpe-rafmagnsborgarhjol",
    ]

    start_urls = [
        f"https://ofsi.is/collections/{c}/products.json?limit=250" for c in COLLECTIONS
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen = set()

    def parse(self, response):
        for product in json.loads(response.text).get("products") or []:
            handle = product.get("handle")
            if not handle or handle in self._seen:
                continue
            prices = []
            for variant in product.get("variants") or []:
                if not variant.get("available", True):
                    continue
                try:
                    price = int(float(variant.get("price") or 0))
                except (TypeError, ValueError):
                    continue
                if price > 0:
                    prices.append(price)
            images = product.get("images") or []
            if not prices or not images:
                continue
            self._seen.add(handle)
            yield {
                "sku": handle,
                "name": (product.get("title") or "").strip(),
                "make": product.get("vendor") or None,
                "price": min(prices),
                "file_urls": [images[0]["src"]],
                "scrape_url": f"{self.site_url}/products/{handle}",
            }
