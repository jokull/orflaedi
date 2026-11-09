"""Downloader middlewares."""
import logging

from scrapy.downloadermiddlewares.retry import get_retry_request

logger = logging.getLogger(__name__)


class TooManyRequestsBackoffMiddleware:
    """Back off per domain on HTTP 429 instead of hammering the shop.

    Scrapy 2.6's RetryMiddleware re-queues a 429 immediately, so six
    attempts burn out in ~12s against Shopify's rate limiter. Here a 429
    raises the download slot's delay (doubling, honouring Retry-After,
    capped) before retrying, so later requests to that host slow down too.
    AutoThrottle never lowers a delay on non-200 responses, and only eases
    it back down as 200s arrive.
    """

    def __init__(self, crawler):
        self.crawler = crawler
        settings = crawler.settings
        self.max_delay = settings.getfloat("BACKOFF_429_MAX_DELAY", 60.0)
        self.min_delay = settings.getfloat("BACKOFF_429_MIN_DELAY", 5.0)
        self.retry_times = settings.getint("BACKOFF_429_RETRY_TIMES", 8)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if response.status != 429:
            return response

        slot_key = request.meta.get("download_slot")
        slot = self.crawler.engine.downloader.slots.get(slot_key) if slot_key else None
        if slot is not None:
            retry_after = _parse_retry_after(response.headers.get(b"Retry-After"))
            slot.delay = min(
                self.max_delay,
                max(self.min_delay, slot.delay * 2, retry_after or 0),
            )
            logger.info("429 from %s; delay now %.1fs", slot_key, slot.delay)

        retry = get_retry_request(
            request,
            spider=spider,
            reason="429",
            max_retry_times=self.retry_times,
        )
        return retry or response


def _parse_retry_after(value):
    if not value:
        return None
    try:
        return float(value.decode() if isinstance(value, bytes) else value)
    except ValueError:
        return None
