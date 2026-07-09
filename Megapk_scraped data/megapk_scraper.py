import asyncio
import random
import csv
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        #antibot-security custom user agent
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        context=await browser.new_context(user_agent=user_agent)
        page=await context.new_page()
        url="https://www.mega.pk/laptop-price-pakistan/"
        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
        except Exception as e:
                print(f"Error occurred while navigating to {url}: {e}")
                
        laptop_data=[]
        page_num=1
        while True:
            # scraping page and its links
            print(f"scraping page number:{page_num}")

            #locating laptop boxes
            lap_boxes_locator=await page.locator("div.lap_thu_box").all() # allboxes
            print(f"Total laptop boxes found on page {page_num}: {len(lap_boxes_locator)}")
            for lap_box in lap_boxes_locator:

                try:
                
                    title_locator=lap_box.locator("div#lap_name_div h3 a") #title
                    title_text=await title_locator.inner_text() #title text
                    product_url=await title_locator.get_attribute("href") #product url

                    #price extraction
                    new_price_box=lap_box.locator("div.cat_price") #new price box
                    new_price_text=await new_price_box.inner_text() #new price text

                    old_price_box=lap_box.locator("div.cat_price div.was") #old price box
                    if await old_price_box.count() > 0:
                        old_price_text=await old_price_box.inner_text() #old price text
                    else:
                        old_price_text="N/A"

                    discount_locator=lap_box.locator("div.discount") #discount box
                    if await discount_locator.count() > 0:
                        discount_text=await discount_locator.inner_text() #discount text
                    else:
                        discount_text="N/A"

                    # laptop features
                    features_locator=lap_box.locator("ul.detailer li") #features box
                    if await features_locator.count() > 0:
                        all_features=await features_locator.all_inner_texts() #all features text
                        cleaned_features= "|".join([f.replace("-","").strip() for f in all_features if f.strip()]) #cleaned features
                    else:
                        cleaned_features="N/A"

                except Exception as e:
                    print(f"Error occurred while locating elements on {url}: {e}")
                    continue

                #  laptop data

                laptop_data.append({
                    "title":title_text,
                    "product_url":product_url,
                    "new_price":new_price_text,
                    "old_price":old_price_text,
                    "discount":discount_text,
                    "features":cleaned_features
                })

                
            next_button=page.locator("div.pagination a").filter(has_text="»").first #next button
            if await next_button.count()>0 and await next_button.is_visible():
                print("Next button is present. Proceeding to the next page.")
                await next_button.scroll_into_view_if_needed()
                await next_button.click()
                await page.wait_for_function(f"document.querySelector('div.lap_thu_box div#lap_name_div h3 a')?.innerText!=='{title_text}'",timeout=10000)
                await page.wait_for_load_state("networkidle")
                wait_time=random.randint(1,3)
                
                print(f"Waiting for {wait_time} seconds before clicking the next button....")
                await asyncio.sleep(wait_time)
                page_num+=1
            else:
                print("Next button not present. Stopping scraping.")
                break   


        #writing data to csv file
    with open("laptops.csv","w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["title","product_url","new_price","old_price","discount","features"])
        writer.writeheader()
        writer.writerows(laptop_data)
        print(f"Scraped data written to laptops.csv. Total laptops scraped: {len(laptop_data)}")
    await browser.close()

asyncio.run(main())



