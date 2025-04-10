import scrapy


class MarkidSpider(scrapy.Spider):
    name = "markid"

    start_urls = [
        "https://markid.is/collections/rafmagnshjol-fjallahjol",
        "https://markid.is/collections/rafmagnshjol-borgahjol",
    ]

    def parse(self, response):
        for node in response.css(".product-item"):
            name = node.css(".product-item__title::text").get()
            make = node.css(".product-item__vendor::text").get()
            yield response.follow(
                node.css("a")[0],
                self.parse_product,
                cb_kwargs={"name": name, "make": make},
            )

    def parse_product(self, response, name, make):
        image_url = (
            "https:" + response.css(".product-gallery__image::attr('data-zoom')").get()
        )

        price = int("".join(response.css(".price-list>.price")[0].re(r"\d")))

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
            "fjallahjól",
            "scott",
            "bergamont",
            "|",
            "dömu",
            "28\""
        ]

        name = " ".join(w for w in name.split() if w.lower() not in stripwords).strip()

        yield {
            "sku": response.url.rsplit("/", 1)[-1],
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
