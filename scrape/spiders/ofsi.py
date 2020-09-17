import scrapy


class OfsiSpider(scrapy.Spider):
    name = "ofsi"

    start_urls = [
        "https://ofsi.is/pages/rafmagnshjol",
    ]

    def parse(self, response):
        for link in response.css(".blocks a.block-link"):
            yield response.follow(link, self.parse)
        for product in response.css(".grid-view-item .grid-view-item__link"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        sku = response.css("#ProductJson-product-template").re(r'"id":(\d+)')[0]
        name = response.css(".product-single__title::text").get().title()
        image_url = response.css(".product-single__photo::attr('data-zoom')").get()
        price = int(
            "".join(response.css("#ProductPrice-product-template::text").re(r"\d+"))
        )

        yield {
            "sku": sku,
            "name": name,
            "make": "Orbea",
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
