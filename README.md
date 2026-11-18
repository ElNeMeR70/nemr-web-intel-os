# 🕷️ Nemr Web Intel OS (محرك جمع البيانات والـ Scraping الذكي)

Autonomous stealth web crawling, HTML DOM distillation, price & metadata mining, and structured JSON/SQL extraction engine.

## 🚀 Capabilities

- **Stealth HTTP Client**: Bypasses soft anti-bot checks using header mimicry and randomized desktop browser profiles.
- **Content Distiller**: Strips navigational bloat and extracts structured text, headings, meta tags, and prices.
- **Direct Database Export**: Exports directly to MySQL `INSERT INTO` queries or clean JSON.

## 📦 Usage

```bash
python cli.py crawl https://example.com --out output.json
python cli.py clean local_file.html
```

## 🧪 Testing

```bash
python -m unittest discover -s tests
```
