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
        for product in response.css("ul._3g4hn ._3DNsL>a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):
        name = response.css("._2qrJF::text").get()
        price = int("".join(response.css("._2POY8 span::text").re(r"\d+")))
        image_url = response.css(".media-wrapper-hook::attr(href)").get()
        sku = response.url

        make = "Sensa"
        if name.startswith("PINARELLO"):
            name = name[len("PINARELLO") :]
            make = "Pinarello"

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
