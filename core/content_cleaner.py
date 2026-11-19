"""
Nemr Web Intel OS - HTML Content, Schema.org JSON-LD, Table & LLM Markdown Extractor (v2.0.0)
Strips DOM boilerplate, extracts JSON-LD & OpenGraph metadata, parses tables, and outputs clean Markdown.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from html import unescape
import json
import re
from typing import Any, Dict, List


@dataclass
class ExtractedDocument:
    title: str = ""
    description: str = ""
    headings: List[str] = field(default_factory=list)
    clean_text: str = ""
    links: List[str] = field(default_factory=list)
    prices: List[str] = field(default_factory=list)
    json_ld: List[Dict[str, Any]] = field(default_factory=list)
    meta_tags: Dict[str, str] = field(default_factory=dict)
    tables: List[List[List[str]]] = field(default_factory=list)
    markdown: str = ""
    token_savings_pct: float = 0.0


class ContentCleaner:
    """Distills noisy HTML into structured JSON-LD, tables, prices, and LLM-ready Markdown."""

    TAG_SCRIPT_STYLE = re.compile(r"<(script|style|svg|noscript|header|footer|nav)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
    JSON_LD_RE = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
    TAG_ALL = re.compile(r"<[^>]+>")
    PRICE_REGEX = re.compile(r"(?:EGP|\$|€|£|SAR|AED|USD)?\s*\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*(?:EGP|\$|€|£|SAR|AED|USD|جنيه|ريال)?\b")

    @classmethod
    def _extract_tables(cls, html: str) -> List[List[List[str]]]:
        tables: List[List[List[str]]] = []
        for tbl_m in re.finditer(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.IGNORECASE):
            rows: List[List[str]] = []
            for tr_m in re.finditer(r"<tr[^>]*>(.*?)</tr>", tbl_m.group(1), re.DOTALL | re.IGNORECASE):
                cells = []
                for cell_m in re.finditer(r"<(?:th|td)[^>]*>(.*?)</(?:th|td)>", tr_m.group(1), re.DOTALL | re.IGNORECASE):
                    txt = unescape(cls.TAG_ALL.sub("", cell_m.group(1)))
                    txt = re.sub(r"\s+", " ", txt).strip()
                    cells.append(txt)
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables

    @classmethod
    def _to_markdown(cls, body_html: str, tables: List[List[List[str]]]) -> str:
        md = body_html
        # Replace links with Markdown syntax
        md = re.sub(
            r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            lambda m: f"[{cls.TAG_ALL.sub('', m.group(2)).strip()}]({m.group(1).strip()})",
            md,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Replace headings h1-h3
        for level in (1, 2, 3):
            hashes = "#" * level
            md = re.sub(
                rf"<h{level}[^>]*>(.*?)</h{level}>",
                lambda m, h=hashes: f"\n\n{h} {re.sub(r'\s+', ' ', cls.TAG_ALL.sub('', m.group(1))).strip()}\n",
                md,
                flags=re.DOTALL | re.IGNORECASE,
            )
        # List items & paragraphs
        md = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: f"\n- {re.sub(r'\s+', ' ', cls.TAG_ALL.sub('', m.group(1))).strip()}", md, flags=re.DOTALL | re.IGNORECASE)
        md = re.sub(r"<p[^>]*>(.*?)</p>", lambda m: f"\n\n{re.sub(r'\s+', ' ', cls.TAG_ALL.sub('', m.group(1))).strip()}\n", md, flags=re.DOTALL | re.IGNORECASE)

        # Strip tables from prose (we append clean GFM tables below)
        md = re.sub(r"<table[^>]*>.*?</table>", "\n", md, flags=re.DOTALL | re.IGNORECASE)
        md = cls.TAG_ALL.sub(" ", md)
        md = unescape(md)

        # Normalize blank lines & spaces per line
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in md.splitlines()]
        compact_lines: List[str] = []
        prev_blank = False
        for ln in lines:
            if not ln:
                if not prev_blank and compact_lines:
                    compact_lines.append("")
                prev_blank = True
            else:
                compact_lines.append(ln)
                prev_blank = False

        # Append formatted GFM tables
        for tbl in tables:
            if not tbl:
                continue
            compact_lines.append("")
            header = tbl[0]
            compact_lines.append("| " + " | ".join(header) + " |")
            compact_lines.append("| " + " | ".join("---" for _ in header) + " |")
            for row in tbl[1:]:
                padded = row + [""] * max(0, len(header) - len(row))
                compact_lines.append("| " + " | ".join(padded[:len(header)]) + " |")

        return "\n".join(compact_lines).strip()

    @classmethod
    def clean_html(cls, html: str) -> ExtractedDocument:
        doc = ExtractedDocument()

        # 1. Extract Schema.org JSON-LD BEFORE stripping <script>
        for jm in cls.JSON_LD_RE.finditer(html):
            raw_json = jm.group(1).strip()
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, dict):
                    doc.json_ld.append(parsed)
                elif isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict):
                            doc.json_ld.append(item)
            except json.JSONDecodeError:
                continue

        # 2. Title & meta tags (description, og:*, twitter:*, canonical)
        t_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
        if t_match:
            doc.title = unescape(cls.TAG_ALL.sub("", t_match.group(1))).strip()

        d_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
        if d_match:
            doc.description = unescape(d_match.group(1)).strip()

        for m in re.finditer(
            r'<meta[^>]+(?:property|name)=["\']((?:og|twitter):[^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
            html,
            re.IGNORECASE,
        ):
            doc.meta_tags[m.group(1).lower()] = unescape(m.group(2)).strip()

        canon_m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if canon_m:
            doc.meta_tags["canonical"] = canon_m.group(1).strip()

        # 3. Headings (h1, h2)
        for h in re.finditer(r"<h[1-2][^>]*>(.*?)</h[1-2]>", html, re.DOTALL | re.IGNORECASE):
            h_text = unescape(cls.TAG_ALL.sub("", h.group(1))).strip()
            if h_text and h_text not in doc.headings:
                doc.headings.append(h_text)

        # 4. Outbound links
        for link in re.finditer(r'<a[^>]*href=["\'](https?://[^"\']+)["\']', html, re.IGNORECASE):
            l_url = link.group(1).strip()
            if l_url not in doc.links:
                doc.links.append(l_url)

        # 5. Strip boilerplate before tables/prose/markdown
        stripped = cls.TAG_SCRIPT_STYLE.sub(" ", html)
        doc.tables = cls._extract_tables(stripped)
        doc.markdown = cls._to_markdown(stripped, doc.tables)

        clean_text = unescape(cls.TAG_ALL.sub(" ", stripped))
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        doc.clean_text = clean_text

        raw_len = max(len(html), 1)
        savings = (1.0 - (len(doc.markdown) / raw_len)) * 100.0
        doc.token_savings_pct = round(max(0.0, savings), 1)

        # 6. Extract prices
        found_prices = cls.PRICE_REGEX.findall(clean_text)
        for p in found_prices:
            p_strip = p.strip()
            if any(curr in p_strip for curr in ("$", "€", "£", "EGP", "SAR", "AED", "جنيه", "ريال")) and p_strip not in doc.prices:
                doc.prices.append(p_strip)

        return doc
