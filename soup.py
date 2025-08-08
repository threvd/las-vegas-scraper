import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.showmelocal.com/search.aspx?q=cell+phone+stores&c=las+vegas&st=nv&page={}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_store_listings(pages=5):
    store_data = []

    for page in range(1, pages + 1):
        print(f"Scraping page {page}...")
        url = BASE_URL.format(page)
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        listings = soup.select(".store-result")

        for listing in listings:
            name_tag = listing.select_one(".store-name a")
            name = name_tag.get_text(strip=True) if name_tag else "N/A"

            addr_tag = listing.select_one(".store-addr")
            address = addr_tag.get_text(strip=True) if addr_tag else "N/A"

            phone_tag = listing.select_one(".store-phone")
            phone = phone_tag.get_text(strip=True) if phone_tag else "N/A"

            store_data.append({
                "name": name,
                "address": address,
                "phone": phone
            })

        time.sleep(1)  # Be polite and don’t hammer the server

    return store_data

def main():
    results = scrape_store_listings(pages=5)  # ~10 stores per page, so 5 pages ≈ 50 stores

    print(f"\nFound {len(results)} stores:\n")
    for i, store in enumerate(results, start=1):
        print(f"{i}. {store['name']} | {store['address']} | {store['phone']}")

if __name__ == "__main__":
    main()
