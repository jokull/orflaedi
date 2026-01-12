import html
import json
import re
import scrapy

from orflaedi.models import VehicleClassEnum


class SoliferSpider(scrapy.Spider):
    name = "solifer"

    start_urls = [
        "https://solifer.is/",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def parse(self, response):
        # Find all product links
        links = response.xpath("//a[contains(@href, '/vara/')]/@href").getall()
        seen = set()
        for link in links:
            if link not in seen:
                seen.add(link)
                yield response.follow(link, self.parse_product)

    def parse_product(self, response):
        # Extract GTM product data (contains structured product info)
        gtm_data = response.xpath(
            '//input[@name="gtm4wp_product_data"]/@value'
        ).get()
        
        if not gtm_data:
            return None
        
        try:
            product = json.loads(html.unescape(gtm_data))
        except json.JSONDecodeError:
            return None
        
        name = product.get("item_name", "")
        if not name:
            return None
        
        price = product.get("price")
        if not price or price < 10000:
            return None
        
        sku = str(product.get("sku", ""))
        
        # Get image from og:image meta tag
        image_url = response.xpath('//meta[@property="og:image"]/@content').get()
        file_urls = [image_url] if image_url else []
        
        # Solifer makes e-bikes with 2x2 drive (motor on both wheels)
        # All are bike_b (pedelec e-bikes)
        classification = VehicleClassEnum.bike_b

        yield {
            "sku": f"solifer-{sku}",
            "name": name,
            "make": "Solifer",
            "classification": classification,
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
        }
