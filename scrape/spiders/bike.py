import scrapy


class BikeSpider(scrapy.Spider):
    name = "bike"

    start_urls = [
        "https://fjallakofinn.is/is/products/Rafhjól,%20götuhjól",
        "https://fjallakofinn.is/is/products/rafhjol-fulldempud-fjallahjol",
    ]

    def parse(self, response):
        for product in response.css(".product-grid .item"):
            make = product.css("h4::text").get()
            name = product.css("em strong::text").get()
            if name.startswith("CONWAY "):
                name = name[len("CONWAY ") :]
            price = "".join(product.css(".price::text").re(r"\d+"))
            link = product.css("a.thumb::attr('href')").get()
            yield response.follow(
                link, self.parse_product, cb_kwargs={"make": make, "name": name, "price": price}
            )

    def parse_product(self, response, make, name, price):

        sku = response.css('input[name="productId"]').xpath("string(@value)").get()
        image_url = response.css(".largeImg_wrap a::attr('href')").get()
        if image_url.startswith("//"):
            image_url = "https:" + image_url

        yield {
            "sku": sku.strip(),
            "name": name.strip(),
            "make": make.strip().lower().title(),
            "price": int(price),
            "file_urls": [image_url],
            "scrape_url": response.url,
        }
