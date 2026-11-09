"""HTTPS download handler backed by urllib instead of Twisted's TLS client.

Shopify's edge rate-limits Scrapy 2.6's Twisted/pyOpenSSL client almost
immediately (HTTP 429 on the first request) while curl or Python's own
ssl module get 200 from the same IP. Fetching through urllib in a thread
keeps the rest of Scrapy (throttling, retries, middlewares) unchanged.
"""
import socket
import urllib.error
import urllib.request

from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from twisted.internet.threads import deferToThread


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # Let Scrapy's RedirectMiddleware see 3xx responses.
    def redirect_request(self, *args, **kwargs):
        return None


class UrllibDownloadHandler:
    lazy = False

    def __init__(self, settings, crawler=None):
        self.timeout = settings.getfloat("DOWNLOAD_TIMEOUT", 180)
        self.opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler)

    def download_request(self, request, spider):
        return deferToThread(self._fetch, request)

    def _fetch(self, request):
        headers = {
            k.decode(): b", ".join(v).decode("latin-1")
            for k, v in request.headers.items()
        }
        req = urllib.request.Request(
            request.url,
            data=request.body or None,
            headers=headers,
            method=request.method,
        )
        try:
            resp = self.opener.open(req, timeout=self.timeout)
        except urllib.error.HTTPError as err:  # 4xx/5xx/3xx still carry a response
            resp = err
        except socket.timeout as err:
            raise TimeoutError(str(err)) from err
        with resp:
            body = resp.read()
            status = resp.status if hasattr(resp, "status") else resp.code
            raw_headers = Headers()
            for key, value in resp.headers.items():
                raw_headers.appendlist(key, value)
        respcls = responsetypes.from_args(headers=raw_headers, url=request.url, body=body)
        return respcls(
            url=request.url,
            status=status,
            headers=raw_headers,
            body=body,
            request=request,
        )
