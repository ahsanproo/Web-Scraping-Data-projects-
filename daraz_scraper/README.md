# Daraz.pk Mobile Phone Scraper

Two different ways of scraping mobile phone listings from Daraz.pk, searching for "mobile phone". One goes through the actual browser (Playwright), the other hits Daraz's internal API directly. Both were built at different points — looks like the API version came after, probably to get more data (ratings, reviews, sold count, seller info) faster than clicking through pages.

## Two approaches, two scripts

### 1. `daraz_scraper.py` — browser-based

Opens Daraz's search results in a real (visible) browser and scrapes what's shown on the page:

- Title, product URL
- Price, discount
- Sold count
- Rating — counted as number of filled star icons (`i._9-ogB`), not a numeric rating value

Saves to `mobile.csv`.

Pagination here works the same way as the mega.pk scraper: Daraz's "next" button doesn't change the URL, so the script grabs the first listing's title before clicking, then waits for that title to change as proof the new page loaded. It also checks Ant Design's pagination classes (`ant-pagination-next`, `ant-pagination-disabled`) to know when it's hit the last page.

### 2. `daraz_api_scraper.py` — API-based

Instead of driving a browser, this one calls Daraz's own catalog API (`daraz.pk/catalog/`) directly with `requests`, passing the search query and page number as parameters. Since it's straight JSON, it pulls a lot more per item:

- Name, item ID, price, original price, discount
- Location, rating score, review count
- Units sold, seller name, brand name, product URL

Saves to `mobile_api.csv`. This one's also faster since there's no browser overhead — it's just HTTP requests with a small random delay (1–3s) between pages.

Both scripts have resume support via a progress file (`daraz_progress.json` — used by the API version to track the last completed page) and retry/backoff handling for failed requests.

## ⚠️ Important: about the cookies used by `daraz_api_scraper.py`

The API script authenticates using a `Cookie` header and CSRF token copied from a real logged-in browser session. These are **no longer hardcoded in the script** — they're loaded from a `.env` file instead, so the real values never end up in git history.

- **These cookies will expire.** Daraz's session tokens don't last forever — once they do, the script will fail (likely with JSON decode errors, since you'll get an HTML/login page back instead of API data). When that happens: log into daraz.pk in a browser, open DevTools → Network tab, grab the fresh `Cookie` and `x-csrf-token` values from any request, and update your `.env` file.
- **`.env` is git-ignored** — it will never get committed. Only `.env.example` (a blank template) is tracked in the repo.

## Setup

**Browser scraper:**
```bash
pip install -r requirements.txt
playwright install chromium
```

**API scraper — also needs a `.env` file:**
```bash
cp .env.example .env
```
Then open `.env` and paste in your own `DARAZ_COOKIE` and `DARAZ_CSRF_TOKEN` (see instructions inside the file for how to get them from DevTools).

## Running it

```bash
python daraz_scraper.py       # browser-based, saves to mobile.csv
python daraz_api_scraper.py   # API-based, saves to mobile_api.csv
```

The API script has a `max_pages = 200` safety cap and stops early after 3 consecutive failures (assumes rate-limiting and bails instead of hammering the API).

## Files in this project

| File | Purpose |
|---|---|
| `daraz_scraper.py` | Browser-based scraper |
| `daraz_api_scraper.py` | API-based scraper (faster, more fields, needs valid cookies) |
| `daraz_progress.json` | Last completed page (used for resuming the API scraper) |
| `daraz_scraper.log` | Run logs for the browser scraper |
| `mobile.csv` | Output from the browser scraper |
| `mobile_api.csv` | Output from the API scraper |

## Notes

- The two scripts save to different CSVs with different columns — they're not meant to be merged as-is. `mobile_api.csv` has richer data (ratings, reviews, seller/brand info) while `mobile.csv` is more bare-bones.
- Prices in `mobile.csv` come as formatted strings (`"Rs. 16,829"`) — will need cleanup similar to the Zameen project before analysis.
- Log file shows a couple of separate runs (page 1 restarting partway through) — normal if the script was stopped and re-run manually rather than crashing.
