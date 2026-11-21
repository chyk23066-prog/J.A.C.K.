import requests
from html.parser import HTMLParser
from urllib.parse import urljoin


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


url = "https://shop.travisscott.com/"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
)
response.raise_for_status()

parser = ProductLinkParser()
parser.feed(response.text)

products = list(dict.fromkeys(
    urljoin(url, link) for link in parser.links
))

print("Status:", response.status_code)
print("Product links found:", len(products))

for product in products[:30]:
    print(product)
