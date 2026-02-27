from playwright.sync_api import sync_playwright
import pandas as pd
from categoryScrapper import scrape_category_page

rows = []
all_products = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # ================= STEP 1 =================
    print("Opening Jiomart...")
    page.goto("https://www.jiomart.com/all-category", timeout=120000)
    page.wait_for_load_state("networkidle")

    print("Waiting for location to be set (manual click allowed)...")
    page.wait_for_selector(".cat-tab-heading", timeout=60000)
    print("Location confirmed. Categories loaded.")

    categories = page.locator(".cat-tab-heading")
    print(f"Found {categories.count()} categories")

    for i in range(categories.count()):
        categories = page.locator(".cat-tab-heading")
        cat_el = categories.nth(i)

        try:
            category = cat_el.inner_text().strip()
        except:
            continue

        print(f"\nCategory: {category}")

        page.evaluate("window.scrollBy(0, 300)")
        page.wait_for_timeout(500)

        try:
            cat_el.click(timeout=5000)
        except:
            continue

        page.wait_for_timeout(1500)

        subcats = page.locator(".jm-list-content.jm-ml-s")
        print(f"  Sub-categories: {subcats.count()}")

        for j in range(subcats.count()):
            subcats = page.locator(".jm-list-content.jm-ml-s")
            sub_el = subcats.nth(j)

            try:
                if not sub_el.evaluate("e => e.offsetHeight > 0"):
                    continue
                sub_category = sub_el.inner_text().strip()
            except:
                continue

            print(f"   ▶ Sub-category: {sub_category}")

            try:
                sub_el.click(force=True, timeout=3000)
                page.wait_for_timeout(1200)
            except:
                continue

            visible_items = page.locator(
                "div.jm-body-xs.jm-fc-primary-grey-80"
            ).evaluate_all("""
                els => els
                    .filter(e => e.offsetHeight > 0)
                    .map(e => ({
                        name: e.innerText.trim(),
                        link: e.closest('a')?.href
                    }))
                    .filter(x => x.name && x.link)
            """)

            print(f"      ✅ Items found: {len(visible_items)}")

            for item in visible_items:
                rows.append((
                    category,
                    sub_category,
                    item["name"],
                    item["link"]
                ))

            # close accordion
            try:
                sub_el.click(force=True)
                page.wait_for_timeout(600)
            except:
                pass

    # ================= SAVE STEP 1 =================
    df_links = pd.DataFrame(
        rows,
        columns=["category", "sub_category", "item", "link"]
    )
    df_links.to_csv("jiomart_categories.csv", index=False)
    print("\n✅ Step 1 completed")

    # ================= STEP 2 =================
    print("\n🚀 Starting Step 2: Product scraping")

    for _, row in df_links.iterrows():
        try:
            products = scrape_category_page(
                context,
                row["category"],
                row["sub_category"],
                row["item"],
                row["link"]
            )
            all_products.extend(products)
        except Exception as e:
            print(f"❌ Failed for {row['item']}: {e}")

    # ================= SAVE FINAL =================
    df_out = pd.DataFrame(
        all_products,
        columns=["category", "sub_category", "item", "itemName", "price"]
    )
    df_out.to_csv("jiomart_products.csv", index=False)
    df_out.to_excel("jiomart_products.xlsx", index=False)

    print("\n✅ Step 2 completed")
    print(f"Total products scraped: {len(df_out)}")

    browser.close()
