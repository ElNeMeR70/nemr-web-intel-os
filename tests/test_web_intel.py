#!/usr/bin/env python3
"""Unit tests for Nemr Web Intel OS v2.0.0."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.content_cleaner import ContentCleaner
from core.data_exporter import DataExporter
from core.diff_monitor import DiffMonitor
from core.sitemap_rag_engine import SitemapRagEngine
from core.tech_contact_miner import TechContactMiner


class TestWebIntel(unittest.TestCase):
    def setUp(self):
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nemr Store - High Performance AI</title>
          <meta name="description" content="Autonomous AI products and software">
          <meta property="og:title" content="Nemr Store OG">
          <link rel="canonical" href="https://elnemer-ai.com/store">
          <script type="application/ld+json">
          {"@context": "https://schema.org", "@type": "Product", "name": "Nemr Apex", "price": "499"}
          </script>
          <script>console.log('tracker');</script>
          <style>body { color: red; }</style>
        </head>
        <body>
          <nav><a href="/home">Home</a></nav>
          <h1>Enterprise AI Subscription</h1>
          <h2>Pricing Details</h2>
          <p>The annual license costs $499 or 25,000 EGP per year.</p>
          <table>
            <tr><th>Plan</th><th>Price</th></tr>
            <tr><td>Pro</td><td>$499</td></tr>
          </table>
          <a href="https://elnemer-ai.com/buy">Purchase Now</a>
          <footer>Copyright 2026</footer>
        </body>
        </html>
        """

    def test_content_cleaner(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        self.assertEqual(doc.title, "Nemr Store - High Performance AI")
        self.assertEqual(doc.description, "Autonomous AI products and software")
        self.assertIn("Enterprise AI Subscription", doc.headings)
        self.assertIn("https://elnemer-ai.com/buy", doc.links)
        self.assertNotIn("console.log", doc.clean_text)
        self.assertNotIn("body { color: red; }", doc.clean_text)
        self.assertTrue(any("$499" in p for p in doc.prices) or any("25,000 EGP" in p for p in doc.prices))

    def test_data_exporter_json(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        json_str = DataExporter.to_json(doc)
        self.assertIn("Nemr Store", json_str)
        self.assertIn("description", json_str)

    def test_data_exporter_mysql_insert(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        sql = DataExporter.to_mysql_insert(doc, table_name="test_articles")
        self.assertIn("INSERT INTO `test_articles`", sql)
        self.assertIn("Nemr Store", sql)

    # v2.0.0 Tests
    def test_json_ld_and_opengraph_extraction(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        self.assertEqual(len(doc.json_ld), 1)
        self.assertEqual(doc.json_ld[0]["@type"], "Product")
        self.assertEqual(doc.meta_tags.get("og:title"), "Nemr Store OG")
        self.assertEqual(doc.meta_tags.get("canonical"), "https://elnemer-ai.com/store")

    def test_table_parsing(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        self.assertEqual(len(doc.tables), 1)
        self.assertEqual(doc.tables[0], [["Plan", "Price"], ["Pro", "$499"]])

    def test_markdown_and_token_savings(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        self.assertIn("# Enterprise AI Subscription", doc.markdown)
        self.assertIn("| Plan | Price |", doc.markdown)
        self.assertIn("[Purchase Now](https://elnemer-ai.com/buy)", doc.markdown)
        self.assertGreater(doc.token_savings_pct, 0.0)

    def test_export_formats_md_csv_jsonl(self):
        doc = ContentCleaner.clean_html(self.sample_html)
        md = DataExporter.to_markdown(doc)
        self.assertTrue(md.startswith("---\ntitle:"))
        self.assertIn("token_savings_pct:", md)

        csv_out = DataExporter.to_csv([doc])
        self.assertIn("title,description,prices", csv_out)
        self.assertIn("Nemr Store - High Performance AI", csv_out)

        jsonl_out = DataExporter.to_jsonl([doc])
        self.assertEqual(len(jsonl_out.splitlines()), 1)
        self.assertIn('"title": "Nemr Store - High Performance AI"', jsonl_out)

    def test_diff_monitor(self):
        mon = DiffMonitor(db_path=":memory:")
        doc1 = ContentCleaner.clean_html("<html><title>Store</title><body><h1>Laptop</h1><p>$999</p></body></html>")
        first = mon.record_and_diff("https://shop.test/p1", doc1)
        self.assertTrue(first["is_first_snapshot"])
        self.assertFalse(first["changed"])

        doc2 = ContentCleaner.clean_html("<html><title>Store</title><body><h1>Laptop Pro</h1><p>$799</p></body></html>")
        second = mon.record_and_diff("https://shop.test/p1", doc2)
        self.assertFalse(second["is_first_snapshot"])
        self.assertTrue(second["changed"])
        self.assertIn("$799", second["added_prices"])
        self.assertIn("$999", second["removed_prices"])
        self.assertIn("Laptop Pro", second["added_headings"])
        mon.close()

    # v3.0.0 Tests
    def test_sitemap_xml_parser_with_namespace(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://elnemer-ai.com/</loc><lastmod>2026-11-18</lastmod><priority>1.0</priority></url>
          <url><loc>https://elnemer-ai.com/pricing</loc><changefreq>weekly</changefreq></url>
        </urlset>
        """
        entries = SitemapRagEngine.parse_sitemap_xml(xml)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["loc"], "https://elnemer-ai.com/")
        self.assertEqual(entries[0]["lastmod"], "2026-11-18")
        self.assertEqual(entries[1]["changefreq"], "weekly")

    def test_rag_markdown_chunker(self):
        long_para = "Nemr Apex Omni builds resilient AI systems. " * 25
        md = f"# Architecture\n\n## Core Engine\n\n{long_para}\n\n# Security\n\nHardened PHP 8.3.\n"
        chunks = SitemapRagEngine.chunk_markdown_for_rag(md, max_chars=300, overlap=60, source_url="https://docs.test")
        self.assertGreaterEqual(len(chunks), 3)
        self.assertEqual(chunks[0]["heading_path"], "Architecture > Core Engine")
        self.assertEqual(chunks[-1]["heading_path"], "Security")
        self.assertGreater(chunks[0]["est_tokens"], 0)

    def test_tech_stack_fingerprinter(self):
        html = '<script src="https://js.stripe.com/v3/"></script><div data-v-123>__NEXT_DATA__ wp-content/themes/</div>'
        res = TechContactMiner.analyze(html, headers={"Server": "LiteSpeed", "X-Powered-By": "PHP/8.3.36"})
        self.assertIn("Stripe", res["tech_stack"])
        self.assertIn("Next.js", res["tech_stack"])
        self.assertIn("WordPress", res["tech_stack"])
        self.assertIn("LiteSpeed", res["tech_stack"])
        self.assertIn("PHP", res["tech_stack"])

    def test_contact_miner_filters_fake_image_emails(self):
        html = 'Contact sales@elnemer-ai.com or hero@2x.png! Follow https://github.com/ElNeMeR70 and call +201012345678.'
        res = TechContactMiner.analyze(html)
        self.assertIn("sales@elnemer-ai.com", res["emails"])
        self.assertNotIn("hero@2x.png", res["emails"])
        self.assertIn("+201012345678", res["phones"])
        self.assertIn("https://github.com/ElNeMeR70", res["socials"].get("github", []))


if __name__ == "__main__":
    unittest.main()
