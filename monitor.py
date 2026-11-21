import requests
from bs4 import BeautifulSoup

url = "https://shop.travisscott.com/"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.get_text(strip=True) if soup.title else "なし")

products = soup.select('a[href*="/products/"]')
print("Product links found:", len(products))

for link in products[:30]:
    name = link.get_text(" ", strip=True)
    href = link.get("href", "")
    print(name, href)
