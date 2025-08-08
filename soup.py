import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.chamberofcommerce.com/united-states/nevada/las-vegas/cellular-telephone-service?page={}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_chamber(pages=5):
    stores = []

    for page in range(1, pages + 1):
        print(f"Scraping page {page}...")
        url = BASE_URL.format(page)
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        listings = soup.select(".business-listing")

        for listing in listings:
            name = listing.select_one(".business-listing--title a")
            phone = listing.select_one(".business-listing--phone")
            address = listing.select_one(".business-listing--address")

            stores.append({
                "name": name.get_text(strip=True) if name else "N/A",
                "address": address.get_text(strip=True) if address else "N/A",
                "phone": phone.get_text(strip=True) if phone else "N/A"
            })

        time.sleep(1)  # Be nice to the server

    return stores

def main():
    stores = scrape_chamber(pages=5)

    print(f"\nFound {len(stores)} stores:\n")
    for i, store in enumerate(stores, start=1):
        print(f"{i}. {store['name']} | {store['address']} | {store['phone']}")

if __name__ == "__main__":
    main()
