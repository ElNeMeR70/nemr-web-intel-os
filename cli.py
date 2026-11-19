#!/usr/bin/env python3
"""
Nemr Web Intel OS v3.0.0 - Unified CLI (Sovereign Edition)
Gzip/Deflate Stealth Crawler, Schema.org & Table Extractor, LLM Markdown & RAG Chunker,
Sitemap XML Parser, Tech Stack Fingerprinter, Contact Miner, and SQLite Snapshot Diff Monitor.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.stealth_crawler import StealthCrawler
from core.content_cleaner import ContentCleaner
from core.data_exporter import DataExporter
from core.diff_monitor import DiffMonitor
from core.sitemap_rag_engine import SitemapRagEngine
from core.tech_contact_miner import TechContactMiner

VERSION = "3.0.0"


def _read_url_or_file(target: str) -> tuple[str, dict]:
    if target.startswith(("http://", "https://")):
        res = StealthCrawler.fetch_url(target)
        if res.error:
            print(f"❌ Error fetching {target}: {res.error}")
            sys.exit(1)
        return res.content, res.headers
    p = Path(target)
    if not p.exists():
        print(f"Error: File '{target}' not found.")
        sys.exit(1)
    return p.read_text(encoding="utf-8", errors="ignore"), {}


def cmd_crawl(args: argparse.Namespace) -> None:
    res = StealthCrawler.fetch_url(args.url, timeout=args.timeout)
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
    print(f"Tables Parsed: {len(doc.tables)} | JSON-LD Blocks: {len(doc.json_ld)}")
    print(f"Links Discovered: {len(doc.links)} | Token Savings: {doc.token_savings_pct}%")
    print("=" * 60)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = out_path.suffix.lower()
        if suffix == ".json":
            out_path.write_text(DataExporter.to_json(doc), encoding="utf-8")
        elif suffix == ".sql":
            out_path.write_text(DataExporter.to_mysql_insert(doc), encoding="utf-8")
        elif suffix == ".md":
            out_path.write_text(DataExporter.to_markdown(doc), encoding="utf-8")
        elif suffix == ".csv":
            out_path.write_text(DataExporter.to_csv([doc]), encoding="utf-8")
        elif suffix == ".jsonl":
            out_path.write_text(DataExporter.to_jsonl([doc]), encoding="utf-8")
        else:
            out_path.write_text(doc.clean_text, encoding="utf-8")
        print(f"\n✓ Saved structured output to: {out_path}\n")


def cmd_clean(args: argparse.Namespace) -> None:
    source_file = Path(args.file)
    if not source_file.exists():
        print(f"Error: File {source_file} not found.")
        sys.exit(1)

    html = source_file.read_text(encoding="utf-8", errors="ignore")
    doc = ContentCleaner.clean_html(html)

    if args.markdown:
        print(DataExporter.to_markdown(doc))
        return

    print(f"Title: {doc.title}")
    print(f"Headings: {doc.headings}")
    print(f"Detected Prices: {doc.prices}")
    print(f"Token Savings: {doc.token_savings_pct}% ({len(html)} raw -> {len(doc.markdown)} md chars)")
    print(f"\nClean Content Preview ({len(doc.clean_text)} chars):\n{doc.clean_text[:400]}...\n")


def cmd_to_markdown(args: argparse.Namespace) -> None:
    source_file = Path(args.file)
    if not source_file.exists():
        print(f"Error: File {source_file} not found.")
        sys.exit(1)

    html = source_file.read_text(encoding="utf-8", errors="ignore")
    doc = ContentCleaner.clean_html(html)
    md = DataExporter.to_markdown(doc)
    print(f"\n📝 LLM Markdown Distillation: {len(html)} raw bytes -> {len(md)} md chars (Savings: {doc.token_savings_pct}%)\n")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"✓ Saved Markdown to: {out_path}\n")
    else:
        print("=" * 60)
        print(md)
        print("=" * 60 + "\n")


def cmd_monitor(args: argparse.Namespace) -> None:
    html, _ = _read_url_or_file(args.target)
    doc = ContentCleaner.clean_html(html)
    monitor = DiffMonitor(db_path=args.db)
    try:
        diff = monitor.record_and_diff(args.target, doc)
        print(f"\n📡 Snapshot Diff Report for `{args.target}`:\n" + "=" * 60)
        print(json.dumps(diff, indent=2, ensure_ascii=False))
        print("=" * 60 + "\n")
    finally:
        monitor.close()


def cmd_rag_chunks(args: argparse.Namespace) -> None:
    fpath = Path(args.file)
    if not fpath.exists():
        print(f"Error: File '{fpath}' not found.")
        sys.exit(1)

    raw = fpath.read_text(encoding="utf-8", errors="ignore")
    md = raw if fpath.suffix.lower() in (".md", ".markdown") else ContentCleaner.clean_html(raw).markdown
    chunks = SitemapRagEngine.chunk_markdown_for_rag(
        md,
        max_chars=args.max_chars,
        overlap=args.overlap,
        source_url=args.source_url or fpath.name,
    )
    jsonl = "\n".join(json.dumps(c, ensure_ascii=False) for c in chunks)
    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(jsonl, encoding="utf-8")
        print(f"\n✓ Exported {len(chunks)} RAG chunk(s) to: {out_p}\n")
    else:
        print(jsonl)


def cmd_tech_profile(args: argparse.Namespace) -> None:
    html, hdrs = _read_url_or_file(args.target)
    report = TechContactMiner.analyze(html, headers=hdrs)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    print(f"\n🛰️ Tech Stack & Contact Intelligence for `{args.target}`:\n" + "=" * 60)
    print(f"Tech Stack: {report['tech_stack']}")
    print(f"Emails:     {report['emails']}")
    print(f"Phones:     {report['phones']}")
    print(f"Socials:    {report['socials']}")
    print("=" * 60 + "\n")


def cmd_parse_sitemap(args: argparse.Namespace) -> None:
    xml_text, _ = _read_url_or_file(args.target)
    entries = SitemapRagEngine.parse_sitemap_xml(xml_text)
    if args.json:
        print(json.dumps(entries, indent=2, ensure_ascii=False))
        return
    print(f"\n🗺️ Parsed {len(entries)} URLs/Sitemaps:\n")
    for e in entries[:50]:
        print(f"  [{e['kind']}] {e['loc']} (lastmod={e['lastmod']})")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Nemr Web Intel OS v3.0.0: Stealth Crawler, RAG & Tech Miner")
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_crawl = subparsers.add_parser("crawl", help="Crawl URL and extract structured data")
    p_crawl.add_argument("url", type=str, help="Target URL")
    p_crawl.add_argument("--timeout", type=int, default=10, help="Timeout in seconds")
    p_crawl.add_argument("--out", type=str, default=None, help="Output file (.json, .sql, .md, .csv, .jsonl, .txt)")
    p_crawl.set_defaults(func=cmd_crawl)

    p_clean = subparsers.add_parser("clean", help="Distill clean content from local HTML file")
    p_clean.add_argument("file", type=str, help="HTML file path")
    p_clean.add_argument("--markdown", action="store_true", help="Output distilled Markdown with frontmatter")
    p_clean.set_defaults(func=cmd_clean)

    p_md = subparsers.add_parser("to-markdown", help="Convert local HTML to LLM Markdown and show token savings")
    p_md.add_argument("file", type=str, help="HTML file path")
    p_md.add_argument("--out", type=str, default=None, help="Output .md path")
    p_md.set_defaults(func=cmd_to_markdown)

    p_mon = subparsers.add_parser("monitor", help="Record snapshot & diff against previous crawl")
    p_mon.add_argument("target", type=str, help="URL or local HTML file path")
    p_mon.add_argument("--db", type=str, default="intel_monitor.db", help="SQLite snapshot DB file")
    p_mon.set_defaults(func=cmd_monitor)

    p_rag = subparsers.add_parser("rag-chunks", help="Split HTML or Markdown into overlapping heading-aware RAG JSONL chunks")
    p_rag.add_argument("file", type=str, help="Input .md or .html file")
    p_rag.add_argument("--max-chars", type=int, default=1000, help="Max characters per chunk")
    p_rag.add_argument("--overlap", type=int, default=150, help="Overlap characters")
    p_rag.add_argument("--source-url", type=str, default="", help="Source URL metadata tag")
    p_rag.add_argument("--out", type=str, default=None, help="Output .jsonl file")
    p_rag.set_defaults(func=cmd_rag_chunks)

    p_tech = subparsers.add_parser("tech-profile", help="Fingerprint tech stack and extract contacts/socials")
    p_tech.add_argument("target", type=str, help="URL or local HTML file")
    p_tech.add_argument("--json", action="store_true", help="Emit JSON output")
    p_tech.set_defaults(func=cmd_tech_profile)

    p_map = subparsers.add_parser("parse-sitemap", help="Parse namespaced sitemap.xml URLs")
    p_map.add_argument("target", type=str, help="URL or local XML file")
    p_map.add_argument("--json", action="store_true", help="Emit JSON output")
    p_map.set_defaults(func=cmd_parse_sitemap)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
