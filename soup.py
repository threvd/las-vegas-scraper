import json

def load_stores_from_json(path="stores.json"):
    with open(path, "r") as f:
        return json.load(f)

def main():
    stores = load_stores_from_json()
    print(f"\nLoaded {len(stores)} store URLs:\n")
    for i, store in enumerate(stores, start=1):
        print(f"{i}. {store['name']} | {store['url']}")

if __name__ == "__main__":
    main()
