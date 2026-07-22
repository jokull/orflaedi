from scrape.shopify import parse_products


def test_parse_products_uses_lowest_available_price():
    payload = {
        "products": [
            {
                "id": 123,
                "title": "Vala",
                "handle": "vala",
                "variants": [
                    {"price": "900000.00", "available": True},
                    {"price": "800000.00", "available": True},
                    {"price": "700000.00", "available": False},
                ],
                "images": [{"src": "https://cdn.example/vala.jpg"}],
            }
        ]
    }

    assert list(parse_products(payload, make="Santa Cruz", site_url="https://scb.is")) == [
        {
            "sku": "123",
            "name": "Vala",
            "make": "Santa Cruz",
            "price": 800000,
            "file_urls": ["https://cdn.example/vala.jpg"],
            "scrape_url": "https://scb.is/products/vala",
        }
    ]


def test_parse_products_skips_unavailable_or_incomplete_products():
    payload = {
        "products": [
            {
                "id": 1,
                "title": "Sold out",
                "handle": "sold-out",
                "variants": [{"price": "100", "available": False}],
                "images": [{"src": "https://cdn.example/sold-out.jpg"}],
            },
            {
                "id": 2,
                "title": "No image",
                "handle": "no-image",
                "variants": [{"price": "100", "available": True}],
                "images": [],
            },
        ]
    }

    assert list(parse_products(payload, make="UNNO", site_url="https://unno.is")) == []
