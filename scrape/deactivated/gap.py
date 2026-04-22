from w3lib import url as w3lib_url
import scrapy


class GapSpider(scrapy.Spider):
    name = "gap"

    start_urls = [
        "https://www.gap.is/fjallahjol/rafmagns-fjallahjol",
        "https://www.gap.is/gotuhjol/rafmagns-gotuhjol",
    ]

    def parse(self, response):
        for link in response.css(".main-products .name a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        sku = w3lib_url.url_query_parameter(response.url, "product_id")
        make, name = response.css(".heading-title::text").get().title().split(" ", 1)
        image_url = response.css(".image a::attr(href)").get()

        price = None
        price_el = response.css(".product-price::text, .price-new::text")
        if price_el:
            price = int("".join(price_el[0].re(r"\d+")))

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
