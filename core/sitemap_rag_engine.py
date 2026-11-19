"""
Nemr Web Intel OS - Sitemap XML Parser & Heading-Aware RAG Markdown Chunker (v3.0.0)
Parses namespaced sitemap XML trees and splits clean Markdown into token-metered overlapping RAG chunks.
"""

from __future__ import annotations
import hashlib
import re
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


class SitemapRagEngine:
    """Parses XML sitemaps and builds heading-aware, overlap-preserved chunks for RAG pipelines."""

    @staticmethod
    def _local_tag(tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1].lower()
        return tag.lower()

    @classmethod
    def parse_sitemap_xml(cls, xml_text: str) -> List[Dict[str, Optional[str]]]:
        root = ET.fromstring(xml_text.strip())
        entries: List[Dict[str, Optional[str]]] = []

        for elem in root:
            ltag = cls._local_tag(elem.tag)
            if ltag not in ("url", "sitemap"):
                continue
            record: Dict[str, Optional[str]] = {
                "kind": ltag,
                "loc": None,
                "lastmod": None,
                "priority": None,
                "changefreq": None,
            }
            for child in elem:
                ctag = cls._local_tag(child.tag)
                if ctag in record and child.text:
                    record[ctag] = child.text.strip()
            if record["loc"]:
                entries.append(record)

        return entries

    @classmethod
    def chunk_markdown_for_rag(
        cls,
        markdown: str,
        max_chars: int = 1000,
        overlap: int = 150,
        source_url: str = "",
    ) -> List[Dict[str, Any]]:
        if not markdown.strip():
            return []

        max_chars = max(100, max_chars)
        overlap = max(0, min(overlap, max_chars // 2))

        # Group text blocks under active heading hierarchy
        sections: List[Dict[str, str]] = []
        heading_stack: Dict[int, str] = {}
        buf: List[str] = []

        def current_heading_path() -> str:
            return " > ".join(heading_stack[lvl] for lvl in sorted(heading_stack))

        for line in markdown.splitlines():
            h_m = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
            if h_m:
                body_only = [b for b in buf if b.strip() and not re.match(r"^#{1,3}\s+", b.strip())]
                if body_only:
                    sections.append({"heading_path": current_heading_path(), "text": "\n".join(buf).strip()})
                buf = []
                lvl = len(h_m.group(1))
                for k in [k for k in heading_stack if k >= lvl]:
                    del heading_stack[k]
                heading_stack[lvl] = h_m.group(2).strip()
                buf.append(line)
            else:
                buf.append(line)

        if buf:
            sections.append({"heading_path": current_heading_path(), "text": "\n".join(buf).strip()})

        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for sec in sections:
            text = sec["text"]
            if not text:
                continue
            if len(text) <= max_chars:
                cid = hashlib.sha256(f"{source_url}|{chunk_idx}|{text}".encode("utf-8")).hexdigest()[:16]
                chunks.append({
                    "chunk_id": cid,
                    "chunk_index": chunk_idx,
                    "source_url": source_url,
                    "heading_path": sec["heading_path"],
                    "content": text,
                    "char_count": len(text),
                    "est_tokens": max(1, round(len(text) / 4.0)),
                })
                chunk_idx += 1
            else:
                start = 0
                step = max(50, max_chars - overlap)
                while start < len(text):
                    piece = text[start:start + max_chars].strip()
                    if piece:
                        cid = hashlib.sha256(f"{source_url}|{chunk_idx}|{piece}".encode("utf-8")).hexdigest()[:16]
                        chunks.append({
                            "chunk_id": cid,
                            "chunk_index": chunk_idx,
                            "source_url": source_url,
                            "heading_path": sec["heading_path"],
                            "content": piece,
                            "char_count": len(piece),
                            "est_tokens": max(1, round(len(piece) / 4.0)),
                        })
                        chunk_idx += 1
                    if start + max_chars >= len(text):
                        break
                    start += step

        return chunks
