import json

import scrapy


class BerlinSpider(scrapy.Spider):
    """
    reidhjolaverzlunin.is is Shopify — uses the /products.json endpoint
    rather than parsing HTML, which makes the spider immune to theme changes.
    """

    name = "berlin"

    start_urls = [
        "https://www.reidhjolaverzlunin.is/collections/rafmagnshjol/products.json?limit=250",
    ]

    def parse(self, response):
        data = json.loads(response.text)
        for product in data.get("products") or []:
            variants = product.get("variants") or []
            if not variants:
                continue
            price_text = variants[0].get("price")
            if not price_text:
                continue
            try:
                price = int(float(price_text))
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue

            images = product.get("images") or []
            image_url = images[0].get("src") if images else None
            if not image_url:
                continue

            yield {
                "sku": str(product["id"]),
                "name": product.get("title") or "",
                "make": product.get("vendor") or None,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": f"https://www.reidhjolaverzlunin.is/products/{product['handle']}",
            }
