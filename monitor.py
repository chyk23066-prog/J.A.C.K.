import json
import os
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests


STORE_URL = "https://shop.travisscott.com/"
STATE_FILE = "seen_products.json"


class ProductLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        attrs = dict(attrs)
        href = attrs.get("href", "")

        if "/products/" in href:
            self.links.append(href)


def get_products():
    response = requests.get(
        STORE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    response.raise_for_status()

    parser = ProductLinkParser()
    parser.feed(response.text)

    products = list(dict.fromkeys(
        urljoin(STORE_URL, link) for link in parser.links
    ))

    return products


def load_seen_products():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_seen_products(products):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)


def send_discord_notification(new_products):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set")

    message = "🆕 **Cactus Jack: 新商品リンクを検知**\n"
    message += "\n".join(new_products)

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=20,
    )
    response.raise_for_status()


def main():
    products = get_products()
    seen_products = load_seen_products()

    print("Product links found:", len(products))

    # 初回は現在の商品を基準として保存し、通知しない
    if seen_products is None:
        save_seen_products(products)
        print("初回実行：現在の商品リンクを保存しました。通知は送っていません。")
        return

    new_products = [
        product for product in products
        if product not in seen_products
    ]

    if new_products:
        print("New products found:", len(new_products))
        send_discord_notification(new_products)
        print("Discord通知を送信しました。")
    else:
        print("新しい商品リンクはありません。")

    save_seen_products(products)


if __name__ == "__main__":
    main()
