import scrapy


class T2(scrapy.Spider):
    name = "t2"

    start_urls = [
        "https://t2.is/collections/e-bikes",
    ]

    def parse(self, response):
        for product in response.css("#product-grid .card__content a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):
        name = response.css(".product__title h1::text").get()
        if name.startswith("TENWAYS "):
            name = name[len("TENWAYS "):]
        price = int("".join(response.css(".price-item--regular::text").re(r"\d+")))
        image_url = 'https:' + response.css(".product__media img::attr(src)").get()
        sku = response.url

        yield {
            "sku": sku,
            "name": name,
            "make": "Tenways",
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
