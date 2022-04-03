import scrapy


class KuldiSpider(scrapy.Spider):
    name = "kuldi"

    start_urls = [
        "https://kuldi.net/collections/giant-rafmagnshjol",
    ]

    def parse(self, response):
        for link in response.css("#Collection .grid__item a.grid-view-item__link"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        price = int(
            "".join(response.css(".product-single__meta .price-item span.money::text")[0].re("\d+"))
        )

        image_url = (
            "https:"
            + response.css(".product-single__media-wrapper>div")[0].css("::attr('data-zoom')").get()
        )
        sku = response.url.rsplit("/", 1)[-1]

        make, name = response.css(".product-single__title::text").get().split(" ", 1)

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
