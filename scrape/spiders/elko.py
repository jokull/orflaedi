from w3lib import url as w3lib_url
import scrapy

from orflaedi.models import VehicleClassEnum


colors = {
    "Svart",
    "Hvítt",
    "Blátt",
    "Rautt",
    "Grænt",
    "Khaki",
    "Grátt",
    "Silfur",
}


skipwords = {"svifbretti", " f. ", "rafhlaða"}


def get_name_and_color(name):
    color = None
    if " - " in name:
        name, color = name.rsplit(" - ", 1)
    return name, color


def get_clean_name_and_classification(name):
    parts = []
    classification = None
    for part in name.split():
        if part.lower() == "rafmagnshlaupahjól":
            classification = VehicleClassEnum.bike_c
            continue
        if part.lower() == "rafmagnsbifhjól":
            classification = VehicleClassEnum.lb_2
            continue
        parts.append(part)
    return " ".join(parts), classification


class ElkoSpider(scrapy.Spider):
    name = "elko"

    start_urls = [
        "https://elko.is/ahugamal/svifbretti-og-hlaupahjol",
        "https://elko.is/ahugamal/lett-bifhjol",
    ]

    def parse(self, response):
        products_without_color = set()
        for link in response.css(".products-grid .product-name a"):
            name = link.css("::text").get()
            name, _ = get_name_and_color(name)
            if name.lower() in products_without_color:
                continue
            products_without_color.add(name.lower())
            if (
                response.url == "https://elko.is/ahugamal/svifbretti-og-hlaupahjol"
                and any(skipword in name for skipword in skipwords)
            ):
                # Filter out accessories from this page
                continue
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        sku = response.css(".product-page .product-code::text").get().strip()
        price = int(
            "".join(response.css(".product-page .product-price::text").re(r"\d+"))
        )

        if price < 10000:
            return None

        file_urls = [response.css(".big-image img::attr(data-lazy-src)").get()]
        name = response.css(".product-page .product-name::text").get().strip()
        name, _ = get_name_and_color(name)
        name, classification = get_clean_name_and_classification(name)

        make = (
            response.css(".tab-pane .table")
            .xpath("//tr[td='Framleiðandi']/td[2]/text()")
            .get()
            .strip()
        )

        if make == "Swagtron":
            name = sku

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "classification": classification,
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
        }
