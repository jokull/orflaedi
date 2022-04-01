import base64
import hashlib

import re
import scrapy


class SkidathjonustanSpider(scrapy.Spider):
    name = "skidathjonustan"

    start_urls = [
        "http://www.skidathjonustan.com/450381818",
        "http://www.skidathjonustan.com/450381826",
    ]

    def parse(self, response):
        for product in response.css(".content .thumbnail a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):
        price = None
        name, *attributes = response.css(".image-caption p::text").getall()
        for attribute in attributes:
            if re.search(r"([\d.]+)\.(\d{3})", attribute):
                price = int("".join(re.findall(r"(\d+)", attribute)))
        image_url = response.css(".image img::attr(src)").get()

        if image_url.startswith("//"):
            image_url = "https:" + image_url

        # Use a hash since this website lists multiple colors as multiple
        # models and has no SKU anywhere.
        hasher = hashlib.sha1("{}-{}".format(name, price).encode())
        sku = base64.urlsafe_b64encode(hasher.digest()).decode("ascii")[:6]

        make = "Superior"

        if name.startswith("CUBE"):
            make = "Cube"
            name = name[len("Cube") :].strip()

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
