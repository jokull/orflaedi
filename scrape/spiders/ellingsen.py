from w3lib import url as w3lib_url
import scrapy


class EllingsenSpider(scrapy.Spider):
    name = "ellingsen"

    start_urls = [
        "https://ellingsen.s4s.is/ellingsen/rafhjol/mate",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/zero",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/merida",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/tern",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/e-fati",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/legend",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/gpad",
    ]

    def parse(self, response):
        for link in response.css(".products-container .product>a::attr(href)"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        price = int("".join(response.css(".information>.product-price::text").re(r"\d+")))

        file_urls = []
        for image_url in response.css(".large-image-preview img::attr(src)").getall():
            if not image_url.endswith(".jpg"):
                continue
            url = response.urljoin(image_url)
            url = w3lib_url.add_or_replace_parameters(url, {"Width": "2400", "Height": "2400"})
            file_urls.append(url)

        yield {
            "sku": response.css(".information>.tiny-productID::text").get(),
            "name": response.css(".information>.product-name::text").get(),
            "price": price,
            "file_urls": file_urls,
        }
