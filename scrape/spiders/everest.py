from w3lib import url as w3lib_url
import scrapy


class EverestSpider(scrapy.Spider):
    name = "everest"

    start_urls = [
        "http://www.everest.is/is/hjol/rafmagnshjol",
    ]

    def parse(self, response):
        for row in response.css(".singleImage"):
            image_url = response.urljoin(row.css("a::attr('href')").get())
            make = row.css("h2 strong::text").get()
            name = row.css("h2::text").get().strip()
            name_el, description_el, price_el = row.css(".description>*")

            price = "".join(price_el.css("::text").re(r"\d+"))
            if not price:
                continue
            price = int(price)

            motor_model = None
            for list_item in description_el.css("::text").getall():
                if ": " not in list_item:
                    continue
                key, value = list_item.split(": ", 1)
                if key == "Mótor":
                    motor_model = value

            sku = name

            yield {
                "sku": sku,
                "make": make,
                "name": name,
                "motor_model": motor_model,
                "price": price,
                "file_urls": [image_url],
                "scrape_url": response.url,
            }
