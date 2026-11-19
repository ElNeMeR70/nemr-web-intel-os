"""
Nemr Web Intel OS - Stealth HTTP Crawler, Robots Checker & Concurrent Batch Fetcher (v2.0.0)
Provides gzip/deflate decompression, User-Agent rotation, exponential backoff, robots.txt checking, and parallel batch crawling.
"""

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import gzip
import random
import time
from typing import Dict, List, Optional
import urllib.error
from urllib.parse import urlparse
import urllib.request
import urllib.robotparser
import zlib


@dataclass
class CrawlResult:
    url: str
    status_code: int
    content: str
    headers: Dict[str, str] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None


class StealthCrawler:
    """Retrieves web pages with compressed encoding handling, retry backoff, and parallel workers."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    @classmethod
    def _decode_body(cls, raw: bytes, content_encoding: str, charset: str) -> str:
        enc = (content_encoding or "").lower()
        data = raw
        if "gzip" in enc:
            try:
                data = gzip.decompress(raw)
            except Exception:
                data = raw
        elif "deflate" in enc:
            try:
                data = zlib.decompress(raw)
            except zlib.error:
                try:
                    data = zlib.decompress(raw, -zlib.MAX_WBITS)
                except Exception:
                    data = raw
        return data.decode(charset or "utf-8", errors="ignore")

    @classmethod
    def check_robots_txt(cls, url: str, user_agent: str = "*") -> bool:
        """Checks robots.txt permissions cleanly; gracefully allows if unreachable."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return True
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            return rp.can_fetch(user_agent, url)
        except Exception:
            return True

    @classmethod
    def fetch_url(cls, url: str, max_retries: int = 2, timeout: int = 10) -> CrawlResult:
        headers = {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        }

        req = urllib.request.Request(url, headers=headers)
        start_time = time.time()

        for attempt in range(max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read()
                    charset = resp.headers.get_content_charset() or "utf-8"
                    content_encoding = resp.headers.get("Content-Encoding", "")
                    content = cls._decode_body(raw, content_encoding, charset)
                    elapsed = time.time() - start_time
                    resp_headers = dict(resp.headers.items())

                    return CrawlResult(
                        url=url,
                        status_code=resp.status,
                        content=content,
                        headers=resp_headers,
                        elapsed_seconds=round(elapsed, 3),
                    )
            except urllib.error.HTTPError as e:
                if attempt == max_retries:
                    return CrawlResult(url=url, status_code=e.code, content="", error=str(e))
                time.sleep(1.0 * (attempt + 1))
            except Exception as e:
                if attempt == max_retries:
                    return CrawlResult(url=url, status_code=0, content="", error=str(e))
                time.sleep(1.0 * (attempt + 1))

        return CrawlResult(url=url, status_code=0, content="", error="Unknown failure")

    @classmethod
    def crawl_batch(cls, urls: List[str], max_workers: int = 4, timeout: int = 10) -> List[CrawlResult]:
        """Fetches multiple URLs concurrently using a bounded thread pool."""
        if not urls:
            return []
        workers = max(1, min(max_workers, len(urls)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(lambda u: cls.fetch_url(u, timeout=timeout), urls))
