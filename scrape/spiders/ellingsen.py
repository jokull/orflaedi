import json
import re
import scrapy

from orflaedi.models import VehicleClassEnum


class EllingsenSpider(scrapy.Spider):
    name = "ellingsen"

    start_urls = [
        "https://rafhjolasetur.is/collections/rafhjol",
        "https://rafhjolasetur.is/collections/rafhlaupahjol",
    ]

    def parse(self, response):
        is_class_c = "rafhlaupahjol" in response.url
        print(is_class_c, response.url)
        for el in response.css(".collection-matrix .product-wrap"):
            yield response.follow(
                el.css("a::attr(href)")[1],
                self.parse_product,
                cb_kwargs={"is_class_c": is_class_c},
            )

    def parse_product(self, response, is_class_c):

        classification = (
            VehicleClassEnum.bike_c if is_class_c else VehicleClassEnum.bike_b
        )

        print(is_class_c, classification)

        file_urls = [
            "https:"
            + response.css(".product-gallery__container .lazyloaded::attr(src)")
            .get()
            .replace("_1200x", "_5000x")
        ]

        obj = None

        for script_tag in response.css("script::text").getall():
            if "var meta = " in script_tag:
                _, obj = script_tag.split("var meta = ")
                obj, _ = obj.split(";", 1)
                obj = json.loads(obj)

        if obj is None:
            print("NO OBJ!")
            return None

        sku = str(obj["product"]["id"])
        make = obj["product"]["vendor"]
        price = int(obj["product"]["variants"][0]["price"] / 100)
        name = obj["product"]["variants"][0]["name"]

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
