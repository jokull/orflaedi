import scrapy


class PelotonSpider(scrapy.Spider):
    name = "peloton"

    start_urls = [
        "https://www.peloton.is/voruflokkur/hjol/gotuhjol/rafdrifin-gotuhjol/",
        "https://www.peloton.is/voruflokkur/hjol/fjallahjol/rafdrifin-fjallahjol/",
    ]

    def parse(self, response):
        for link in response.css(".product .fusion-product-buttons a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        sku = response.css(".sku::text").get()
        name = response.css(".product_title::text").get()
        make = response.css(".product_meta span")[-1].css("a::text").get()
        image_url = response.css(".woocommerce-product-gallery__wrapper a::attr('href')").get()
        price = int("".join(response.css(".summary .woocommerce-Price-amount").re(r"\d")))

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
