"""Spiders that must run through a real browser (scrape/browser_crawl.py).

Shopify throttles non-browser clients from the production IP, so these are
crawled on the host by bin/update-and-deploy.sh and skipped by the Docker
scrapy runner.
"""

BROWSER_SPIDERS = frozenset(
    {
        "berlin",
        "hjolasprettur",
        "kuldi",
        "markid",
        "ofsi",
        "scb",
        "t2",
        "unno",
    }
)
