LOG_LEVEL = "ERROR"
SPIDER_MODULES = ["scrape.spiders"]
ITEM_PIPELINES = {
    "scrape.pipelines.DatabasePipeline": 100,
}

# Some retailer sites (e.g. gastec) 403 the default Scrapy UA. Present as a
# regular browser; spiders that need something different can override.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Rate limiting to avoid 429s
DOWNLOAD_DELAY = 2  # 2 seconds between requests
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # One at a time per domain
RANDOMIZE_DOWNLOAD_DELAY = True  # Add jitter

# AutoThrottle for adaptive rate limiting
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Respect robots.txt
ROBOTSTXT_OBEY = True

# Retry settings
RETRY_TIMES = 5
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]
