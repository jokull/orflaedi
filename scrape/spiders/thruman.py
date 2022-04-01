import scrapy


from orflaedi.models import VehicleClassEnum


class ThrumanSpider(scrapy.Spider):
    name = "thruman"

    start_urls = [
        "https://thruman.is/vara-flokkur/rafhlaupahjol/",
        "https://thruman.is/vara-flokkur/rafmotorhjol/super-soco-motorhjol/",
    ]

    def parse(self, response):
        classification = None
        if response.url.endswith("/super-soco-motorhjol/"):
            classification = VehicleClassEnum.lb_2
        for link in response.css("ul.products a.woocommerce-LoopProduct-link"):
            yield response.follow(
                link, self.parse_product, cb_kwargs={"classification": classification}
            )

    def parse_product(self, response, classification):
        price = int(
            "".join(
                response.css(".product_infos .price .woocommerce-Price-amount bdi")[-1].re(r"\d+")
            )
        )
        if price < 40_000:
            return

        name = response.css(".product_title::text").get()

        stripwords = [
            "svart",
            "hvítt",
            "blátt",
            "gult",
            "rautt",
            "blátt",
            "brúnt",
            "grátt",
            "17.5ah",
            "36v",
            "ebike",
            "rafhlaupahjól",
            "rafhjól",
            "fjallarafhjól",
            "rafmagnshjól",
            "rafmótorhjól",
            "forsala",
        ]

        name = " ".join(w for w in name.split() if w.lower() not in stripwords)

        make = None

        if name.lower().startswith("super soco"):
            make = "Super Soco"
            name = name[len("Super Soco ") :]

        if name.lower().startswith("kaabo "):
            make = "Kaabo"
            name = name[len("kaabo ") :]

        if name.lower().startswith("vsett "):
            make = "VSETT"
            name = name[len("VSETT ") :]

        if make:

            yield {
                "sku": response.css(".single_add_to_cart_button::attr(data-product_id)").get(),
                "name": name,
                "make": make,
                "classification": classification or VehicleClassEnum.bike_c,
                "price": price,
                "file_urls": [
                    response.css(".woocommerce-product-gallery__image a::attr(href)").get()
                ],
                "scrape_url": response.url,
            }
