import scrapy


class HvellurSpider(scrapy.Spider):
    name = "hvellur"

    start_urls = [
        "http://hvellur.com/product-category/reidhjol/rafhjol/",
    ]

    def parse(self, response):
        for product in response.css(".product a.product-image-link"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        sku = response.css(".single-product-page::attr('id')").re(r"product-(\d+)")[0]
        make, name = response.css(".product_title::text").get().split(" ", 1)

        if "rafhjól" not in name.lower():
            return None

        image_url = response.css(".product-image-wrap a::attr('href')").get()
        price_el = response.css(".entry-summary .price .woocommerce-Price-amount::text")
        price = int("".join(price_el.re(r"\d+")))

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
