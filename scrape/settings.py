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
# 429 is handled by TooManyRequestsBackoffMiddleware, which slows the domain
# down before retrying.
RETRY_HTTP_CODES = [500, 502, 503, 504]
DOWNLOADER_MIDDLEWARES = {
    # Runs before RetryMiddleware (550) on responses.
    "scrape.middlewares.TooManyRequestsBackoffMiddleware": 560,
}
SPIDER_MIDDLEWARES = {
    "scrape.middlewares.BrowserOnlyMiddleware": 10,
}
BACKOFF_429_RETRY_TIMES = 8
BACKOFF_429_MAX_DELAY = 60
# Shopify throttles Twisted's TLS fingerprint; fetch HTTPS through urllib.
DOWNLOAD_HANDLERS = {
    "https": "scrape.handlers.UrllibDownloadHandler",
}
