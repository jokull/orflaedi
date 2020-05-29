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
        "https://www.nova.is/barinn/dotabud?vendor=Super%20SOCO",
        "https://www.nova.is/barinn/dotabud?type=Rafskúta",
    ]

    def parse(self, response):
        for link in response.css(".BscZe6kcLQ"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        sku = response.url
        name = response.css(".ar9onfjwtl::text").get().title()
        make = response.css("._3IURkV6Lje::text").get().title()
        image_url = response.css("._3VOebxMeP_::attr('src')").get()
        image_url = get_original_image_url(image_url)
        price = int(
            "".join(response.css(".OptionPrice_optionPrice_34JZ4::text").re(r"\d+"))
        )

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
