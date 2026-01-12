import json
import scrapy

from orflaedi.models import VehicleClassEnum


class ElkoSpider(scrapy.Spider):
    name = "elko"

    start_urls = [
        "https://elko.is/voruflokkar/farartaeki-339?categories=188",
        "https://elko.is/voruflokkar/lett-bifhjol-287",
    ]

    def parse(self, response):
        for link in response.xpath("//a[contains(@href, '/vorur/')]/@href").getall():
            yield response.follow(link, self.parse_product)

    def parse_product(self, response):
        # Extract JSON data from Next.js __NEXT_DATA__ script
        script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not script:
            return None
        
        try:
            data = json.loads(script)
            props = data.get("props", {}).get("pageProps", {})
            product = props.get("initialProduct", {})
            variant = props.get("initialVariant", {})
        except (json.JSONDecodeError, KeyError):
            return None
        
        name = product.get("name", "")
        if not name:
            return None
        
        # Extract make from name (first word)
        parts = name.split(" ", 1)
        if len(parts) < 2:
            return None
        make, name = parts
        
        # Get SKU
        sku = variant.get("sku")
        if not sku:
            return None
        
        # Get price from listings
        listings = variant.get("listings", {})
        webshop = listings.get("webshop", {})
        price_info = webshop.get("price", {})
        price = price_info.get("discountedPrice") or price_info.get("price")
        
        if not price or price < 10000:
            return None
        
        # Get image
        images = variant.get("images", [])
        file_urls = []
        if images:
            first_image = images[0].get("image", {})
            image_url = first_image.get("jpgL") or first_image.get("webpL")
            if image_url:
                file_urls = [image_url]
        
        # Determine classification based on category or name
        product_type = product.get("type", "")
        name_lower = name.lower()
        
        if "hlaupahjól" in name_lower or product_type == "farartaeki":
            classification = VehicleClassEnum.bike_c
        elif "bifhjól" in name_lower or "létt bifhjól" in name_lower:
            classification = VehicleClassEnum.lb_2
        else:
            classification = VehicleClassEnum.bike_c

        yield {
            "sku": sku,
            "name": name,
            "make": make,
            "classification": classification,
            "price": price,
            "file_urls": file_urls,
            "scrape_url": response.url,
        }
