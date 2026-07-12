# Mega.pk Laptop Scraper

A Playwright scraper that goes through [mega.pk](https://www.mega.pk/laptop-price-pakistan/)'s laptop listings page and pulls out pricing + spec info for every laptop, page by page, into a CSV.

## What it does

For every laptop box on the page, it grabs:

- Title
- Product URL
- New price (current price)
- Old price (if the item is discounted — otherwise `N/A`)
- Discount percentage (if any)
- Features (RAM, storage, screen size, CPU, etc.) — pulled from the feature list and joined into one `|`-separated string

It writes to `laptops.csv`, appending after every page instead of waiting till the end — so if the script crashes halfway, whatever was scraped up to that point is already saved.

## How pagination is handled

This is the part worth explaining, since it's not the usual "wait for URL to change" approach.

Mega.pk's pagination doesn't change the URL when you click "next" — it's the same page reloading its content. So instead of waiting for a URL change, the script:

1. Grabs the title of the **first** laptop box before clicking next
2. Clicks the next (`»`) button
3. Waits until that first box's title actually changes (`page.wait_for_function`) — this is proof the new page's content has loaded, not just that the click registered
4. Then waits for network to go idle, plus a small random 1–3 second pause (to look less bot-like)

It also checks if the next button is disabled (by checking its parent element's class) or just not visible, and stops scraping if so — that's how it knows it's hit the last page.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Running it

```bash
python mega_scraper.py
```

It opens a visible browser (not headless — mega.pk's layout/behavior is easier to debug this way, and some sites behave differently in headless mode). It'll keep going page by page, printing progress as it works, until there's no next page left.

Logs (page numbers scraped, item counts, errors) go to `mega_scraper.log` alongside the console output.

## Files in this project

| File | Purpose |
|---|---|
| `mega_scraper.py` | Main scraper script |
| `mega_scraper.log` | Run logs |
| `laptops.csv` | Scraped output |

## Notes

- Selectors (`div.lap_thu_box`, `div.cat_price`, `div.pagination`, etc.) are tied to mega.pk's current HTML. If they redesign the site, these will need updating.
- Price fields come through as raw text (e.g. `"384,999 - PKR"`), so they'll need parsing/cleanup before doing any real analysis — similar to what was done for the Zameen project.
- Delete or back up `laptops.csv` before re-running if you don't want new data appended to old data.
