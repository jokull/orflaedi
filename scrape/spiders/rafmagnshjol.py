import scrapy


class RafmagnshjolSpider(scrapy.Spider):
    name = "rafmagnshjol"

    start_urls = [
        "https://rafmagnshjol.is/hjolin/",
    ]

    def parse(self, response):
        for link in response.css(".product>a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        price_element = response.css(".woocommerce-Price-amount::text")
        if price_element:
            price = int("".join(price_element.re(r"\d+")))
        else:
            price = None

        sku = response.url.rsplit("/")[-2]

        yield {
            "sku": sku,
            "name": response.css(".product_title::text").get(),
            "make": "QWIC",
            "price": price,
            "file_urls": [
                response.css(".woocommerce-product-gallery__wrapper a::attr(href)").get()
            ],
            "scrape_url": response.url,
        }
