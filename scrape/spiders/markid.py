import scrapy


class MarkidSpider(scrapy.Spider):
    name = "markid"

    start_urls = [
        "https://markid.is/collections/scott-hjol-rafmagnshjol",
    ]

    def parse(self, response):
        for link in response.css(".product-item>a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        name = response.css(".product-meta__title::text").get()
        make = response.css(".product-meta__vendor::text").get()
        image_url = "https:" + response.css(".product-gallery__image::attr('data-zoom')").get()

        price = int("".join(response.css(".price").re(r"\d")))

        yield {
            "sku": response.url.rsplit("/", 1)[-1],
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
