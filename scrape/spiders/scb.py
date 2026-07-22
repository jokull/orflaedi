import json

import scrapy

from scrape.shopify import parse_products


class ScbSpider(scrapy.Spider):
    """Santa Cruz e-bikes sold by SCB through Shopify."""

    name = "scb"
    retailer_name = "SCB"
    retailer_website_url = "https://scb.is"

    start_urls = [
        "https://scb.is/collections/frontpage/products.json?limit=250",
    ]

    def parse(self, response):
        yield from parse_products(
            json.loads(response.text),
            make="Santa Cruz",
            site_url=self.retailer_website_url,
        )
