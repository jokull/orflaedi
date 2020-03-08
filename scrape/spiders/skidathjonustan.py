import re
import scrapy


class SkidathjonustanSpider(scrapy.Spider):
    name = "skidathjonustan"

    start_urls = [
        "http://www.skidathjonustan.com/434026228",
    ]

    def parse(self, response):
        for product in response.css(".content .thumbnail a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        sku = response.url
        price = None
        motor_model = None
        name, *attributes = response.css(".image-caption p::text").getall()
        for attribute in attributes:
            if re.search(r"([\d.]+)\.(\d{3})", attribute):
                price = int("".join(re.findall(r"(\d+)", attribute)))
            if "Shimano Steps" in attribute:
                motor_model = attribute
        image_url = response.css(".image img::attr(src)").get()

        yield {
            "sku": sku,
            "name": name,
            "make": "Superior",
            "price": price,
            "motor_model": motor_model,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
