import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; scraping script)",
}

def scrape_duckduckgo(query):
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for link in soup.find_all("a", class_="result__url"):
        text = link.get_text()
        results.append(text)

    return results

def extract_phone_numbers(text):
    phone_pattern = r"\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}"
    return re.findall(phone_pattern, text)

def run():
    query = "cell phone store Las Vegas phone number"
    links = scrape_duckduckgo(query)

    found_numbers = set()

    for url in links:
        try:
            page = requests.get("http://" + url, headers=HEADERS, timeout=5)
            phones = extract_phone_numbers(page.text)
            for p in phones:
                found_numbers.add(p)
        except Exception:
            continue

    print(f"\nFound {len(found_numbers)} unique phone numbers:")
    for num in sorted(found_numbers):
        print(num)

if __name__ == "__main__":
    run()

