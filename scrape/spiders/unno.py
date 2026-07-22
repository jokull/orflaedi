import json

import scrapy

from scrape.shopify import parse_products


class UnnoSpider(scrapy.Spider):
    """UNNO e-bikes from the brand's Icelandic Shopify store."""

    name = "unno"
    retailer_name = "UNNO"
    retailer_website_url = "https://unno.is"

    start_urls = [
        "https://unno.is/products.json?limit=250",
    ]

    def parse(self, response):
        yield from parse_products(
            json.loads(response.text),
            make="UNNO",
            site_url=self.retailer_website_url,
        )
