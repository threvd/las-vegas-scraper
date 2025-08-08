# Las Vegas Cell Phone Store Scraper

This tool extracts phone numbers from store landing pages for wireless carriers in the Las Vegas metro area. It uses [Playwright](https://playwright.dev/python/) to render each page like a real browser, then attempts to extract phone numbers from:

- `<a href="tel:…">` links  
- visible text  
- structured JSON-LD metadata (`"telephone"` fields)

The script reads from a JSON file of store name + URL pairs (`stores.json`), optionally updates it with found phone numbers, and writes results to:

- `numbers.json` → full scrape result history (with timestamps and sources)  
- `numbers.csv` → clean table of stores + phones  
- `errors.json` → errors during scraping (timeouts, 403s, etc.)

---

## ⚙️ Setup

1. Install dependencies:

```bash
pip3 install playwright bs4
python3 -m playwright install chromium

