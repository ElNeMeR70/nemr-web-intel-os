"""
Nemr Web Intel OS - HTML Content & Metadata Extractor
Strips DOM boilerplate and extracts structured text, titles, prices, and tables.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ExtractedDocument:
    title: str = ""
    description: str = ""
    headings: List[str] = field(default_factory=list)
    clean_text: str = ""
    links: List[str] = field(default_factory=list)
    prices: List[str] = field(default_factory=list)


class ContentCleaner:
    """Strips navigation/scripts and isolates meaningful structured text."""

    TAG_SCRIPT_STYLE = re.compile(r"<(script|style|svg|noscript|header|footer|nav)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
    TAG_ALL = re.compile(r"<[^>]+>")
    PRICE_REGEX = re.compile(r"(?:EGP|\$|€|£|SAR|AED|USD)?\s*\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*(?:EGP|\$|€|£|SAR|AED|USD|جنيه|ريال)?\b")

    @classmethod
    def clean_html(cls, html: str) -> ExtractedDocument:
        doc = ExtractedDocument()

        # Title
        t_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
        if t_match:
            doc.title = cls.TAG_ALL.sub("", t_match.group(1)).strip()

        # Meta description
        d_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
        if d_match:
            doc.description = d_match.group(1).strip()

        # Headings (h1, h2)
        for h in re.finditer(r"<h[1-2][^>]*>(.*?)</h[1-2]>", html, re.DOTALL | re.IGNORECASE):
            h_text = cls.TAG_ALL.sub("", h.group(1)).strip()
            if h_text and h_text not in doc.headings:
                doc.headings.append(h_text)

        # Links
        for link in re.finditer(r'<a[^>]*href=["\'](https?://[^"\']+)["\']', html, re.IGNORECASE):
            l_url = link.group(1).strip()
            if l_url not in doc.links:
                doc.links.append(l_url)

        # Strip scripts, styles, navs
        stripped = cls.TAG_SCRIPT_STYLE.sub(" ", html)
        clean_text = cls.TAG_ALL.sub(" ", stripped)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        doc.clean_text = clean_text

        # Extract prices
        found_prices = cls.PRICE_REGEX.findall(clean_text)
        for p in found_prices:
            p_strip = p.strip()
            if any(curr in p_strip for curr in ("$", "€", "£", "EGP", "SAR", "AED", "جنيه", "ريال")) and p_strip not in doc.prices:
                doc.prices.append(p_strip)

        return doc
