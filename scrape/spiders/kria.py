import scrapy


class KriaSpider(scrapy.Spider):
    name = "kria"

    start_urls = [
        "https://kriacycles.com/product-category/bikes/turbo-e-bikes/",
    ]

    def parse(self, response):
        for link in response.css(".products a.wrap_image"):
            yield response.follow(link, self.parse_product)
        for link in response.css(".page-numbers a.next"):
            yield response.follow(link, self.parse)

    def parse_product(self, response):

        price = int("".join(response.css(".woocommerce-Price-amount bdi::text")[0].re(r"\d+")))
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
