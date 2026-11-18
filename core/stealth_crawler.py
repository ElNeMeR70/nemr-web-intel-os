"""
Nemr Web Intel OS - Stealth Crawler
Performs resilient HTTP retrieval with realistic user-agent rotation, backoff, and header mimicry.
"""

from __future__ import annotations
import random
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CrawlResult:
    url: str
    status_code: int
    content: str
    headers: Dict[str, str] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None


class StealthCrawler:
    """Retrieves web pages with realistic browser headers and retry mechanisms."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    @classmethod
    def fetch_url(cls, url: str, max_retries: int = 2, timeout: int = 10) -> CrawlResult:
        headers = {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
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
                    content = raw.decode(charset, errors="ignore")
                    elapsed = time.time() - start_time
                    resp_headers = dict(resp.headers.items())

                    return CrawlResult(
                        url=url,
                        status_code=resp.status,
                        content=content,
                        headers=resp_headers,
                        elapsed_seconds=round(elapsed, 3)
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
