import scrapy


class GastecSpider(scrapy.Spider):
    name = "gastec"

    start_urls = [
        "http://gastec.is/vorur/c/TA8z9YCkyT/rafhjol/",
    ]

    def parse(self, response):
        for product in response.css(".products-main a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        image_url = response.urljoin(response.css(".img::attr('href')")[0].get())
        name = response.css(".heading h2::text").re_first(r"\w+")

        for price in response.css(".mainContent h4").re("([\d\.]+\.)"):
            price = int(price.replace(".", ""))
            sku = f"{response.url}{price}"

            yield {
                "sku": sku,
                "name": name,
                "make": "Urbanbiker",
                "price": price,
                "file_urls": [image_url],
                "scrape_url": response.url,
            }
