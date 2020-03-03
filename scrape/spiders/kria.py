import scrapy


class KriaSpider(scrapy.Spider):
    name = "kria"

    start_urls = [
        "https://kriacycles.com/collections/rafmagnshjol",
    ]

    def parse(self, response):
        for link in response.css(".products a.product-title::attr(href)"):
            yield response.follow(link, self.parse_product)
        for link in response.xpath("//a[@title='layout.pagination.next_html']"):
            yield response.follow(link, self.parse)

    def parse_product(self, response):

        price = int("".join(response.css("#ProductPrice::text").re(r"\d+")))

        image_url = response.css("#ProductPhoto img::attr(src)").get()
        sku = image_url.split("/")[-1].split("-")[0]

        yield {
            "sku": sku,
            "name": response.css(".product-title h1::text").get(),
            "make": response.xpath("//meta[@name='twitter:data2']/@content").get(),
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
