import json
import os
import time
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests


STORE_URL = "https://shop.travisscott.com/"
STATE_FILE = "seen_products.json"
NO_CHANGE_INTERVAL = 15 * 60  # 15分（秒）


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

    return list(dict.fromkeys(
        urljoin(STORE_URL, link) for link in parser.links
    ))


def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 以前の形式（商品リンクのリスト）にも対応
    if isinstance(data, list):
        return {
            "products": data,
            "last_no_change_notice": time.time(),
        }

    return data


def save_state(products, last_no_change_notice):
    state = {
        "products": products,
        "last_no_change_notice": last_no_change_notice,
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def send_discord_notification(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set")

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=20,
    )
    response.raise_for_status()


def main():
    now = time.time()
    products = get_products()
    state = load_state()

    print("Product links found:", len(products))

    # 初回は現在の商品を基準として保存する
    if state is None:
        save_state(products, now)
        print("初回実行：現在の商品リンクを保存しました。")
        return

    seen_products = state["products"]
    last_notice = state.get("last_no_change_notice", now)

    new_products = [
        product for product in products
        if product not in seen_products
    ]

    if new_products:
        message = "🆕 **Cactus Jack: 新商品リンクを検知**\n"
        message += "\n".join(new_products)

        send_discord_notification(message)
        print("新商品をDiscordに通知しました。")

        # 新商品通知後、変化なし通知の15分間隔もリセット
        last_notice = now

    elif now - last_notice >= NO_CHANGE_INTERVAL:
        message = (
            "監視中：新しい商品リンクはありません。"
            f" 現在{len(products)}件です。"
        )

        send_discord_notification(message)
        print("変化なしの通知をDiscordに送信しました。")

        last_notice = now

    else:
        remaining = int(NO_CHANGE_INTERVAL - (now - last_notice))
        print(f"変化なし。次の通知まで約{remaining}秒です。")

    save_state(products, last_notice)


if __name__ == "__main__":
    main()
