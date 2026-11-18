---
name: nemr-web-intel-os
description: Autonomous stealth web crawling, HTML DOM distillation, price & metadata mining, and structured JSON/SQL extraction engine. Use when the user asks to scrape websites, extract clean data from web pages, mine pricing/catalog data, or export HTML to MySQL.
---

# Nemr Web Intel OS (محرك جمع البيانات والـ Scraping الذكي)

Autonomous stealth web mining, DOM boilerplate stripping, and structured JSON/SQL extraction engine.

## Key Capabilities

1. **Stealth Crawler (`crawl`)**:
   - Browser header mimicry, User-Agent rotation, and exponential retry backoff.
2. **DOM Boilerplate Cleaner (`clean`)**:
   - Strips `<script>`, `<style>`, `<nav>`, `<footer>`, and `<noscript>`.
   - Isolates article titles, meta descriptions, headings, outbound URLs, and pricing values (`$`, `EGP`, `SAR`, `EUR`).
3. **Structured Exporter**:
   - Exports directly to clean JSON or sanitized MySQL `INSERT INTO` statements ready for database ingestion.

## CLI Quick Reference

```bash
# 1. Crawl Webpage & Export Structured JSON
python cli.py crawl https://example.com --out data.json

# 2. Crawl & Export Directly to MySQL
python cli.py crawl https://example.com --out articles.sql

# 3. Clean & Extract Data from Local HTML File
python cli.py clean saved_page.html
```
