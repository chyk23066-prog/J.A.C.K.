import json
import os
from pathlib import Path

import requests

STORE_URL = "https://shop.travisscott.com"
PRODUCTS_URL = f"{STORE_URL}/products.json?limit=250"
STATE_FILE = Path("seen_products.json")

KEYWORDS = ("gta", "grand theft auto", "air force", "af1")


def notify_discord(message):
    webhook = os.environ["DISCORD_WEBHOOK_URL"]
    response = requests.post(
        webhook,
        json={"content": message},
        timeout=20,
    )
    response.raise_for_status()


def main():
    response = requests.get(
        PRODUCTS_URL,
        headers={"User-Agent": "CactusJackReleaseMonitor/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    products = response.json().get("products", [])

    seen = set()
    if STATE_FILE.exists():
        seen = set(json.loads(STATE_FILE.read_text(encoding="utf-8")))

    matches = []
    for product in products:
        title = product.get("title", "")
        handle = product.get("handle", "")
        searchable = f"{title} {handle}".lower()

        if any(word in searchable for word in KEYWORDS):
            product_url = f"{STORE_URL}/products/{handle}"
            if product_url not in seen:
                matches.append((title, product_url))
                seen.add(product_url)

    if matches:
        message = "Cactus Jack公式ストアで関連商品を検出！\n" + "\n".join(
            f"{title}\n{url}" for title, url in matches
        )
        notify_discord(message)

    STATE_FILE.write_text(
        json.dumps(sorted(seen), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
