import json
from w3lib import url as w3lib_url
import scrapy

from scrapy.http import JsonRequest

"""

curl 'https://tri.is/api/Item/' \
-X 'POST' \
-H 'Content-Type: application/json' \
-H 'Accept: application/json, text/plain, */*' \
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImI3MmE2ZTkxLTE0YTQtNGRjYy04ZWUxLWIzZmNlMTgwMWQ2ZiIsIlVzZXJJZCI6ImI3MmE2ZTkxLTE0YTQtNGRjYy04ZWUxLWIzZmNlMTgwMWQ2ZiIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTYxNjUxMjExNCwiZXhwIjoxNjE5MTA0MTE0LCJpYXQiOjE2MTY1MTIxMTR9.VU6a4kNnEB7pEVb2aneQIiWCHr8SWeTVq1enuS8UfiQ' \
-H 'Accept-Language: en-us' \
-H 'Accept-Encoding: gzip, deflate, br' \
-H 'Host: tri.is' \
-H 'Origin: https://tri.is' \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15' \
-H 'Connection: keep-alive' \
-H 'Referer: https://tri.is/voruflokkur/75-rafhjol?p=3&sort=Ver%C3%B0i%20-%20l%C3%A6gst%20fyrst' \
-H 'Content-Length: 149' \
-H 'Cookie: _ga=GA1.2.741821048.1616512115; _gat_gtag_UA_190846308_1=1; _gid=GA1.2.2097464263.1616512115; ARRAffinity=b23cb19e85cc9ba591ea2c3dffa0cd9f330a52b9028ecd388e61395a96675609; ARRAffinitySameSite=b23cb19e85cc9ba591ea2c3dffa0cd9f330a52b9028ecd388e61395a96675609' \
--data-binary '{"action":1012,"item":{"installationId":"4194608E-5859-4927-82ED-57E38800D9BE","itemCategoryCode":"75"},"key":"b72a6e91-14a4-4dcc-8ee1-b3fce1801d6f"}'

"""


class TriSpider(scrapy.Spider):
    """ This is an ajax scroll scraper

    """

    name = "tri"
    handle_httpstatus_list = [401]

    def start_requests(self):
        request = scrapy.http.JsonRequest(
            "https://tri.is/api/Item/",
            method="POST",
            headers={
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImI3MmE2ZTkxLTE0YTQtNGRjYy04ZWUxLWIzZmNlMTgwMWQ2ZiIsIlVzZXJJZCI6ImI3MmE2ZTkxLTE0YTQtNGRjYy04ZWUxLWIzZmNlMTgwMWQ2ZiIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTYxNjUxMjExNCwiZXhwIjoxNjE5MTA0MTE0LCJpYXQiOjE2MTY1MTIxMTR9.VU6a4kNnEB7pEVb2aneQIiWCHr8SWeTVq1enuS8UfiQ"
            },
            data={
                "action": 1012,
                "item": {
                    "installationId": "4194608E-5859-4927-82ED-57E38800D9BE",
                    "itemCategoryCode": "75",
                },
                "key": "b72a6e91-14a4-4dcc-8ee1-b3fce1801d6f",
            },
        )
        yield request

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
