import scrapy


class OfsiSpider(scrapy.Spider):
    name = "ofsi"

    start_urls = [
        "https://ofsi.is/collections/rafmagnshjol",
    ]

    def parse(self, response):
        for link in response.css(".grid__item a.full-unstyled-link"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):
        make = response.css(".product__info-container .product__text::text").get()
        name = response.css(".product__info-container .product__title::text").get().strip()
        sku = response.url.rsplit("/", 1)[-1]
        image_url = "https:" + response.css(".product__media img::attr('src')").get()
        price = int("".join(response.css(".price-item::text")[0].re(r"\d+")))

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
