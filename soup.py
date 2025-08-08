import json, csv, re, time, os, argparse, asyncio, datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

PHONE_RE = re.compile(r'(?:\+1[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})')

def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def load_json(path, default=None):
    if not Path(path).exists():
        return default if default is not None else []
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_stores(path="stores.json"):
    return load_json(path, default=[])

def from_json_ld(html):
    soup = BeautifulSoup(html, "html.parser")
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        def scan(obj):
            if isinstance(obj, dict):
                # common keys
                for k in ("telephone", "phone"):
                    if k in obj and isinstance(obj[k], str):
                        m = PHONE_RE.search(obj[k])
                        if m: return m.group(0)
                # nested
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

def normalize_phone(s):
    if not s: return None
    m = PHONE_RE.search(s)
    return m.group(0) if m else None

async def scrape_phone(page, url):
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    # 1) tel: links
    try:
        tel = await page.eval_on_selector('a[href^="tel:"]', 'el => el.getAttribute("href")')
        if tel:
            p = normalize_phone(tel.replace("tel:", ""))
            if p: return p
    except Exception:
        pass
    # 2) JSON-LD
    html = await page.content()
    p = from_json_ld(html)
    if p: return p
    # 3) visible text (fallback)
    try:
        text = await page.inner_text("body")
        p = normalize_phone(text)
        if p: return p
    except Exception:
        pass
    return None

def within_max_age(timestamp_iso, max_age_days):
    try:
        ts = datetime.datetime.fromisoformat(timestamp_iso.replace("Z",""))
        age = datetime.datetime.utcnow() - ts
        return age.days <= max_age_days
    except Exception:
        return False

async def main_async(args):
    stores = load_stores(args.stores)
    if args.limit:
        stores = stores[:args.limit]

    # cache from previous numbers.json (optional)
    cache = load_json(args.cache, default=[])
    cache_map = {(c["name"], c["url"]): c for c in cache}

    results, errors = [], []
    print(f"\nscraping {len(stores)} stores… (refresh={args.refresh}, max_age={args.max_age})\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"))
        page = await context.new_page()

        for i, store in enumerate(stores, 1):
            name, url = store.get("name",""), store.get("url","")
            prefilled = store.get("phone")

            # prefer phone already in stores.json (unless refresh)
            if prefilled and not args.refresh:
                phone = normalize_phone(prefilled)
                results.append({"name": name, "url": url, "phone": phone or prefilled, "updated_at": now_iso(), "source": "stores.json"})
                print(f"{i}. {name}\n    {phone or prefilled}  (from stores.json)\n")
                continue

            # check cache age (numbers.json)
            cached = cache_map.get((name, url))
            if cached and not args.refresh and args.max_age is not None:
                if within_max_age(cached.get("updated_at",""), args.max_age):
                    results.append(cached)
                    print(f"{i}. {name}\n    {cached['phone']}  (from cache, fresh)\n")
                    continue

            # scrape
            try:
                phone = await scrape_phone(page, url)
                phone = phone or "Not found"
                rec = {"name": name, "url": url, "phone": phone, "updated_at": now_iso(), "source": "scrape"}
                results.append(rec)
                print(f"{i}. {name}\n    {phone}\n")
            except Exception as e:
                err = f"Error: {e}"
                results.append({"name": name, "url": url, "phone": err, "updated_at": now_iso(), "source": "error"})
                errors.append({"name": name, "url": url, "error": str(e)})
                print(f"{i}. {name}\n    {err}\n")
            time.sleep(0.3)

        await browser.close()

    # save outputs
    save_json(args.cache, results)
    with open(args.csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name","url","phone","updated_at","source"])
        w.writeheader()
        for r in results:
            if r["phone"] not in (None, "Not found") and not str(r["phone"]).startswith("Error"):
                w.writerow(r)

    save_json(args.errors, errors)

    # optional write-back to stores.json
    if args.write_back:
        updated = []
        for s in stores:
            # find latest result for same name+url
            match = next((r for r in results if r["name"] == s["name"] and r["url"] == s["url"]), None)
            if match and not str(match["phone"]).startswith("Error") and match["phone"] != "Not found":
                s = {**s, "phone": match["phone"]}
            updated.append(s)
        save_json(args.stores, updated)
        print(f"wrote phones back to {args.stores}")

    print(f"✅ saved: {args.cache}, {args.csv}, {args.errors}")

def parse_args():
    ap = argparse.ArgumentParser(description="Scrape store phone numbers with caching & refresh controls.")
    ap.add_argument("--stores", default="stores.json", help="input stores file (json)")
    ap.add_argument("--cache", default="numbers.json", help="output/cache json of results")
    ap.add_argument("--csv", default="numbers.csv", help="clean csv output")
    ap.add_argument("--errors", default="errors.json", help="errors output json")
    ap.add_argument("--refresh", action="store_true", help="force re-scrape even if phone exists or cache is fresh")
    ap.add_argument("--max-age", type=int, default=30, help="days to trust cached numbers.json entries (default 30). set to 0 to always consider stale (unless --refresh).")
    ap.add_argument("--write-back", action="store_true", help="write found phones back into stores.json")
    ap.add_argument("--limit", type=int, default=None, help="only process first N stores")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main_async(args))
