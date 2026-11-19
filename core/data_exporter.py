"""
Nemr Web Intel OS - Structured Data Exporter (v2.0.0)
Converts extracted web intelligence into JSON, Markdown with YAML frontmatter, CSV, JSONL, or MySQL INSERT statements.
"""

from __future__ import annotations
import csv
import io
import json
from typing import List
from core.content_cleaner import ExtractedDocument


class DataExporter:
    """Exports structured web intelligence across JSON, Markdown, CSV, JSONL, and MySQL."""

    @classmethod
    def to_json(cls, doc: ExtractedDocument) -> str:
        return json.dumps({
            "title": doc.title,
            "description": doc.description,
            "headings": doc.headings,
            "prices": doc.prices,
            "meta_tags": doc.meta_tags,
            "json_ld": doc.json_ld,
            "tables": doc.tables,
            "links_count": len(doc.links),
            "token_savings_pct": doc.token_savings_pct,
            "clean_text_sample": doc.clean_text[:500],
        }, indent=2, ensure_ascii=False)

    @classmethod
    def to_markdown(cls, doc: ExtractedDocument) -> str:
        frontmatter = [
            "---",
            f"title: {json.dumps(doc.title, ensure_ascii=False)}",
            f"description: {json.dumps(doc.description, ensure_ascii=False)}",
            f"prices: {json.dumps(doc.prices, ensure_ascii=False)}",
            f"token_savings_pct: {doc.token_savings_pct}",
            "---",
            "",
        ]
        return "\n".join(frontmatter) + (doc.markdown or doc.clean_text)

    @classmethod
    def to_csv(cls, docs: List[ExtractedDocument]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["title", "description", "prices", "headings_count", "links_count", "token_savings_pct"])
        for d in docs:
            writer.writerow([
                d.title,
                d.description,
                "; ".join(d.prices),
                len(d.headings),
                len(d.links),
                d.token_savings_pct,
            ])
        return buf.getvalue()

    @classmethod
    def to_jsonl(cls, docs: List[ExtractedDocument]) -> str:
        lines = []
        for d in docs:
            lines.append(
                json.dumps(
                    {
                        "title": d.title,
                        "description": d.description,
                        "prices": d.prices,
                        "headings": d.headings,
                        "markdown": d.markdown,
                        "json_ld": d.json_ld,
                    },
                    ensure_ascii=False,
                )
            )
        return "\n".join(lines)

    @classmethod
    def to_mysql_insert(cls, doc: ExtractedDocument, table_name: str = "web_intel_records") -> str:
        safe_title = doc.title.replace("'", "''")
        safe_desc = doc.description.replace("'", "''")
        safe_prices = json.dumps(doc.prices, ensure_ascii=False).replace("'", "''")
        safe_text = doc.clean_text[:1000].replace("'", "''")

        return f"""INSERT INTO `{table_name}` (`title`, `description`, `prices_json`, `content`, `created_at`) 
VALUES ('{safe_title}', '{safe_desc}', '{safe_prices}', '{safe_text}', CURRENT_TIMESTAMP);"""
