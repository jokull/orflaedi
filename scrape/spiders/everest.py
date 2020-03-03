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
            name_el, description_el, price_el = row.css(".description>*")
            make, name = name_el.css("::text").get().split(" ", 1)

            price = int("".join(price_el.css("span")[0].re(r"\d+")))

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
