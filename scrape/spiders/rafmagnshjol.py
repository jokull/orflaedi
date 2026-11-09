import scrapy


# The first gallery image of some QWIC products carries a German test-award
# badge ("BEST GETEST", "beste koop"). Pin a clean side-on cutout instead.
IMAGE_OVERRIDES = {
    "inter-tour": "https://rafmagnshjol.is/wp-content/uploads/2020/01/2019_cutout_premium-i_mn7belt_female_matte-black.jpg",
    "atlas-tour": "https://rafmagnshjol.is/wp-content/uploads/2025/08/1.ATLAS-TOUR.jpg",
}


class RafmagnshjolSpider(scrapy.Spider):
    name = "rafmagnshjol"

    start_urls = [
        "https://rafmagnshjol.is/hjolin/",
    ]

    def parse(self, response):
        for link in response.css(".product>a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        price_element = response.css(".woocommerce-Price-amount bdi::text")[0]
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
                IMAGE_OVERRIDES.get(sku)
                or response.css(".woocommerce-product-gallery__image img::attr('data-src')")[0].get()
            ],
            "scrape_url": response.url,
        }
