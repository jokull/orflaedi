import json
from w3lib import url as w3lib_url
import scrapy

from scrapy.http import JsonRequest

"""

curl 'https://tri.is/api/Item/' \
-X 'POST' \
-H 'Content-Type: application/json' \
-H 'Accept: application/json, text/plain, */*' \
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImY0YzE1OGU1LTUyZWMtNGE2OC05YTc1LTFiN2U1MDVhZjYwMCIsIlVzZXJJZCI6ImY0YzE1OGU1LTUyZWMtNGE2OC05YTc1LTFiN2U1MDVhZjYwMCIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTY0ODgwNTE4OSwiZXhwIjoxNjUxMzk3MTg5LCJpYXQiOjE2NDg4MDUxODl9.kFtDTGR-2CDK3cySxTqOegvhDLsuj7jZ0nOF5MyeuVY' \
-H 'Accept-Language: en-GB,en;q=0.9' \
-H 'Accept-Encoding: gzip, deflate, br' \
-H 'Host: tri.is' \
-H 'Origin: https://tri.is' \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15' \
-H 'Connection: keep-alive' \
-H 'Referer: https://tri.is/voruflokkur/128-fjallahjol-rafhjol' \
-H 'Content-Length: 169' \
-H 'Cookie: cookieconsent_status=dismiss; _ga=GA1.2.447029418.1648805191; _gid=GA1.2.142441294.1648805191; showMailPopup=unset; showPopup=unset; ARRAffinity=821f3d315b7de303b2592bf162ce2628b1823f4a1099dac41d9a2fe5bc429152; ARRAffinitySameSite=821f3d315b7de303b2592bf162ce2628b1823f4a1099dac41d9a2fe5bc429152' \
--data-binary '{"action":1012,"item":{"installationId":"4194608E-5859-4927-82ED-57E38800D9BE","itemCategoryCode":"128"},"withAllTags":true,"key":"f4c158e5-52ec-4a68-9a75-1b7e505af600"}'
"""


class TriSpider(scrapy.Spider):
    """ This is an ajax scroll scraper

    """

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
                    "action": 1012,
                    "item": {
                        "installationId": "4194608E-5859-4927-82ED-57E38800D9BE",
                        "itemCategoryCode": str(category_code),
                    },
                    "key": "f4c158e5-52ec-4a68-9a75-1b7e505af600",
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
            yield {
                "sku": product["no"],
                "price": int(round(product["salesPrice"])),
                "name": name,
                "make": make,
                "file_urls": [response.urljoin(product["imageUrl"])],
                "scrape_url": response.urljoin(f'/vara/{product["slug"]}'),
            }
