import scrapy


class BikeSpider(scrapy.Spider):
    name = "bike"

    start_urls = [
        "https://bike.is/products/rafmagnshjol",
    ]

    def parse(self, response):
        for product in response.css(".tile .tile-thumb a"):
            yield response.follow(product, self.parse_product)

    def parse_product(self, response):

        els = [
            el.css("::text").get()
            for el in response.css(".preContent p *")
            if len(el.css("*")) == 1
        ]
        name, sku = [el for el in els if el]
        _, sku = sku.split(" ", 1)
        make, name = name.split(" ", 1)
        image_url = response.urljoin(
            response.css(".product-showcase-slider img::attr('src')")[1].get()
        )
        price = int("".join(response.css(".shop-price::text").re(r"\d+")))

        yield {
            "sku": sku.strip(),
            "name": name.strip(),
            "make": make.strip(),
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
