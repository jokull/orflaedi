import scrapy


def get_original_image_url(url):
    # image_urls have this appendage for thumbnails _600x500.png ... remove it
    folder, filename = url.rsplit("/", 1)
    filename, query = filename.rsplit("?", 1)
    filename_base, extension = filename.rsplit(".", 1)
    filename_base, _ = filename_base.rsplit("_", 1)
    return "{}/{}.{}?{}".format(folder, filename_base, extension, query)


class NovaSpider(scrapy.Spider):
    name = "nova"

    start_urls = [
        "https://www.nova.is/barinn/dotabud?type=Rafskúta",
        "https://www.nova.is/barinn/dotabud?type=Rafhj%C3%B3l",
    ]

    def parse(self, response):
        for link in response.css("._3HOZOUI1WV a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        sku = response.url
        name = response.css("._2lrIFynBxV::text").get().title()
        make = response.css("._1A6KQNOkFI::text").get().title()
        image_url = response.css("._2l8kk3sVj1::attr('src')").get()
        image_url = get_original_image_url(image_url)
        price = int("".join(response.css(".OptionPrice__optionPrice___2qA1G::text").re(r"\d+")))

        if price > 20_000:
            yield {
                "sku": sku,
                "name": name,
                "make": make,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": response.url,
            }
