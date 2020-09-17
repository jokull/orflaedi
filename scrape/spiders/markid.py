import scrapy


class MarkidSpider(scrapy.Spider):
    name = "markid"

    start_urls = [
        "https://markid.is/voruflokkur/scott-hjol/rafmagnshjol/?v=0bfc16cc12ef",
    ]

    def parse(self, response):
        for link in response.css(".product>a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        sku = response.css(".product::attr('class')").re(r"post-(\d+)")[0]
        make, name = response.css(".entry-title::text").get().title().split(" ", 1)
        image_url, _ = (
            response.css(".woocommerce-product-gallery__wrapper a::attr(href)")
            .get()
            .split("?", 1)
        )

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": int(
                "".join(response.css(".woocommerce-Price-amount::text")[0].re(r"\d+"))
            ),
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
