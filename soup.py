import json, csv, re, time, asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

PHONE_RE = re.compile(r'(?:\+1[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})')

def load_stores(path="stores.json"):
    with open(path, "r") as f:
        return json.load(f)

def from_json_ld(html):
    """look for phone in schema.org JSON-LD blocks"""
    soup = BeautifulSoup(html, "html.parser")
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        def scan(obj):
            if isinstance(obj, dict):
                # common keys
                for k in ("telephone", "phone", "contactPoint"):
                    if k in obj and isinstance(obj[k], str) and PHONE_RE.search(obj[k]):
                        return PHONE_RE.search(obj[k]).group(0)
                # nested contactPoint arrays
                if "contactPoint" in obj and isinstance(obj["contactPoint"], list):
                    for cp in obj["contactPoint"]:
                        m = scan(cp)
                        if m: return m
                # fallback: scan all string fields
                for v in obj.values():
                    m = scan(v)
                    if m: return m
            elif isinstance(obj, list):
                for it in obj:
                    m = scan(it)
                    if m: return m
            elif isinstance(obj, str):
                m = PHONE_RE.search(obj)
                if m: return m.group(0)
            return None
        m = scan(data)
        if m: return m
    return None

def normalize(phone):
    if not phone: return None
    m = PHONE_RE.search(phone)
    return m.group(0) if m else None

async def scrape_one(page, name, url):
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        return {"name": name, "url": url, "phone": f"Error: {e}"}

    # 1) tel: links
    try:
        tel = await page.eval_on_selector('a[href^="tel:"]', 'el => el.getAttribute("href")')  # first tel:
        if tel:
            phone = normalize(tel.replace("tel:", "").strip())
            if phone:
                return {"name": name, "url": url, "phone": phone}
    except Exception:
        pass

    # 2) visible text
    try:
        html = await page.content()
        # try json-ld first (often on carrier pages)
        phone = from_json_ld(html)
        if not phone:
            text = await page.inner_text("body")
            phone = normalize(text)
        if phone:
            return {"name": name, "url": url, "phone": phone}
    except Exception as e:
        return {"name": name, "url": url, "phone": f"Error: {e}"}

    return {"name": name, "url": url, "phone": "Not found"}

async def main_async():
    stores = load_stores("stores.json")
    results, errors = [], []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"))
        page = await context.new_page()

        print(f"\nscraping {len(stores)} stores for phone numbers…\n")
        for i, store in enumerate(stores, 1):
            print(f"{i}. {store['name']}")
            rec = await scrape_one(page, store["name"], store["url"])
            print(f"    {rec['phone']}\n")
            results.append(rec)
            if isinstance(rec["phone"], str) and rec["phone"].startswith("Error"):
                errors.append({"name": store["name"], "url": store["url"], "error": rec["phone"]})
            # light politeness delay
            time.sleep(0.5)

        await browser.close()

    with open("numbers.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("numbers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "url", "phone"])
        w.writeheader()
        for r in results:
            if r["phone"] not in (None, "Not found") and not str(r["phone"]).startswith("Error"):
                w.writerow(r)

    with open("errors.json", "w") as f:
        json.dump(errors, f, indent=2)

    print("✅ saved: numbers.json, numbers.csv, errors.json")

if __name__ == "__main__":
    asyncio.run(main_async())
