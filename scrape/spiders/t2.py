import json

import scrapy

from scrape.shopify import parse_products


class T2(scrapy.Spider):
    name = "t2"
    retailer_name = "T2"
    retailer_website_url = "https://t2.is"

    start_urls = [
        "https://t2.is/collections/e-bikes/products.json?limit=250",
    ]

    def parse(self, response):
        for item in parse_products(
            json.loads(response.text),
            make="Tenways",
            site_url=self.retailer_website_url,
        ):
            if item["name"].upper().startswith("TENWAYS "):
                item["name"] = item["name"][len("TENWAYS ") :]
            yield item
