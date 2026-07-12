import asyncio
import csv
import json
import os
import logging
import random

from playwright.async_api import async_playwright


logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.101 Safari/537.36",

            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.120 Safari/537.36",

            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.113 Safari/537.36",

            # Chrome macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.101 Safari/537.36",

            # Chrome Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.101 Safari/537.36"
]
async def main():
    if os.path.exists("progress.json"):
        with open("progress.json", "r") as f:
            progress = json.load(f)
            page_number = progress.get("page", 1)
    else:
        page_number = 1


    url = f"https://www.zameen.com/Homes/Lahore-1-{page_number}.html"
    async def block_ads(route):
        url = route.request.url

        if (
            route.request.resource_type in ["image", "media", "font"]
            or "doubleclick.net" in url
            or "googlesyndication.com" in url
            or "googleads" in url
        ):
            await route.abort()
        else:
            await route.continue_()

    


    async with async_playwright() as p:
        browser = await p.chromium.launch(
                    headless=False,
                    args=["--start-maximized"]
                )
        user_agent = random.choice(USER_AGENTS)
        print(f"Using User-Agent:\n{user_agent}")
        logging.info(f"Using User-Agent: {user_agent}")
        context = await browser.new_context(
                    no_viewport=True,
                    user_agent=user_agent
                )
        page = await context.new_page()
    
        await page.route("**/*", block_ads)


        # goto url with retry
        success = False
        for attempt in range(3):
            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                print(f"Starting from Page {page_number}")
                print(page.url)

                logging.info(f"Starting from Page {page_number}")
                logging.info(f"Current URL: {page.url}")

                success = True
                break

            except Exception as e:
                print(f"Attempt {attempt + 1} Failed: {e}")
                logging.error(f"Attempt {attempt + 1} Failed: {e}")

                await page.wait_for_timeout(2000)

        if not success:
            print("Failed to open page after 3 attempts.")
            logging.error("Failed to open page after 3 attempts.")
            await browser.close()
            return
        
    
        

        # get text function
        async def get_text(locator):
            try:
                return await locator.inner_text()
            except Exception as e:
                logging.error(f"Text Error: {e}")
                return "N/A"  

        detail_page = await context.new_page()
        await detail_page.route("**/*", block_ads)
        seen_urls = set()
        while True:
            all_properties = []
            print(f"\nScraping Page {page_number}")


            all_listing = await page.locator('li[aria-label="Listing"]').all()
            if not all_listing:
                print("No listings found.")
                break
            
            print(f"total listings :{len(all_listing)}")

            for listing in all_listing:
                link = "N/A"
                
                title = await get_text(
                listing.locator('h2[aria-label="Title"]')
                )

                price = await get_text(
                    listing.locator('span[aria-label="Price"]')
                )

                location = await get_text(
                    listing.locator('div[aria-label="Location"]')
                )

                beds = await get_text(
                    listing.locator('span[aria-label="Beds"]')
                )

                baths = await get_text(
                    listing.locator('span[aria-label="Baths"]')
                )

                area = await get_text(
                    listing.locator('span[aria-label="Area"]')
                )

                property_type = "N/A"
                purpose = "N/A"
                creation_date = "N/A"
            

                try:
                    link = await listing.locator(
                    'a[aria-label="Listing link"]'
                    ).get_attribute("href")

                    if link:
                        link = "https://www.zameen.com" + link

                        if link in seen_urls:
                            continue
                        seen_urls.add(link)

                        #details page
                        await detail_page.goto(
                            link,
                            wait_until="domcontentloaded",
                            timeout=60000
                        )
                    
                    
                        property_type = await get_text(
                        detail_page.locator('span[aria-label="Type"]'))

                        purpose = await get_text(
                        detail_page.locator('span[aria-label="Purpose"]'))

                        creation_date = await get_text(
                        detail_page.locator('span[aria-label="Creation date"]'))
                
                except Exception as e:
                    logging.error(f"Link Error: {e}")
                    

                property_data = {
                "title": title,
                "price": price,
                "location": location,
                "beds": beds,
                "baths": baths,
                "area": area,
                "url":link,
                "property_type": property_type,
                "purpose": purpose,
                "creation_date": creation_date,

                }
                all_properties.append(property_data)

            print(f"Page {page_number} scraped successfully.")
            print(f"successfully scraped data  total scraped data is:{len(all_properties)}")
            logging.info(f"Total scraped data: {len(all_properties)}")


            
    
            file_exists = os.path.exists("zameen_data.csv")
            with open("zameen_data.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["title","price","location","beds","baths","area",
                                "url","property_type","purpose","creation_date"]
                )
                if not file_exists:
                    writer.writeheader()
                writer.writerows(all_properties)

            print("CSV Saved Successfully")

            # Next button locate karo
            next_button = page.locator('a[title="Next"]')
        
            # Check next button
            if await next_button.count() > 0:
                print("Next button found")

                next_url = await next_button.get_attribute("href")
                print(f"Next Page: {next_url}")

                success = False

                for attempt in range(3):
                    try:
                        await next_button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)

                        old_url = page.url

                        await next_button.click()

                        await page.wait_for_url(
                            lambda url: url != old_url,
                            timeout=30000
                        )

                        # Wait for new page
                        await page.wait_for_selector('li[aria-label="Listing"]')
                        await page.wait_for_load_state("domcontentloaded")
                        await page.wait_for_timeout(1000)
                        

                        print(f"Current URL: {page.url}")
                        logging.info(f"Current URL: {page.url}")

                        # Page successfully load ho gaya
                        import re

                        match = re.search(r"Lahore-1-(\d+)\.html", page.url)

                        if match:
                            page_number = int(match.group(1))

                        with open("progress.json", "w") as f:
                            json.dump(
                                {
                                    "page": page_number
                                },
                                f,
                                indent=4
                            )

                        success = True
                        break

                    except Exception as e:
                        print(f"Next Button Attempt {attempt + 1} Failed: {e}")
                        logging.error(f"Next Button Attempt {attempt + 1} Failed: {e}")

                        await page.wait_for_timeout(2000)
            
                
                if not success:
                    print("Next button failed after 3 attempts.")
                    logging.error("Next button failed after 3 attempts.")
                    break
            else:
                print("Last Page Reached")
                logging.info("Last Page Reached")
                break
            


        await page.wait_for_timeout(3000)
        await detail_page.close()
        await browser.close()

asyncio.run(main())