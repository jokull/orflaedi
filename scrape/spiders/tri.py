import json
from w3lib import url as w3lib_url
import scrapy

from scrapy.http import JsonRequest

"""

curl 'https://tri.is/api/Item/'

-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) Gecko/20100101 Firefox/80.0'
-H 'Accept: application/json, text/plain, */*'
-H 'Accept-Language: en-US,en;q=0.5' --compressed
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6Ijc1MGI0YWU1LTdmNDQtNDY2Mi05OTJkLWNhYzI5MjNlMmNjMiIsIlVzZXJJZCI6Ijc1MGI0YWU1LTdmNDQtNDY2Mi05OTJkLWNhYzI5MjNlMmNjMiIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTYwMDMzOTQ2OSwiZXhwIjoxNjAwOTQ0MjY5LCJpYXQiOjE2MDAzMzk0Njl9.wntjuNqKLseIODabbAmYm8xL0JHjU_KAjPquOVWtH3k'
-H 'Content-Type: application/json'
-H 'Origin: https://tri.is'
-H 'Connection: keep-alive'
-H 'Referer: https://tri.is/voruflokkur/7-rafmagnshjol'
-H 'Cookie: _ga=GA1.2.1688704323.1598385129; cookieconsent_status=dismiss; ARRAffinity=c302ece2eb7eb6fd55dc77d1860502ec67d8434ab3760fed5785cd0560fe98d4; _gid=GA1.2.1922800837.1600339469; _gat_gtag_UA_176996653_1=1'
-H 'Pragma: no-cache'
-H 'Cache-Control: no-cache'
--data-raw '{"action":1012,"item":{"installationId":"4194608E-5859-4927-82ED-57E38800D9BE","itemCategoryCode":"7"},"key":"750b4ae5-7f44-4662-992d-cac2923e2cc2"}'

curl 'https://tri.is/api/Item/'
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 11.1; rv:84.0) Gecko/20100101 Firefox/84.0'
-H 'Accept: application/json, text/plain, */*'
-H 'Accept-Language: en-US,en;q=0.5'
--compressed
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImU4NTY1MGI0LTlmYmEtNDAzMC05MmU4LWU1ZmRmN2YwMzUxYSIsIlVzZXJJZCI6ImU4NTY1MGI0LTlmYmEtNDAzMC05MmU4LWU1ZmRmN2YwMzUxYSIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTYwOTk0NTgzMywiZXhwIjoxNjEyNTM3ODMzLCJpYXQiOjE2MDk5NDU4MzN9.-rqZboTFhApIEJA9TbBh6zdKSGDXVbPpehw-6W9D3eo'
-H 'Content-Type: application/json'
-H 'Origin: https://tri.is'
-H 'Connection: keep-alive'
-H 'Referer: https://tri.is/voruflokkur/7-rafmagnshjol'
-H 'Cookie: ARRAffinity=eeccce1f071ae2a9b91cf780900c188053ae4b2e48c8f13243fa2699fade1e32; ARRAffinitySameSite=eeccce1f071ae2a9b91cf780900c188053ae4b2e48c8f13243fa2699fade1e32; _ga=GA1.2.162009546.1609945833; _gid=GA1.2.1934676362.1609945833; cookieconsent_status=dismiss'
-H 'Pragma: no-cache'
-H 'Cache-Control: no-cache'
--data-raw '{"action":1012,"item":{"installationId":"4194608E-5859-4927-82ED-57E38800D9BE","itemCategoryCode":"7"},"key":"e85650b4-9fba-4030-92e8-e5fdf7f0351a"}'

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
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFlMmZlN2MxLWM3ZmUtNDRjZi1hZTM3LTAyMWQzODdlZjRiZCIsIlVzZXJJZCI6ImFlMmZlN2MxLWM3ZmUtNDRjZi1hZTM3LTAyMWQzODdlZjRiZCIsIkluc3RhbGxhdGlvbklkIjoiNDE5NDYwOEUtNTg1OS00OTI3LTgyRUQtNTdFMzg4MDBEOUJFIiwiQWRtaW4iOiJGYWxzZSIsIm5iZiI6MTYxMjg5OTQwOCwiZXhwIjoxNjE1NDkxNDA4LCJpYXQiOjE2MTI4OTk0MDh9.JL_GHLAEPybhqFsvmRDXZKnvUN669eyE8ullFk0DLRo"
            },
            data={
                "action": 1012,
                "item": {
                    "installationId": "4194608E-5859-4927-82ED-57E38800D9BE",
                    "itemCategoryCode": "7",
                },
                "key": "e85650b4-9fba-4030-92e8-e5fdf7f0351a",
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
