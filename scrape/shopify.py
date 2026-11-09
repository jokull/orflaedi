"""Helpers shared by Shopify-backed retailer spiders."""


def parse_products(payload, *, make, site_url, include_unavailable=False):
    """Yield normalized bike items from a Shopify products response.

    include_unavailable keeps sold-out products (priced from all variants),
    for shops that sell incoming stock as pre-orders while it shows sold out.
    """
    for product in payload.get("products") or []:
        variants = product.get("variants") or []
        available_variants = [v for v in variants if v.get("available", True)]
        if not available_variants and include_unavailable:
            available_variants = variants
        prices = []
        for variant in available_variants:
            try:
                price = int(float(variant.get("price") or 0))
            except (TypeError, ValueError):
                continue
            if price > 0:
                prices.append(price)

        images = product.get("images") or []
        image_url = images[0].get("src") if images else None
        handle = product.get("handle")
        if not prices or not image_url or not handle:
            continue

        yield {
            "sku": str(product["id"]),
            "name": product.get("title") or "",
            "make": make,
            "price": min(prices),
            "file_urls": [image_url],
            "scrape_url": f"{site_url}/products/{handle}",
        }
