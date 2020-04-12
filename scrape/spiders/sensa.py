import base64
import hashlib

import re
import scrapy


class SensaSpider(scrapy.Spider):
    name = "sensa"

    start_urls = [
        "https://www.sensabikes.is/cyclocross",
    ]

    def parse(self, response):
        for product in response.css("._3g8J4 a._34sIs"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):
        name = response.css("._2qrJF::text").get()
        price = int("".join(response.css("._2sFaY span::text").re(r"\d+")))
        image_url = response.css("._1oSdp::attr(style)").re_first(r"url\(([^\)]+)")
        sku = response.url

        yield {
            "sku": sku,
            "name": name,
            "make": "Sensa",
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
