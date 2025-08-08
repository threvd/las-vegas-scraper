import json
import csv
import requests
import re
import time
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ScraperBot/1.0)"
}

def load_stores(path="stores.json"):
    with open(path, "r") as f:
        return json.load(f)

def extract_phone_regex(text):
    phone_pattern = r'(702[\s\-\.]?\d{3}[\s\-\.]?\d{4}|\(702\)[\s\-\.]?\d{3}[\s\-\.]?\d{4})'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None

def extract_phone_href(html):
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    for link in links:
        if link["href"].startswith("tel:") and "702" in link["href"]:
            return link["href"].replace("tel:", "").strip()
    return None

def scrape_and_save():
    stores = load_stores()
    results = []
    errors = []

    print(f"\nScraping {len(stores)} stores for phone numbers:\n")

    for i, store in enumerate(stores, start=1):
        print(f"{i}. {store['name']}")
        url = store["url"]

        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()

            phone = extract_phone_href(res.text)
            if not phone:
                phone = extract_phone_regex(res.text)

            phone = phone or "Not found"
        except Exception as e:
            phone = f"Error: {e}"
            errors.append({
                "name": store["name"],
                "url": store["url"],
                "error": str(e)
            })

        print(f"    Phone: {phone}\n")

        results.append({
            "name": store["name"],
            "url": store["url"],
            "phone": phone
        })

        time.sleep(1)

    # Output all results
    with open("numbers.json", "w") as f:
        json.dump(results, f, indent=2)

    # Output only clean phone numbers
    with open("numbers.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "phone"])
        writer.writeheader()
        for row in results:
            if not row["phone"].startswith("Error") and row["phone"] != "Not found":
                writer.writerow(row)

    # Output error list
    with open("errors.json", "w") as f:
        json.dump(errors, f, indent=2)

    print("✅ Saved: numbers.json, numbers.csv, errors.json")

if __name__ == "__main__":
    scrape_and_save()
