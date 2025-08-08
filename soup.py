import json
import requests
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ScraperBot/1.0)"
}

def load_stores_from_json(path="stores.json"):
    with open(path, "r") as f:
        return json.load(f)

def extract_phone_number(text):
    phone_pattern = r'(702[\s\-\.]?\d{3}[\s\-\.]?\d{4}|\(702\)[\s\-\.]?\d{3}[\s\-\.]?\d{4})'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else "Not found"

def main():
    stores = load_stores_from_json()
    results = []

    print(f"\nScraping {len(stores)} stores for phone numbers:\n")

    for i, store in enumerate(stores, start=1):
        url = store['url']
        name = store['name']
        print(f"{i}. {name}")

        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            phone = extract_phone_number(res.text)
        except Exception as e:
            phone = f"Error: {e}"

        print(f"    URL: {url}")
        print(f"    Phone: {phone}\n")

        results.append({
            "name": name,
            "url": url,
            "phone": phone
        })

        time.sleep(1)

    # Save to numbers.json
    with open("numbers.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved results to numbers.json")

if __name__ == "__main__":
    main()
