#!/usr/bin/env python3
"""Unit tests for Nemr Web Intel OS."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.content_cleaner import ContentCleaner
from core.data_exporter import DataExporter


class TestWebIntel(unittest.TestCase):
    def setUp(self):
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nemr Store - High Performance AI</title>
          <meta name="description" content="Autonomous AI products and software">
          <script>console.log('tracker');</script>
          <style>body { color: red; }</style>
        </head>
        <body>
          <nav><a href="/home">Home</a></nav>
          <h1>Enterprise AI Subscription</h1>
          <h2>Pricing Details</h2>
          <p>The annual license costs $499 or 25,000 EGP per year.</p>
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


if __name__ == "__main__":
    unittest.main()
