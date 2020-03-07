import scrapy


class HjolaspretturSpider(scrapy.Spider):
    name = "hjolasprettur"

    start_urls = [
        "https://hjolasprettur.is/collections/rafmagnshjol",
    ]

    def parse(self, response):
        for product in response.css(".main-content .grid__item>a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        sku = response.css("#ProductJson-product-template").re(r'"id":(\d+)')[0]
        make, name = (
            response.css(".product-single__title::text").get().title().split(" ", 1)
        )
        image_url = response.css(".product-single__photo>a::attr('href')").get()
        price = int(
            "".join(response.css("#ProductPrice-product-template::text").re(r"\d+"))
        )

        try:
            motor_model = response.css(".pim_ebikemotordescription td::text")[2].get()
        except IndexError:
            motor_model = None

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "motor_model": motor_model,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
