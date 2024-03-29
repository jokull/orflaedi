import scrapy


class KriaSpider(scrapy.Spider):
    name = "kria"

    start_urls = [
        "https://kriahjol.is/product-category/bikes/rafhjol/",
        "https://kriahjol.is/product-category/bikes/rafhjol/page/2/",
    ]

    def parse(self, response):
        for link in response.css(".products a.wrap_image"):
            yield response.follow(link, self.parse_product)
        for link in response.css(".page-numbers a.next"):
            yield response.follow(link, self.parse)

    def parse_product(self, response):

        price_el = response.css(".wrap_price .woocommerce-Price-amount bdi::text")
        if not price_el:
            return

        price = int("".join(price_el[0].re(r"\d+")))
        if price < 30_000:
            return

        image_url = response.css(".item_slick::attr(href)").get()
        sku = response.xpath("//meta[@property='og:url']").css("::attr(content)").get()

        yield {
            "sku": sku,
            "name": response.css("h1.product_title::text").get(),
            "make": "Specialized",
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
