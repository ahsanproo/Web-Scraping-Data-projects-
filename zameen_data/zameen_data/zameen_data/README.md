# Zameen.com Property Scraper

A Playwright-based scraper that pulls property listings (for Lahore) from Zameen.com and dumps them into a CSV. There's also a cleanup script that takes the raw scraped data and turns it into something actually usable for analysis.

## What it does

`scraper.py` opens Zameen.com listing pages one by one, grabs the following for every property:

- Title
- Price
- Location
- Beds / Baths
- Area
- Property type, purpose (sale/rent), and posting date — these come from the listing's own detail page, since they're not shown on the listing card
- Listing URL

It saves everything to `zameen_data.csv`, appending page by page instead of writing everything at the end. It also skips ads (images, fonts, media, doubleclick/googlesyndication requests) to keep page loads faster.

### Resume support

If the script crashes or you stop it midway, it doesn't start over. It keeps track of the current page in `progress.json`, so next time you run it, it just picks up from where it left off.

### Retry logic

Both the initial page load and the "click Next page" step have a 3-attempt retry built in, since Zameen's pages can be flaky or slow to load. If something fails after 3 tries, it logs the error and stops instead of hanging forever.

### Logging

Everything (page numbers, errors, retries, current URL) gets logged to `scraper.log`, in addition to printing to the console. Useful if you want to check what happened during a long overnight run without watching the terminal the whole time.

## Cleaning the data

Raw scraped data is messy — inconsistent price formats (Crore/Lakh/plain numbers), area in different units (Marla/Kanal/Sq Ft/Sq Yd), missing fields marked as "N/A", duplicate listings, etc.

`clean_zameen_data.py` handles all of that:

- Drops duplicate listings (same URL)
- Converts "N/A" and blank values to actual `NaN`
- Parses price strings into a proper numeric column (`price_pkr`) — handles Crore, Lakh, and plain PKR values
- Extracts beds/baths as numbers
- Parses area into a value + unit, then converts everything into a common `area_marla` column (Kanal → Marla, Sq Ft → Marla, Sq Yd → Marla) so properties can actually be compared
- Splits location into `area_name` and `city` — with a special case for DHA listings, since Zameen's location strings for DHA don't cleanly separate into area/city otherwise
- Drops rows where both price and area are missing (basically unusable rows)

Output goes to `zameen_data_cleaned.csv`.

## Setup

```bash
pip install -r requirments.txt
playwright install chromium
```

(Yes, the requirements file has a typo in the name — `requirments.txt`, not `requirements.txt`. Kept it as-is so nothing breaks. It only lists `playwright` and `pandas` — those are the only two actually used by these scripts.)

## Running it

**1. Scrape the data:**

```bash
python scraper.py
```

This runs in a visible (non-headless) browser window — it's set up that way on purpose, since Zameen can be picky about headless bots. Let it run; it'll go page by page until there's no "Next" button left, i.e. the last page.

To scrape a different city, change the `url` variable in `scraper.py` (currently hardcoded to Lahore, page 1 onward).

**2. Clean the data:**

```bash
python clean_zameen_data.py
```

Reads `zameen_data.csv`, cleans it, and writes `zameen_data_cleaned.csv`.

## Files in this project

| File | Purpose |
|---|---|
| `scraper.py` | Main scraper script |
| `clean_zameen_data.py` | Cleans and structures the raw CSV |
| `progress.json` | Tracks last scraped page (for resuming) |
| `scraper.log` | Run logs — errors, retries, page progress |
| `zameen_data.csv` | Raw scraped output |
| `zameen_data_cleaned.csv` | Cleaned, analysis-ready output |
| `requirments.txt` | Python dependencies |

## Notes / things to keep in mind

- Selectors are based on Zameen's current page structure (things like `aria-label="Listing"`, `aria-label="Price"`, etc.). If Zameen changes their site layout, the scraper will need selector updates.
- Right now it's hardcoded for Lahore listings only.
- Since it visits each property's detail page individually (for type/purpose/date), scraping is on the slower side — this is a tradeoff for getting more complete data per listing.
- Delete `progress.json` if you want to start scraping from page 1 again instead of resuming.
