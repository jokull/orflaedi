import json

import scrapy


class KuldiSpider(scrapy.Spider):
    """
    kuldi.net is Shopify. Hits /products.json on the relevant e-bike
    collections and dedupes by product id, since a single bike often
    appears in both a brand collection (e.g. norco-rafmagnshjol) and
    a category collection (rafmagnsfjallahjol).
    """

    name = "kuldi"

    COLLECTIONS = [
        "rafhjol-allt",
        "rafmagnsfjallahjol",
        "norco-rafmagnshjol",
        "pivot-rafmagnshjol",
        "giant-rafmagnshjol",
    ]

    start_urls = [
        f"https://kuldi.net/collections/{c}/products.json?limit=250" for c in COLLECTIONS
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_ids = set()

    def parse(self, response):
        data = json.loads(response.text)
        for product in data.get("products") or []:
            pid = product["id"]
            if pid in self._seen_ids:
                continue
            self._seen_ids.add(pid)

            variants = product.get("variants") or []
            if not variants:
                continue
            try:
                price = int(float(variants[0].get("price") or 0))
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue

            images = product.get("images") or []
            image_url = images[0].get("src") if images else None
            if not image_url:
                continue

            yield {
                "sku": str(pid),
                "name": product.get("title") or "",
                "make": product.get("vendor") or None,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": f"https://kuldi.net/products/{product['handle']}",
            }
