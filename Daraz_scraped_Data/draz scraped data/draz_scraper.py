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
        url="https://www.daraz.pk/catalog/?spm=a2a0e.searchlist.search.2.9f4658b3nBaRtR&q=mobile%20phone&_keyori=ss&from=search_history&sugg=mobile%20phone_0_1"
        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
        
        except Exception as e:
                print(f"Error occurred while navigating to {url}: {e}")
                await browser.close()
                return
        scraped_data=[]
        page_num=1
        while True:
            
            #locating mobile boxes
            boxes_locator=await page.locator("div.Bm3ON").all() # allboxes
            print(f"total mobile boxes found {len(boxes_locator)}")
            for box in boxes_locator[:400]:
                try:
                    title_locator=box.locator("div.RfADt a")
                    title_text=await title_locator.inner_text()
                    product_link=await title_locator.get_attribute("href")
                    #price
                    price_locator=box.locator("div.aBrP0 span.ooOxS")
                    if await price_locator.count()>0:
                        price_val=await price_locator.inner_text()
                    else:
                        price_val="N/A"
                    #discount
                    disc_locator=box.locator("div.WNoq3 span.IcOsH")
                    if await disc_locator.count()>0:
                        disc_val=await disc_locator.inner_text()
                    else:
                        disc_val="N/A"
                    


                    #sold
                    sold_locator = box.locator("div._6uN7R span._1cEkb span").first
                    if await sold_locator.count()>0:
                        sold_text = await sold_locator.inner_text()
                    else:
                        sold_text="N/A"

                    #rating stars
                    rating_locator =  box.locator("div.mdmmT i._9-ogB")
                    if await rating_locator.count()>0:
                        rating_val = await rating_locator.count()
                    else:
                        rating_val="N/A"
                except Exception as e:
                    print(f"Error occurred while locating elements on {url}: {e}")
                    continue
                
                


                scraped_data.append({
                    "title":title_text,
                    "url":product_link,
                    "price":price_val,
                    "discount":disc_val,
                    "sold":sold_text,
                    "rating":rating_val
                })

                #next button
            next_button=page.locator("button.ant-pagination-item-link span.anticon-right")
            if await next_button.count()>0 and await next_button.is_visible():
                print("Next button is present. Proceeding to the next page.")
                await next_button.scroll_into_view_if_needed()
                await next_button.click()
                await page.wait_for_function(f"document.querySelector('div.RfADt a')?.innerText!==`{title_text}`",timeout=10000)
                await page.wait_for_load_state("networkidle")
                wait_time=random.randint(1,3)
            
                print(f"Waiting for {wait_time} seconds before clicking the next button....")
                await asyncio.sleep(wait_time)
                print(f"scraping page number:{page_num}")
                if(page_num<=20-1):
                    page_num+=1
                else:
                    break
            else:
                print("Next button not present. Stopping scraping.")
                break   


        #writing data to csv file
    with open("mobile.csv","w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=[ 
                    "title",
                    "url",
                    "price",
                    "discount",
                    "sold",
                    "rating"])
        writer.writeheader()
        writer.writerows(scraped_data)
        print(f"Scraped data written to laptops.csv. Total laptops scraped: {len(scraped_data)}")







    await browser.close()

asyncio.run(main())



