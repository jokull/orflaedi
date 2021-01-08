IMAGE_URL = "https://www.becycled.be/files/10-2019/ad16444/urban-arrow-family-performance-cx-1181171642_large.jpg"

import scrapy


def get_original_image_url(url):
    # image_urls have this appendage for thumbnails _600x500.png ... remove it
    folder, filename = url.rsplit("/", 1)
    filename, query = filename.rsplit("?", 1)
    filename_base, extension = filename.rsplit(".", 1)
    filename_base, _ = filename_base.rsplit("_", 1)
    return "{}/{}.{}?{}".format(folder, filename_base, extension, query)


class NytjahjolSpider(scrapy.Spider):
    name = "nytjahjol"

    start_urls = [
        "https://www.nytjahjol.is/hjoacutel.html",
    ]

    def parse(self, response):
        el = response.css(".wsite-multicol-tr td")[0]
        make = "Urban Arrow"
        name = "Family Performance CX"
        price = int(''.join([s for s in el.css(".paragraph").re(r"[\d\.]+ kr\.")[0] if s in '1234567890']))
        yield {
            'sku': 'https://www.nytjahjol.is/hjoacutel.html',
            'file_urls': [IMAGE_URL],
            'scrape_url': 'https://www.nytjahjol.is/hjoacutel.html',
            'make': make,
            'name': name,
            'price': price,
        }
