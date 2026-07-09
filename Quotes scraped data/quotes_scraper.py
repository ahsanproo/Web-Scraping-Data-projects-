import asyncio
import random
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=False)
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        context=await browser.new_context(user_agent=user_agent)
        page=await context.new_page()
    
        pag_num=1
        while True:
            print(f"scraping page number:{pag_num}")
            url=f"https://quotes.toscrape.com/page/{pag_num}/"

            try:
                await page.goto(url)
            except Exception as e:
                print(f"error ocuured in scrapping data:{e}")
                continue

            quotes_locator=page.locator("div.quote span.text")
            all_quotes=await quotes_locator.all_inner_texts()
            author_locator=page.locator("div.quote small.author")
            all_author=await author_locator.all_inner_texts()

            for quote,author in zip(all_quotes[:2],all_author[:2]):
                print(f"---quote:{quote} ---author:{author}")
            
            next_button=page.locator("li.next a")
            if await next_button.count()>0:
                print("next button is present")
                wait_time=random.randint(1,3)*1000
                print(f"waiting for {wait_time} milliseconds before clicking next button")
                await page.wait_for_timeout(wait_time)
                await next_button.click()
                pag_num+=1
            else:
                print("next button not present stop scraping")
                break
    
    await browser.close()

asyncio.run(main())