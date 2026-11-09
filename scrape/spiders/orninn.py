import json
import re

import scrapy
from scrapy.http import JsonRequest


QUERY = """
query Ebikes($after: String) {
  category(slug: "hjol-rafhjol") {
    products(first: 100, after: $after, channel: "hjol") {
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          slug
          name
          isAvailableForPurchase
          attributes { attribute { slug } values { name } }
          thumbnail(size: 1024) { url }
          variants { sku quantityAvailable }
          pricing { priceRange { start { gross { amount } } } }
        }
      }
    }
  }
}
"""

# Pre-order listings are prefixed "Forpöntun: " in the product name.
PREORDER_RE = re.compile(r"^\s*forpöntun\s*:\s*", re.I)
# Trek part numbers, e.g. variant "0100652981-001" -> "0100652981". These
# match the SKUs the old WooCommerce scraper stored, so rows keep identity.
PART_NO_RE = re.compile(r"^(\d{10})(?:-\d+)?$")


class OrninnSpider(scrapy.Spider):
    """Örninn moved from WooCommerce to a Next.js storefront on Saleor.

    Query Saleor's public GraphQL API for the E-Bikes category.
    """

    name = "orninn"
    api_url = "https://saleor.orninn.is/graphql/"
    site_url = "https://orninn.is"

    def start_requests(self):
        yield self._request(None)

    def _request(self, after):
        return JsonRequest(
            self.api_url,
            data={"query": QUERY, "variables": {"after": after}},
            callback=self.parse,
            dont_filter=True,
        )

    def parse(self, response):
        payload = json.loads(response.text)
        if payload.get("errors"):
            raise ValueError(f"Saleor errors: {payload['errors']}")
        products = payload["data"]["category"]["products"]

        for edge in products["edges"]:
            node = edge["node"]
            if not node.get("isAvailableForPurchase"):
                continue
            try:
                price = int(node["pricing"]["priceRange"]["start"]["gross"]["amount"])
            except (KeyError, TypeError, ValueError):
                continue
            image = (node.get("thumbnail") or {}).get("url")
            if not price or not image:
                continue

            make = None
            for attr in node.get("attributes") or []:
                if attr["attribute"]["slug"] == "brand" and attr["values"]:
                    make = attr["values"][0]["name"]
            if make and make.isupper() and len(make) > 3:
                make = make.title()  # "TREK" -> "Trek", "STOER" -> "Stoer"

            name = PREORDER_RE.sub("", node["name"]).strip()
            if make and name.lower().startswith(make.lower() + " "):
                name = name[len(make) + 1:]

            sku = node["slug"]
            for variant in node.get("variants") or []:
                match = PART_NO_RE.match(variant.get("sku") or "")
                if match:
                    sku = match.group(1)
                    break

            yield {
                "sku": sku,
                "name": name,
                "make": make,
                "price": price,
                "file_urls": [image],
                "scrape_url": f"{self.site_url}/products/{node['slug']}",
            }

        page = products["pageInfo"]
        if page["hasNextPage"]:
            yield self._request(page["endCursor"])
