import scrapy


from orflaedi.models import VehicleClassEnum


class ThrumanSpider(scrapy.Spider):
    name = "thruman"

    start_urls = [
        "https://thruman.is/vara-flokkur/rafhlaupahjol/rafhlaupahjol-rafhlaupahjol/"
    ]

    def parse(self, response):
        for link in response.css("ul.products a.woocommerce-LoopProduct-link"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):
        price = int(
            "".join(response.css(".woocommerce-Price-amount bdi")[-1].re(r"\d+"))
        )
        if price < 40000:
            return

        make, name = response.css(".product_title::text").get().split(" ", 1)

        yield {
            "sku": response.css(
                ".single_add_to_cart_button::attr(data-product_id)"
            ).get(),
            "name": name,
            "make": make,
            "classification": VehicleClassEnum.bike_c,
            "price": price,
            "file_urls": [response.css(".gallery_image_link::attr(href)").get()],
            "scrape_url": response.url,
        }
