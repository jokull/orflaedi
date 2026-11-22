from scrape.spiders.tri import large_image_url


def test_large_image_url_adds_suffix_once():
    assert (
        large_image_url("https://tri.is/images/bike.webp")
        == "https://tri.is/images/bike_large.webp"
    )
    assert (
        large_image_url("https://tri.is/images/bike_thumbnail.webp")
        == "https://tri.is/images/bike_large.webp"
    )
    assert (
        large_image_url("https://tri.is/images/bike_large.webp")
        == "https://tri.is/images/bike_large.webp"
    )
