import scrapy


class GastecSpider(scrapy.Spider):
    name = "gastec"

    start_urls = [
        "https://www.gastec.is/vorur/rafhjol/hjol/",
    ]

    def parse(self, response):
        for product in response.css(".products .product_tag-rafhjol .product-title a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        image_url = response.urljoin(
            response.css(".woocommerce-product-gallery__image a::attr('href')")[0].get()
        )
        name = response.css(".product-title::text").get()
        make = response.css(".wb-posted_in a::text").get()
        price = "".join(
            response.css(".product-page-price .woocommerce-Price-amount bdi::text").re("\d+")
        )

        if not make and "Dakota" in name:
            make = "Dakota"

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
            "dakota",
        ]

        name = " ".join(w for w in name.split() if w.lower() not in stripwords)

        make = make.strip() if make else ""

        if "urbanbiker" in make.lower() or not make.strip():
            make = "Urbanbiker"

        yield {
            "sku": response.css(".sku::text").get(),
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
