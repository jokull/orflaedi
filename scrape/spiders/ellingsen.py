import json
import re
import scrapy

from orflaedi.models import VehicleClassEnum


class EllingsenSpider(scrapy.Spider):
    name = "ellingsen"

    start_urls = [
        "https://s4s.is/rafhjolasetrid/rafhjol/borgarhjol",
        "https://s4s.is/rafhjolasetrid/rafhjol/fjallahjol",
        "https://s4s.is/rafhjolasetrid/rafhjol/fjoelskyldurafhjol",
        "https://s4s.is/rafhjolasetrid/rafhlaupahjol/oell-rafhlaupahjol",
    ]

    def parse(self, response):
        is_class_c = "rafhlaupahjol" in response.url
        for el in response.css(".productCard a"):
            yield response.follow(
                el, self.parse_product, cb_kwargs={"is_class_c": is_class_c},
            )

    def parse_product(self, response, is_class_c):

        classification = VehicleClassEnum.bike_c if is_class_c else VehicleClassEnum.bike_b

        image_url = response.css(".productImage::attr(src)").get()

        if image_url:
            file_urls = [image_url.replace("855", "5000").replace("925", "5000")]
        else:
            return

        sku = response.css(".productNumber::text").get()
        make = response.css(".productBrand::text").get()
        
        price_text = response.css(".productPrice::text").get()
        if price_text:
            price = int("".join(re.findall(r"\d+", price_text)))
        else:
            return
        
        if price == 0:
            return

        name = response.css(".productName::text").get()

        if make == "Riese & Muller":
            make = "Riese & Müller"

        if make in name:
            name = "".join(name.split(make)).strip()

        stripwords = [
            "svart",
            "hvítt",
            "blátt",
            "gult",
            "rautt",
            "blátt",
            "brúnt",
            "grátt",
            "17.5ah",
            "36v",
            "ebike",
            "rafhlaupahjól",
            "rafhjól",
            "fjallarafhjól",
        ]

        name = " ".join(w for w in name.split() if w.lower() not in stripwords)

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
            "classification": classification,
        }
