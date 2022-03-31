import scrapy


class HvellurSpider(scrapy.Spider):
    name = "hvellur"

    start_urls = [
        "http://hvellur.com/product-category/reidhjol/rafhjol/",
    ]

    def parse(self, response):
        for product in response.css(".product-grid-item"):
            price = int("".join(product.css(".woocommerce-Price-amount ::text").re("\d+")))
            if price > 100000:
                link = product.css(".product-element-top a")[0]
                yield response.follow(link, self.parse_product, cb_kwargs={"price": price})

    def parse_product(self, response, price):

        sku = response.css(".single-product-page::attr('id')").re(r"product-(\d+)")[0]
        make, name = response.css(".product_title::text").get().split(" ", 1)

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
        ]

        name = " ".join(w for w in name.split() if w.lower() not in stripwords)

        image_url = response.css(".product-image-wrap a::attr('href')").get()

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
