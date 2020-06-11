import json
import scrapy


from orflaedi.models import VehicleClassEnum


products = {
    "3903001": ('Xiaomi', 'M365'),
    "3903008": ('Rawlink', 'Rawlink'),
}


structure = (
    (VehicleClassEnum.bike_c, "https://www.husa.is/umbraco/api/product/GetProducts?categoryId=5637294576"),
    (VehicleClassEnum.bike_b, "https://www.husa.is/umbraco/api/product/GetProducts?categoryId=5637171587"),
)

class HusasmidjanSpider(scrapy.Spider):
    name = "husasmidjan"

    start_urls = [url for _, url in structure]

    def parse(self, response):

        for classification, url in structure:
            if url == response.url:
                break
        else:
            raise

        for product in json.loads(response.text):
            sku = product['Sku']
            if sku in products:
                name, make = products[sku]
            else:
                name = product['Title']
                make = product.get('Brand')

            prefix = 'Reiðhjól Rafmagns '
            if name.startswith(prefix):
                name = name[len(prefix):]

            yield {
                "sku": sku,
                "name": name,
                "make": make,
                "classification": classification,
                "price": product['CurrencyString'],
                "file_urls": [response.urljoin(product['ImageUrl'])],
                "scrape_url": response.urljoin(product['Url']),

            }
