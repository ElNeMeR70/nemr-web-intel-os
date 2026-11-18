#!/usr/bin/env python3
"""
Nemr Web Intel OS - Unified CLI
Stealth Web Scraping, HTML DOM Distillation, and Structured JSON/SQL Export.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.stealth_crawler import StealthCrawler
from core.content_cleaner import ContentCleaner
from core.data_exporter import DataExporter


def cmd_crawl(args: argparse.Namespace) -> None:
    url = args.url
    print(f"\n🕷️ Stealth Crawling: {url}...\n")
    res = StealthCrawler.fetch_url(url, timeout=args.timeout)

    if res.error:
        print(f"❌ Error: {res.error} (Status: {res.status_code})")
        return

    print(f"✓ Status {res.status_code} in {res.elapsed_seconds}s")
    doc = ContentCleaner.clean_html(res.content)

    print("=" * 60)
    print(f"Title: {doc.title}")
    print(f"Description: {doc.description}")
    print(f"Headings: {doc.headings[:5]}")
    print(f"Detected Prices: {doc.prices}")
    print(f"Links Discovered: {len(doc.links)}")
    print("=" * 60)

    if args.out:
        out_path = Path(args.out)
        if out_path.suffix == ".json":
            out_path.write_text(DataExporter.to_json(doc), encoding="utf-8")
        elif out_path.suffix == ".sql":
            out_path.write_text(DataExporter.to_mysql_insert(doc), encoding="utf-8")
        else:
            out_path.write_text(doc.clean_text, encoding="utf-8")
        print(f"\n✓ Saved structured output to: {out_path}\n")


def cmd_clean(args: argparse.Namespace) -> None:
    source_file = Path(args.file)
    if not source_file.exists():
        print(f"Error: File {source_file} not found.")
        sys.exit(1)

    print(f"\n🧹 Distilling Clean Content from: {source_file}...\n")
    html = source_file.read_text(encoding="utf-8", errors="ignore")
    doc = ContentCleaner.clean_html(html)

    print(f"Title: {doc.title}")
    print(f"Headings: {doc.headings}")
    print(f"Detected Prices: {doc.prices}")
    print(f"\nClean Content Preview ({len(doc.clean_text)} chars):\n{doc.clean_text[:400]}...\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Nemr Web Intel OS: Stealth Web Mining & AI Content Distiller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # crawl
    p_crawl = subparsers.add_parser("crawl", help="Crawl URL and extract structured data")
    p_crawl.add_argument("url", type=str, help="Target URL")
    p_crawl.add_argument("--timeout", type=int, default=10, help="Timeout in seconds")
    p_crawl.add_argument("--out", type=str, default=None, help="Output file (.json, .sql, .txt)")
    p_crawl.set_defaults(func=cmd_crawl)

    # clean
    p_clean = subparsers.add_parser("clean", help="Distill clean content from local HTML file")
    p_clean.add_argument("file", type=str, help="HTML file path")
    p_clean.set_defaults(func=cmd_clean)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
