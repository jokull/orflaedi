import json
from urllib.parse import quote

import scrapy

from orflaedi.models import VehicleClassEnum


class EllingsenSpider(scrapy.Spider):
    """
    Scrapes Ellingsen e-bikes via the Dynamicweb backend JSON API
    (rather than the client-rendered s4s.is SPA). Two calls:

      1. POST /dwapi/ecommerce/products — product metadata + pagination
      2. GET  /api/products/live         — current prices/stock for the SKUs
    """

    name = "ellingsen"
    custom_settings = {"ROBOTSTXT_OBEY": False}  # dwapi endpoints aren't in robots.txt

    API_BASE = "https://backend.s4s.is"
    CATEGORY_ENDPOINT = (
        API_BASE
        + "/dwapi/ecommerce/products"
        "?RepositoryName=EllingsenProducts"
        "&QueryName=EllingsenQuery"
        "&GroupID=GROUP705,GROUP541,GROUP603,GROUP547,GROUP868,GROUP605,GROUP793,GROUP817,GROUP818"
    )
    LIVE_ENDPOINT = API_BASE + "/api/products/live"
    PRODUCT_URL = "https://s4s.is/ellingsen/vara?ProductId={sku}"

    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://s4s.is/",
    }

    def start_requests(self):
        yield self._category_request(page=1)

    def _category_request(self, page):
        body = json.dumps(
            {
                "CurrentPage": page,
                "PageSize": 100,
                "ShopID": "SHOP1",
                "CountryCode": "IS",
                "CurrencyCode": "ISK",
                "FilledProperties": [
                    "Products",
                    "PageCount",
                    "CurrentPage",
                    "TotalProductsCount",
                ],
                "ProductSettings": {
                    "FilledProperties": [
                        "Id",
                        "Number",
                        "Name",
                        "Title",
                        "DefaultImage",
                        "Manufacturer",
                    ]
                },
            }
        )
        return scrapy.Request(
            self.CATEGORY_ENDPOINT,
            method="POST",
            body=body,
            headers=self.HEADERS,
            callback=self.parse_category,
            cb_kwargs={"page": page},
        )

    def parse_category(self, response, page):
        data = json.loads(response.text)
        products = data.get("Products") or []
        if not products:
            return

        numbers = [p["Number"] for p in products]
        yield scrapy.Request(
            f"{self.LIVE_ENDPOINT}?Products={','.join(numbers)}&ShopId=SHOP1",
            headers=self.HEADERS,
            callback=self.parse_prices,
            cb_kwargs={"products": products},
        )

        page_count = data.get("PageCount") or 1
        if page < page_count:
            yield self._category_request(page=page + 1)

    def parse_prices(self, response, products):
        prices_by_number = {
            p["Number"]: p for p in (json.loads(response.text).get("Products") or [])
        }

        for product in products:
            sku = product["Number"]
            live = prices_by_number.get(sku)
            if not live:
                continue

            price_info = live.get("Price") or {}
            price = price_info.get("PriceWithVat") or 0
            if price <= 0 or live.get("SoldOut"):
                continue

            default_image = product.get("DefaultImage") or {}
            image_path = default_image.get("Value")
            if not image_path:
                continue
            image_url = (
                f"{self.API_BASE}/Admin/Public/GetImage.ashx"
                f"?Width=5000&Height=5000&Compression=99&Quality=99"
                f"&Image={quote(image_path)}"
            )

            manufacturer = product.get("Manufacturer") or {}
            make = manufacturer.get("Name")
            if make == "Riese & Muller":
                make = "Riese & Müller"

            name = (product.get("Title") or product.get("Name") or "").strip()
            if make and name.startswith(make):
                name = name[len(make) :].strip()

            yield {
                "sku": sku,
                "name": name,
                "make": make,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": self.PRODUCT_URL.format(sku=sku),
                "classification": VehicleClassEnum.bike_b,
            }
