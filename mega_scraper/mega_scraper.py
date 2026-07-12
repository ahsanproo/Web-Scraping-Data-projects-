import asyncio
import random
import csv
import os
import re
import logging

from playwright.async_api import async_playwright

logging.basicConfig(
    filename="mega_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

CSV_PATH = "laptops.csv"
FIELDNAMES = ["title", "product_url", "new_price", "old_price", "discount", "features"]


def clean_feature_text(text):
    """Sirf leading bullet dash hatao, beech ke hyphens (jese i5-1135G7) rehne do."""
    return re.sub(r"^-\s*", "", text).strip()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        # antibot-security custom user agent
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        url = "https://www.mega.pk/laptop-price-pakistan/"

        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Error occurred while navigating to {url}: {e}")
            logging.error(f"Navigation error: {e}")
            await browser.close()
            return

        page_num = 1

        while True:
            page_data = []
            print(f"scraping page number: {page_num}")

            # locating laptop boxes
            lap_boxes_locator = await page.locator("div.lap_thu_box").all()
            print(f"Total laptop boxes found on page {page_num}: {len(lap_boxes_locator)}")

            if not lap_boxes_locator:
                print("No boxes found on this page. Stopping.")
                break

            # Pehle box ka title save karo -- pagination check ke liye
            # (last box ki bajaye, taake sahi comparison ho)
            first_title_before_click = "N/A"
            try:
                first_title_before_click = await lap_boxes_locator[0].locator(
                    "div#lap_name_div h3 a"
                ).inner_text()
            except Exception:
                pass

            for lap_box in lap_boxes_locator:
                try:
                    title_locator = lap_box.locator("div#lap_name_div h3 a")
                    title_text = await title_locator.inner_text()
                    product_url = await title_locator.get_attribute("href")

                    # price extraction
                    new_price_box = lap_box.locator("div.cat_price")
                    new_price_text = await new_price_box.inner_text()

                    old_price_box = lap_box.locator("div.cat_price div.was")
                    if await old_price_box.count() > 0:
                        old_price_text = await old_price_box.inner_text()
                    else:
                        old_price_text = "N/A"

                    discount_locator = lap_box.locator("div.discount")
                    if await discount_locator.count() > 0:
                        discount_text = await discount_locator.inner_text()
                    else:
                        discount_text = "N/A"

                    # laptop features
                    features_locator = lap_box.locator("ul.detailer li")
                    if await features_locator.count() > 0:
                        all_features = await features_locator.all_inner_texts()
                        cleaned_features = "|".join(
                            clean_feature_text(f) for f in all_features if f.strip()
                        )
                    else:
                        cleaned_features = "N/A"

                except Exception as e:
                    print(f"Error occurred while locating elements on {url}: {e}")
                    logging.error(f"Element error: {e}")
                    continue

                page_data.append({
                    "title": title_text,
                    "product_url": product_url,
                    "new_price": new_price_text,
                    "old_price": old_price_text,
                    "discount": discount_text,
                    "features": cleaned_features,
                })

            print(f"Page {page_num} scraped: {len(page_data)} items")
            logging.info(f"Page {page_num} scraped: {len(page_data)} items")

        
            file_exists = os.path.exists(CSV_PATH)
            with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(page_data)

            print("CSV Saved Successfully")

        
            next_button = page.locator("div.pagination a").filter(has_text="»").first

            has_next = await next_button.count() > 0
            is_disabled = False
            if has_next:
                parent_class = await next_button.evaluate(
                    "el => el.parentElement ? el.parentElement.className : ''"
                )
                is_disabled = "disabled" in (parent_class or "")

            if has_next and not is_disabled:
                is_visible = await next_button.is_visible()
                if is_visible:
                    print("Next button is present. Proceeding to the next page.")
                    try:
                        await next_button.scroll_into_view_if_needed()
                        await next_button.click()

                        # Pehle box ka title change hone ka wait karo (naya page load hua)
                        await page.wait_for_function(
                            f"document.querySelector('div.lap_thu_box div#lap_name_div h3 a')?.innerText !== `{first_title_before_click}`",
                            timeout=10000,
                        )
                        await page.wait_for_load_state("networkidle")

                        wait_time = random.randint(1, 3)
                        print(f"Waiting for {wait_time} seconds before next page...")
                        await asyncio.sleep(wait_time)

                        page_num += 1

                    except Exception as e:
                        print(f"Error clicking next button: {e}")
                        logging.error(f"Next button error: {e}")
                        break
                else:
                    print("Next button not visible. Stopping scraping.")
                    break
            else:
                print("Next button not present or disabled. Stopping scraping.")
                break

        await browser.close()
        print(f"Scraping finished. Data saved incrementally to {CSV_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
