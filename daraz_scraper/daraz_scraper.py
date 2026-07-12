import asyncio
import random
import csv
import os
import logging

from playwright.async_api import async_playwright

logging.basicConfig(
    filename="daraz_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

CSV_PATH = "mobile.csv"
FIELDNAMES = ["title", "url", "price", "discount", "sold", "rating"]


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

        url = (
            "https://www.daraz.pk/catalog/?spm=a2a0e.searchlist.search.2.9f4658b3nBaRtR"
            "&q=mobile%20phone&_keyori=ss&from=search_history&sugg=mobile%20phone_0_1"
        )

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

            # locating mobile boxes
            boxes_locator = await page.locator("div.Bm3ON").all()
            print(f"total mobile boxes found: {len(boxes_locator)}")

            if not boxes_locator:
                print("No boxes found on this page. Stopping.")
                break

            first_title_before_click = "N/A"
            try:
                first_title_before_click = await boxes_locator[0].locator(
                    "div.RfADt a"
                ).inner_text()
            except Exception:
                pass

            for box in boxes_locator:
                try:
                    title_locator = box.locator("div.RfADt a")
                    title_text = await title_locator.inner_text()
                    product_link = await title_locator.get_attribute("href")

                    # price
                    price_locator = box.locator("div.aBrP0 span.ooOxS")
                    if await price_locator.count() > 0:
                        price_val = await price_locator.inner_text()
                    else:
                        price_val = "N/A"

                    # discount
                    disc_locator = box.locator("div.WNoq3 span.IcOsH")
                    if await disc_locator.count() > 0:
                        disc_val = await disc_locator.inner_text()
                    else:
                        disc_val = "N/A"

                    # sold
                    sold_locator = box.locator("div._6uN7R span._1cEkb span").first
                    if await sold_locator.count() > 0:
                        sold_text = await sold_locator.inner_text()
                    else:
                        sold_text = "N/A"

                    # rating stars
                    rating_locator = box.locator("div.mdmmT i._9-ogB")
                    if await rating_locator.count() > 0:
                        rating_val = await rating_locator.count()
                    else:
                        rating_val = "N/A"

                except Exception as e:
                    print(f"Error occurred while locating elements on {url}: {e}")
                    logging.error(f"Element error: {e}")
                    continue

                page_data.append({
                    "title": title_text,
                    "url": product_link,
                    "price": price_val,
                    "discount": disc_val,
                    "sold": sold_text,
                    "rating": rating_val,
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

            
            next_li = page.locator("li.ant-pagination-next")
            next_button = next_li.locator("button")

            has_next = await next_li.count() > 0
            is_disabled = False
            if has_next:
                class_attr = await next_li.get_attribute("class") or ""
                is_disabled = "ant-pagination-disabled" in class_attr

            if has_next and not is_disabled:
                print("Next button is present. Proceeding to the next page.")

                try:
                    await next_button.scroll_into_view_if_needed()
                    await next_button.click()

                   
                    await page.wait_for_function(
                        f"document.querySelector('div.RfADt a')?.innerText !== `{first_title_before_click}`",
                        timeout=10000,
                    )
                    await page.wait_for_load_state("networkidle")

                    wait_time = random.randint(1, 3)
                    print(f"Waiting for {wait_time} seconds before next page...")
                    await asyncio.sleep(wait_time)

                    page_num += 1
                    print(f"Moving to page number: {page_num}")

                except Exception as e:
                    print(f"Error clicking next button: {e}")
                    logging.error(f"Next button error: {e}")
                    break
            else:
                print("Next button not present, disabled, or max pages reached. Stopping.")
                break

        await browser.close()
        print(f"Scraping finished. Data saved incrementally to {CSV_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
