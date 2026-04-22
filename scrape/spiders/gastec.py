import html
import json
import re

import scrapy


class GastecSpider(scrapy.Spider):
    """
    gastec.is is WooCommerce. Uses the built-in Store API which
    returns products as JSON. Category 766 ('Hjól') holds the
    e-bikes only (accessories and parts live in separate categories).

    Most bikes on gastec are Urbanbiker-branded; when the name
    contains "Dakota" that's the model line, not the brand.
    """

    name = "gastec"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    CATEGORY_ID = 766  # 'Hjól' — e-bikes only
    start_urls = [
        f"https://www.gastec.is/wp-json/wc/store/v1/products?category={CATEGORY_ID}&per_page=100",
    ]

    STRIPWORDS = {
        "svart", "hvítt", "blátt", "gult", "rautt", "brúnt", "grátt",
        "17.5ah", "36v", "ebike", "rafhlaupahjól", "rafhjól",
        "fjallarafhjól", "rafmagnshjól", "fulldempað",
    }

    def parse(self, response):
        products = json.loads(response.text)
        for product in products:
            price_text = (product.get("prices") or {}).get("price")
            if not price_text:
                continue
            try:
                price = int(price_text)
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue

            images = product.get("images") or []
            image_url = images[0].get("src") if images else None
            if not image_url:
                continue

            raw_name = html.unescape(product.get("name") or "")
            tokens = [t for t in re.split(r"[\s]+", raw_name) if t]
            cleaned = [t for t in tokens if t.lower() not in self.STRIPWORDS]
            name = " ".join(cleaned).strip()

            make = "Urbanbiker"

            yield {
                "sku": str(product["id"]),
                "name": name,
                "make": make,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": product["permalink"],
            }
