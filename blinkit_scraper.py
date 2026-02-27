from playwright.sync_api import sync_playwright, TimeoutError
import pandas as pd
import time
from urllib.parse import urljoin

BASE_URL = "https://www.blinkit.com"
URL = "https://www.blinkit.com/categories"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        geolocation={"latitude": 20.2806667, "longitude": 85.8246389}
    )
    context.grant_permissions(["geolocation"])

    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)

    # Handle location popup if it appears
    try:
        page.click("text=Detect my location", timeout=8000)
        time.sleep(5)
    except TimeoutError:
        pass

    # Let React render
    time.sleep(6)

    # Extract links + layout info
    raw_links = page.evaluate("""
        () => {
            return Array.from(document.querySelectorAll("a"))
                .map(a => {
                    const rect = a.getBoundingClientRect();
                    const inHeader = !!a.closest("header, nav, [role='navigation']");
                    return {
                        text: a.textContent.replace(/\\s+/g, ' ').trim(),
                        href: a.getAttribute("href"),
                        y: rect.top,
                        inHeader: inHeader
                    };
                });
        }
    """)

    browser.close()

# Post-filtering
seen = set()
data = []

for item in raw_links:
    text = item["text"]
    href = item["href"]
    y = item["y"]
    in_header = item["inHeader"]

    if not text or len(text) < 4:
        continue

    if not href:
        continue

    # ❌ Exclude navbar / header links
    if in_header:
        continue

    # ❌ Exclude very top-of-page links (navbar area)
    if y < 200:
        continue

    full_url = urljoin(BASE_URL, href)
    key = (text, full_url)

    if key not in seen:
        seen.add(key)
        data.append(key)

print(f"✅ Found {len(data)} category links (navbar excluded)")

# Save output
df = pd.DataFrame(data, columns=["Category", "Link"])
df.to_csv("blinkit_categories.csv", index=False)
df.to_excel("blinkit_categories.xlsx", index=False)

print("📁 Files saved:")
print(" - blinkit_categories.csv")
print(" - blinkit_categories.xlsx")
