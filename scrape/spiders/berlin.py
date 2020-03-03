import scrapy


class BerlinSpider(scrapy.Spider):
    name = "berlin"

    start_urls = [
        "https://www.reidhjolaverzlunin.is/collections/rafmagnshjol",
    ]

    def parse(self, response):
        for link in response.css(".product>a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        price = int("".join(response.css(".money::text")[0].re(r"\d+")))
        sku = response.css(".product-single::attr('class')").re(r"product-(\d+)")[0]

        yield {
            "sku": sku,
            "name": response.css(".section__title-text::text").get(),
            "make": response.css("h4.section__title-desc a::text").get(),
            "price": price,
            "file_urls": [response.css(".product-single__photo__img::attr('data-pswp-src')").get()],
            "scrape_url": response.url,
        }
