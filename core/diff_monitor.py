"""
Nemr Web Intel OS - SQLite Snapshot Diff Monitor (v2.0.0)
Tracks webpage changes over time (content hash, prices, headings) using pure stdlib sqlite3.
"""

from __future__ import annotations
import datetime
import hashlib
import json
import sqlite3
from typing import Any, Dict, List
from core.content_cleaner import ExtractedDocument


class DiffMonitor:
    """Monitors price and content changes across crawls via SQLite snapshots."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS intel_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                title TEXT NOT NULL,
                prices_json TEXT NOT NULL,
                headings_json TEXT NOT NULL,
                captured_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record_and_diff(self, url: str, doc: ExtractedDocument) -> Dict[str, Any]:
        payload_hash = hashlib.sha256(
            f"{doc.title}|{json.dumps(doc.prices, sort_keys=True)}|{doc.clean_text}".encode("utf-8")
        ).hexdigest()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cur = self._conn.execute(
            "SELECT content_hash, prices_json, headings_json, captured_at FROM intel_snapshots WHERE url = ? ORDER BY id DESC LIMIT 1",
            (url,),
        )
        prev = cur.fetchone()

        self._conn.execute(
            "INSERT INTO intel_snapshots (url, content_hash, title, prices_json, headings_json, captured_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                url,
                payload_hash,
                doc.title,
                json.dumps(doc.prices, ensure_ascii=False),
                json.dumps(doc.headings, ensure_ascii=False),
                now_iso,
            ),
        )
        self._conn.commit()

        if prev is None:
            return {
                "is_first_snapshot": True,
                "changed": False,
                "added_prices": [],
                "removed_prices": [],
                "added_headings": [],
                "previous_captured_at": None,
            }

        prev_hash, prev_prices_json, prev_headings_json, prev_ts = prev
        prev_prices = json.loads(prev_prices_json)
        prev_headings = json.loads(prev_headings_json)

        added_prices: List[str] = [p for p in doc.prices if p not in prev_prices]
        removed_prices: List[str] = [p for p in prev_prices if p not in doc.prices]
        added_headings: List[str] = [h for h in doc.headings if h not in prev_headings]

        return {
            "is_first_snapshot": False,
            "changed": prev_hash != payload_hash,
            "added_prices": added_prices,
            "removed_prices": removed_prices,
            "added_headings": added_headings,
            "previous_captured_at": prev_ts,
        }

    def close(self) -> None:
        self._conn.close()
