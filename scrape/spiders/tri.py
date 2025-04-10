import json
import os
import scrapy

from scrapy.http import JsonRequest

"""
curl 'https://tri.is/api/Item/' \
-X 'POST' \
-H 'Content-Type: application/json' \
-H 'Accept: application/json, text/plain, */*' \
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IjBjN2JlMTNmLTVkZGUtNGRiOS1iMjYyLTdkZGZhZGE2ZjEyZiIsIlVzZXJJZCI6IjBjN2JlMTNmLTVkZGUtNGRiOS1iMjYyLTdkZGZhZGE2ZjEyZiIsIkluc3RhbGxhdGlvbklkIjoiODgxNDFBMTEtQ0FCMC00QjcwLUI0N0YtODVCMEU2QjMxODk5IiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTczODQxNzQzNywiZXhwIjoxNzM5MDIyMjM3LCJpYXQiOjE3Mzg0MTc0Mzd9.Gfhd6uaeOB4J4WGEkPAx6wQaLSbaLG8hLS9dw7hYIZY' \
-H 'Sec-Fetch-Site: same-origin' \
-H 'Accept-Language: en-GB,en;q=0.9' \
-H 'Accept-Encoding: gzip, deflate, br' \
-H 'Sec-Fetch-Mode: cors' \
-H 'Origin: https://tri.is' \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15' \
-H 'Content-Length: 345' \
-H 'Connection: keep-alive' \
-H 'Sec-Fetch-Dest: empty' \
-H 'Cookie: _fbp=fb.1.1738417440997.33803704338218544; _ga=GA1.1.470114118.1738417441; _ga_TRWKVW16JC=GS1.1.1738417440.1.1.1738417487.13.0.0; showPopup=unset; selectedViewSearch=grid; CookieConsent={stamp:%27PlaGkYbzZ3ZXUrwqZb3Nrkt2dzvPC6O41lJwJmdFPXo8QlrYAd2ceg==%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cmethod:%27explicit%27%2Cver:1%2Cutc:1738417440662%2Cregion:%27is%27}; showMailPopup=unset; ARRAffinity=d886985d948de2f194492fcf5ada89566c7eab1ef13a27d2972352bcb41430eb; ARRAffinitySameSite=d886985d948de2f194492fcf5ada89566c7eab1ef13a27d2972352bcb41430eb' \
-H 'Priority: u=3, i' \
--data-binary '{"isComputed":false,"customerNumber":"1111111119","withImportantTags":true,"withAllTags":true,"ignoreMultiDescriptions":true,"maxAgeInDays":0,"withCategories":true,"withMainStoreCategories":false,"action":1012,"item":{"itemCategoryCode":"127","installationId":"88141A11-CAB0-4B70-B47F-85B0E6B31899"},"key":"0c7be13f-5dde-4db9-b262-7ddfada6f12f"}'
"""


class TriSpider(scrapy.Spider):
    """This is an ajax scroll scraper"""

    name = "tri"
    handle_httpstatus_list = [401]

    def start_requests(self):
        for category_code in (128, 129, 130):
            yield scrapy.http.JsonRequest(
                "https://tri.is/api/Item/",
                method="POST",
                headers={
                    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImY0YzE1OGU1LTUyZWMtNGE2OC05YTc1LTFiN2U1MDVhZjYwMCIsIlVzZXJJZCI6ImY0YzE1OGU1LTUyZWMtNGE2OC05YTc1LTFiN2U1MDVhZjYwMCIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTY0ODgwNTE4OSwiZXhwIjoxNjUxMzk3MTg5LCJpYXQiOjE2NDg4MDUxODl9.kFtDTGR-2CDK3cySxTqOegvhDLsuj7jZ0nOF5MyeuVY"
                },
                data={
                    "isComputed": False,
                    "customerNumber": "1111111119",
                    "withImportantTags": True,
                    "withAllTags": True,
                    "ignoreMultiDescriptions": True,
                    "maxAgeInDays": 0,
                    "withCategories": True,
                    "withMainStoreCategories": False,
                    "action": 1012,
                    "item": {
                        "itemCategoryCode": "127",
                        "installationId": "88141A11-CAB0-4B70-B47F-85B0E6B31899",
                    },
                    "key": "0c7be13f-5dde-4db9-b262-7ddfada6f12f",
                },
            )

    def parse(self, response):
        self.skip = True
        for product in json.loads(response.body)["items"]:
            name = product["name"]
            make = None
            if name.startswith("Cube "):
                name = name[len("Cube ") :]
                make = "Cube"
            image_url = response.urljoin(product['imageUrl'])
            if image_url == "https://tri.is/images/":
                image_url = response.urljoin(product['thumbNailUrl'])

            # Insert "_large" before the file extension
            filename, ext = os.path.splitext(image_url)

            if filename.endswith("_thumbnail"):
                filename, _ = filename.rsplit("_", 1)

            # Optional check to avoid double-adding '_large'
            # if "_large" not in filename:
            image_url_large = f"{filename}_large{ext}"

            url = response.urljoin(f"/vara/{product['slug']}")

            if product["no"] == "536252":
                return

            yield {
                "sku": product["no"],
                "price": int(round(product["salesPrice"])),
                "name": name,
                "make": make,
                "file_urls": [image_url_large],
                "scrape_url": url,
            }
