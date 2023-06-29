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
        "https://elko.is/voruflokkar/farartaeki-339?categories=188",
        "https://elko.is/voruflokkar/lett-bifhjol-287",
    ]

    def parse(self, response):
        for link in response.xpath("//a[contains(@href, '/vorur/')]"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):
        name_node = response.xpath("//h1")
        make, name = name_node.xpath("text()").get().split(" ", 1)
        if " - " in name:
            name = name.split(" - ", 1)[0]

        sku = name_node.xpath("following-sibling::div[1]/span/text()").get().strip()

        price = int("".join(response.css(".large::text").re(r"\d+")))

        if price < 10000:
            return None
        carousel = response.css(".slick-track")
        file_urls = [carousel.xpath("//button/div/@src")[0].get()]
        classification = (
            VehicleClassEnum.bike_c
            if (
                response.xpath("//a[contains(@href, '/voruflokkar/')]/text()")[1].get()
                == "Hlaupahjól"
            )
            else VehicleClassEnum.lb_2
        )

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "classification": classification,
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
        }
