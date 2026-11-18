"""
Nemr Web Intel OS - Structured Data Exporter
Converts extracted web intelligence into JSON, CSV, or MySQL INSERT statements.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List
from core.content_cleaner import ExtractedDocument


class DataExporter:
    """Exports structured data to multiple persistence formats."""

    @classmethod
    def to_json(cls, doc: ExtractedDocument) -> str:
        return json.dumps({
            "title": doc.title,
            "description": doc.description,
            "headings": doc.headings,
            "prices": doc.prices,
            "links_count": len(doc.links),
            "clean_text_sample": doc.clean_text[:500]
        }, indent=2, ensure_ascii=False)

    @classmethod
    def to_mysql_insert(cls, doc: ExtractedDocument, table_name: str = "web_intel_records") -> str:
        safe_title = doc.title.replace("'", "''")
        safe_desc = doc.description.replace("'", "''")
        safe_prices = json.dumps(doc.prices)
        safe_text = doc.clean_text[:1000].replace("'", "''")

        return f"""INSERT INTO `{table_name}` (`title`, `description`, `prices_json`, `content`, `created_at`) 
VALUES ('{safe_title}', '{safe_desc}', '{safe_prices}', '{safe_text}', CURRENT_TIMESTAMP);"""
