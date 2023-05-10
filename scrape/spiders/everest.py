from w3lib import url as w3lib_url
import scrapy


class EverestSpider(scrapy.Spider):
    name = "everest"

    start_urls = [
        "http://www.everest.is/is/hjol/rafmagnshjol",
    ]

    def parse(self, response):
        for row in response.css(".products .product"):
            image_url = response.urljoin(row.css("a img::attr('src')").get())
            make, name = row.css("h3 a span::text").get().split(" ", 1)

            price = "".join(row.css(".priceDiff>.price span.n::text").re(r"\d+"))
            if not price:
                continue
            price = int(price)

            sku = row.css("a::attr('href')").get()

            yield {
                "sku": sku,
                "make": make,
                "name": name,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": response.url,
            }
