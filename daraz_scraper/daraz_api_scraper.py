import csv
import json
import os
import time
import random

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.daraz.pk/catalog/"
PROGRESS_PATH = "daraz_progress.json"
SEARCH_QUERY = "mobile phone"
CSV_PATH = "mobile_api.csv"
FIELDNAMES = [
    "name", "itemId", "price", "originalPrice", "discount",
    "location", "ratingScore", "review", "itemSoldCntShow",
    "sellerName", "brandName", "url",
]

# Cookie aur CSRF token ab .env file se aa rahe hain (see .env.example)
DARAZ_COOKIE = os.getenv("DARAZ_COOKIE", "")
DARAZ_CSRF_TOKEN = os.getenv("DARAZ_CSRF_TOKEN", "")

if not DARAZ_COOKIE or not DARAZ_CSRF_TOKEN:
    raise SystemExit(
        "DARAZ_COOKIE ya DARAZ_CSRF_TOKEN .env file mein set nahi hain.\n"
        "1. daraz.pk pe login karo\n"
        "2. DevTools -> Network tab se koi request select karo\n"
        "3. uska Cookie header aur x-csrf-token copy karo\n"
        "4. .env.example ko .env mein rename karke wahan paste karo"
    )

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.daraz.pk/",
    "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-csrf-token": DARAZ_CSRF_TOKEN,
    "Cookie": DARAZ_COOKIE,
}


def fetch_page(page_number):
    """Ek page ka JSON data fetch karta hai."""
    params = {
        "ajax": "true",
        "isFirstRequest": "true" if page_number == 1 else "false",
        "page": page_number,
        "q": SEARCH_QUERY,
    }

    response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
    response.raise_for_status()

    try:
        return response.json()
    except json.JSONDecodeError:
    
        print(f"  [DEBUG] Status code: {response.status_code}")
        print(f"  [DEBUG] Response text (first 300 chars): {response.text[:300]!r}")
        raise


def extract_items(data):
    """JSON response se listItems nikal kar clean dict banata hai."""

    list_items = data.get("mods", {}).get("listItems", [])

    items = []
    for item in list_items:
        items.append({
            "name": item.get("name", "N/A"),
            "itemId": item.get("itemId", "N/A"),
            "price": item.get("price", "N/A"),
            "originalPrice": item.get("originalPrice", "N/A"),
            "discount": item.get("discount", "N/A"),
            "location": item.get("location", "N/A"),
            "ratingScore": item.get("ratingScore", "N/A"),
            "review": item.get("review", "N/A"),
            "itemSoldCntShow": item.get("itemSoldCntShow", "N/A"),
            "sellerName": item.get("sellerName", "N/A"),
            "brandName": item.get("brandName", "N/A"),
            "url": "https:" + item.get("itemUrl", "") if item.get("itemUrl") else "N/A",
        })

    return items


def load_progress():
    """Pichli baar jahan ruke thay, wahan se page number uthao."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r") as f:
            progress = json.load(f)
            return progress.get("page", 1)
    return 1


def save_progress(page_number):
    """Current page number ko progress file mein save karo."""
    with open(PROGRESS_PATH, "w") as f:
        json.dump({"page": page_number}, f, indent=4)


def main():
    all_items = []
    page = load_progress()
    max_pages = 200  # safety limit

    if page > 1:
        print(f"Resuming from page {page} (progress file found)")

    consecutive_failures = 0
    max_consecutive_failures = 3  

    while page <= max_pages:
        print(f"Fetching page {page}...")

        try:
            data = fetch_page(page)
            consecutive_failures = 0  
        except Exception as e:
            consecutive_failures += 1
            print(f"Error fetching page {page}: {e} (failure {consecutive_failures}/{max_consecutive_failures})")

            if consecutive_failures >= max_consecutive_failures:
                print("Too many consecutive failures. Stopping (Daraz may be rate-limiting).")
                break

            
            backoff_time = 5 * consecutive_failures
            print(f"Retrying page {page} after {backoff_time}s...")
            time.sleep(backoff_time)
            continue

        items = extract_items(data)

        if not items:
            print("No more items found. Stopping.")
            break

        print(f"Page {page}: {len(items)} items found")
        all_items.extend(items)

      
        file_exists_flag = os.path.exists(CSV_PATH)
        mode = "a" if file_exists_flag else "w"
        with open(CSV_PATH, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists_flag:
                writer.writeheader()
            writer.writerows(items)

        page += 1
        save_progress(page) 
        wait_time = random.uniform(1, 3)
        time.sleep(wait_time)

    print(f"\nDone. Total items scraped: {len(all_items)}")
    print(f"Saved to {CSV_PATH}")


if __name__ == "__main__":
    main()