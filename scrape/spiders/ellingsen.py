from w3lib import url as w3lib_url
import scrapy


class EllingsenSpider(scrapy.Spider):
    name = "ellingsen"

    start_urls = [
        "https://ellingsen.s4s.is/ellingsen/rafhjol/oell-rafhjol",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/issimo/rafhjol",
        "https://ellingsen.s4s.is/ellingsen/rafhjol/merida",
    ]

    def parse(self, response):
        for el in response.css(".products-container .product"):
            if el.css(".product_Discount_Text::text").get() == "Uppselt":
                continue
            yield response.follow(el.css("a::attr(href)")[1], self.parse_product)

    def parse_product(self, response):

        price = int(
            "".join(response.css(".information>.product-price::text").re(r"\d+"))
        )

        file_urls = []
        for image_url in response.css(".large-image-preview img::attr(src)").getall():
            if not image_url.endswith(".jpg"):
                continue
            url = response.urljoin(image_url)
            url = w3lib_url.add_or_replace_parameters(
                url, {"Width": "2400", "Height": "2400"}
            )
            file_urls.append(url)

        name = response.css(".information>.product-name::text").get()
        make = None

        for trim in ("rafhlaupahjól", "rafhjól"):
            if name.endswith(f" {trim}"):
                name = name[: -len(f" {trim}")]

        if name.startswith("Fantic Issimo"):
            make, name = name.split(" ", 1)
            name = " ".join(name.split()[:2])

        if name == "Mate X Bike":
            make, name = "Mate", "Mate X"

        if name == "Legend eBike Milano":
            make, name = "Legend", "Milano"

        if name == "Legend eBike Monza":
            make, name = "Legend", "Monza"

        if name == "Legend eBike Siena":
            make, name = "Legend", "Siena"

        for _make in ("Tern", "Zero"):
            if name.startswith(_make):
                make, name = _make, name

        yield {
            "sku": response.css(".information>.tiny-productID::text").get(),
            "name": name,
            "make": make,
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
        }
