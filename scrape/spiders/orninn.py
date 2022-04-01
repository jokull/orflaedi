import scrapy


class OrninnSpider(scrapy.Spider):
    name = "orninn"

    start_urls = [
        "https://orninn.is/product-category/reidhjol/rafhjol/",
    ]

    def parse(self, response):
        for link in response.css(".product-wrap>a::attr(href)"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        price = int("".join(response.css(".woocommerce-Price-amount bdi::text")[0].re(r"\d+")))

        file_urls = [response.css(".slider a::attr(href)")[0].get()]

        yield {
            "sku": response.css(".sku::text").get(),
            "name": response.css(".summary>.entry-title::text").get(),
            "make": response.css(".posted_in a::text")[1].get().lower().title(),
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
        }
