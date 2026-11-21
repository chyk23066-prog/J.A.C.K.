import requests

url = "https://shop.travisscott.com/"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
)

print("Status:", response.status_code)
print("Final URL:", response.url)
print("Page title:", response.text[:300])
response.raise_for_status()
