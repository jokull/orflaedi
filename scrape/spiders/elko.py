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
        for link in response.css(".fpJyEp a"):
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):

        make, name = response.css("h1::text").get().split(" ", 1)
        if " - " in name:
            name = name.split(" - ", 1)[0]

        sku = response.css(".bbyYtt::text").get().strip()

        price = int("".join(response.css(".doQNfU::text").re(r"\d+")))

        if price < 10000:
            return None

        file_urls = [response.css(".slick-slide .sc-e8985f8b-8::attr('src')")[0].get()]
        classification = (
            VehicleClassEnum.bike_c
            if (response.css(".eyHLkH ::text")[2].get() == "Hlaupahjól")
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
