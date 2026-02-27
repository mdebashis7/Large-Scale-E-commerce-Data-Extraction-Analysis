from playwright.sync_api import TimeoutError
import time


def auto_scroll(page, max_idle_rounds=5):
    """
    Scrolls until lazy loading stops.
    Stops when page height does not change for `max_idle_rounds`.
    """
    last_height = page.evaluate("document.body.scrollHeight")
    idle_rounds = 0

    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.2)

        new_height = page.evaluate("document.body.scrollHeight")

        if new_height == last_height:
            idle_rounds += 1
            if idle_rounds >= max_idle_rounds:
                break
        else:
            idle_rounds = 0
            last_height = new_height


def scrape_category_page(context, category, sub_category, item, link):
    page = context.new_page()

    print(f"\n🔗 Opening: {category} → {sub_category} → {item}")
    page.goto(link, timeout=120000)
    page.wait_for_load_state("networkidle")

    # Trigger lazy loading
    auto_scroll(page)

    products = []

    name_locator = page.locator(
        "div.plp-card-details-name.line-clamp.jm-body-xs.jm-fc-primary-grey-80"
    )
    price_locator = page.locator(
        "span.jm-heading-xxs.jm-mb-xxs"
    )

    count = min(name_locator.count(), price_locator.count())
    print(f"   🧾 Products found: {count}")

    for i in range(count):
        try:
            name = name_locator.nth(i).inner_text().strip()
            price = price_locator.nth(i).inner_text().strip()
        except TimeoutError:
            continue

        row = (category, sub_category, item, name, price)
        products.append(row)

        # 🔥 live visibility
        print(f"      ✔ {name} | {price}")

    page.close()
    return products
