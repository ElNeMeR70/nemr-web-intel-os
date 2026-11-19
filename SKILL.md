---
name: nemr-web-intel-os
description: Autonomous stealth web crawler & AI data intelligence OS v3.0.0: gzip/deflate concurrent HTTP crawler, Schema.org JSON-LD & table extractor, LLM-ready Markdown distiller, namespaced sitemap.xml parser, heading-aware overlapping RAG JSONL chunker, tech stack fingerprinter & contact/social miner, and SQLite price/content diff monitor. Use when scraping websites, chunking docs for RAG, parsing sitemaps, profiling site tech stacks, or monitoring price changes.
---

# Nemr Web Intel OS v3.0.0 (محرك جمع البيانات والـ RAG وبصمة المواقع)

Autonomous gzip/deflate stealth crawler, LLM Markdown distiller, namespaced Sitemap XML parser, heading-aware RAG JSONL chunker, tech-stack & contact miner, and SQLite change monitor.

## Key Capabilities

1. **Sitemap XML Parser & Heading-Aware RAG Chunker (`parse-sitemap`, `rag-chunks`)**:
   - Parses `<urlset>`/`<sitemapindex>` XML cleanly across namespaces; splits HTML/Markdown by `#`/`##`/`###` headings with configurable overlap, SHA-256 `chunk_id`, `heading_path`, and token estimates for vector DBs.
2. **Tech Stack Fingerprinter & Contact Miner (`tech-profile`)**:
   - Detects CMS/frameworks/CDNs/gateways (WordPress, Next.js, Laravel, Cloudflare, LiteSpeed, Stripe, Paymob) from DOM + HTTP headers, and extracts verified business emails (filtering retina `.png`/`.jpg` false positives), phones, and social URLs.
3. **Stealth & Concurrent Crawler (`crawl`)**:
   - Transparently decodes `gzip`/`deflate`, respects `robots.txt`, and supports `ThreadPoolExecutor` batch crawls.
4. **Markdown Distillation, Polyglot Export & Diff Monitor (`to-markdown`, `clean`, `monitor`)**:
   - Extracts JSON-LD, OpenGraph, and `<table>` into GFM Markdown, CSV, JSONL, JSON, or MySQL inserts, and tracks price/content diffs in SQLite.

## CLI Quick Reference

```bash
python cli.py --version
python cli.py parse-sitemap https://elnemer-ai.com/sitemap.xml --json
python cli.py rag-chunks docs.html --max-chars 800 --overlap 120 --out chunks.jsonl
python cli.py tech-profile https://apex.elnemer-ai.com --json
python cli.py to-markdown page.html --out article.md
python cli.py monitor page.html --db price_watch.db
```
