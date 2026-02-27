import csv
import time
import pandas as pd
from playwright.sync_api import sync_playwright


INPUT_CSV = "blinkit_categories.csv"
OUTPUT_CSV = "blinkit_items.csv"
OUTPUT_XLSX = "blinkit_items.xlsx"


def handle_location_popup(page):
    try:
        btn = page.locator("text=Detect my location")
        if btn.is_visible(timeout=4000):
            print("📍 Detecting location...")
            btn.click()
            time.sleep(5)
    except:
        pass


def safe_text(parent, selector):
    loc = parent.locator(selector)
    if loc.count() == 0:
        return ""
    return loc.first.text_content().strip()


def scrape_category(page, category, url):
    print(f"\n📂 Category: {category}")
    print(f"🌐 URL: {url}")

    page.goto(url, timeout=60000)
    handle_location_popup(page)

    page.wait_for_selector("#plpContainer", timeout=60000)
    time.sleep(2)

    container = page.locator("#plpContainer")
    blocks = container.locator("div[class*='tw-px-3']")
    count = blocks.count()

    print(f"🧱 Found {count} products")

    rows = []

    for i in range(count):
        block = blocks.nth(i)

        name = safe_text(
            block,
            "div.tw-text-300.tw-font-semibold"
        )

        description = safe_text(
            block,
            "div.tw-text-200.tw-font-medium"
        )

        price = safe_text(
            block,
            "div.tw-text-200.tw-font-semibold"
        )

        if not name or not price:
            continue

        rows.append({
            "category": category,
            "item": name,
            "description": description,
            "price": price,
            "category_url": url
        })

    return rows


def main():
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            geolocation={"latitude": 20.2806667, "longitude": 85.8246389},
            permissions=["geolocation"]
        )
        page = context.new_page()

        with open(INPUT_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)

            for row in reader:
                if len(row) < 2:
                    continue

                category, link = row[0].strip(), row[1].strip()

                if not link.startswith("https"):
                    print(f"⏭ Skipping invalid link for {category}")
                    continue

                try:
                    rows = scrape_category(page, category, link)
                    all_rows.extend(rows)
                except Exception as e:
                    print(f"⚠️ Failed category {category}: {e}")

        print("\n⏸ Browser left open. Press ENTER to finish export.")
        input()

    # Export
    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    print("\n✅ Export complete")
    print(f"📁 {OUTPUT_CSV}")
    print(f"📁 {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
