from w3lib import url as w3lib_url
import scrapy


class TriSpider(scrapy.Spider):
    """ This is an ajax scroll scraper

    """

    name = "tri"

    start_urls = [
        "https://tri.is/products/rafmagnshlaupahjol?page=1&ajax=1",
        "https://tri.is/products/rafmagnshjol?page=1&ajax=1",
    ]

    def parse(self, response):
        products = response.css(".product")
        for product in products:
            link = product.css(".footer>a::attr(href)").get()
            yield response.follow("https://tri.is{}".format(link), self.parse_product)
        if products:
            current_page = w3lib_url.url_query_parameter(response.url, "page", default="1")
            yield response.follow(
                w3lib_url.add_or_replace_parameters(
                    response.url, {"page": str(int(current_page) + 1)}
                ),
                self.parse,
            )

    def parse_product(self, response):

        make, name = response.css("h1::text").get().split(" ", 1)

        yield {
            "sku": response.xpath("//form/input[@name='productId']/@value").get(),
            "name": name,
            "make": make,
            "motor_model": response.xpath(
                "//div[@id='techno']//li[span='DRIVE UNIT']/span[2]//text()"
            ).get(),
            "price": int("".join(response.css(".price").re(r"\d+"))),
            "file_urls": [response.css(".ms-slide img::attr(src)").get()],
            "scrape_url": response.url,
        }
