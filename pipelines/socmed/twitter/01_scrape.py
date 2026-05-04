"""
STEP 1 - Scrape Twitter/X by Keyword (ScrapeBadger API)
========================================================
Searches Twitter for tweets matching each keyword from variable_keywords.csv.
Uses ScrapeBadger advanced search API (no browser needed).

Input : data/raw/variable_keywords.csv
Output: data/processed/twitter/twitter_raw.csv

Setup:
  Add to .env: SCRAPEBADGER_KEY=your_api_key
  Get key at: https://scrapebadger.com/dashboard/api-keys

Run: source venv/bin/activate && python pipelines/socmed/twitter/01_scrape.py
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")

ROOT      = Path(__file__).parent.parent.parent.parent
INPUT_KW  = ROOT / "data" / "raw" / "variable_keywords.csv"
TW_DIR    = ROOT / "data" / "processed" / "twitter"
OUTPUT    = TW_DIR / "twitter_raw.csv"
TW_DIR.mkdir(parents=True, exist_ok=True)

API_KEY    = os.getenv("SCRAPE_BADGER")
API_URL    = "https://scrapebadger.com/v1/twitter/tweets/advanced_search"
MAX_PAGES  = 5      # max pages per keyword (20 tweets/page → 100 max)
SLEEP_REQ  = 3.0    # seconds between page requests
SLEEP_KW   = 8.0    # seconds between keywords
TEST_MODE  = False
TEST_KW    = 2


def scrape_keyword(keyword: str, existing_ids: set) -> list:
    headers = {"x-api-key": API_KEY}
    params  = {
        "query"      : f"{keyword} lang:id",
        "query_type" : "Latest",
        "count"      : 20,
    }
    results = []
    cursor  = None

    for page in range(MAX_PAGES):
        if cursor:
            params["cursor"] = cursor
        elif "cursor" in params:
            del params["cursor"]

        try:
            resp = requests.get(API_URL, headers=headers, params=params, timeout=30)
            if resp.status_code == 429:
                print(f"  429 rate limit page {page+1}, waiting 30s...")
                time.sleep(30)
                resp = requests.get(API_URL, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ERROR page {page+1}: {e}")
            break

        tweets = data.get("data") or []
        new = 0
        for t in tweets:
            if t.get("is_retweet"):
                continue
            tid = str(t.get("id", ""))
            if not tid or tid in existing_ids:
                continue
            existing_ids.add(tid)

            hashtags = ",".join(h.get("text","") for h in (t.get("hashtags") or []))
            mentions = ",".join(m.get("username","") for m in (t.get("user_mentions") or []))

            results.append({
                "tweet_id"            : tid,
                "tweet_url"           : f"https://twitter.com/{t.get('username','')}/status/{tid}",
                "username"            : t.get("username", ""),
                "user_name"           : t.get("user_name", ""),
                "user_followers_count": t.get("user_followers_count", 0),
                "user_following_count": t.get("user_following_count", 0),
                "user_tweet_count"    : t.get("user_tweet_count", 0),
                "user_verified"       : t.get("user_verified", False) or t.get("user_is_blue_verified", False),
                "created_at"          : t.get("created_at", ""),
                "text"                : t.get("full_text") or t.get("text", ""),
                "favorite_count"      : t.get("favorite_count", 0),
                "retweet_count"       : t.get("retweet_count", 0),
                "reply_count"         : t.get("reply_count", 0),
                "quote_count"         : t.get("quote_count", 0),
                "view_count"          : t.get("view_count", 0),
                "hashtags"            : hashtags,
                "user_mentions"       : mentions,
            })
            new += 1

        cursor = data.get("next_cursor")
        print(f"    page {page+1}: {len(tweets)} tweets, {new} new, cursor={'yes' if cursor else 'no'}")

        if not cursor or not tweets:
            break
        time.sleep(SLEEP_REQ)

    return results


def main():
    if not API_KEY:
        print("[ERROR] SCRAPE_BADGER not set in .env")
        return

    kw_df = pd.read_csv(INPUT_KW, sep="\t")
    kw_df.columns = [c.strip() for c in kw_df.columns]
    if TEST_MODE:
        kw_df = kw_df.head(TEST_KW)
        print(f"[TEST MODE] {TEST_KW} keywords only")

    existing_ids = set()
    all_rows = []
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT, dtype=str)
        existing_ids = set(prev["tweet_id"].dropna().tolist())
        all_rows = prev.to_dict("records")
        print(f"[RESUME] {len(existing_ids)} tweets already scraped")

    for i, row in kw_df.iterrows():
        var_num  = str(row.get("Variabel", "")).strip()
        var_name = str(row.get("Variabel", "")).strip()
        keyword  = str(row.get("Keyword", "")).strip()

        # parse variable_number from Kategori column
        kategori = str(row.get("Kategori", "")).strip()
        var_num  = kategori.split(".")[0].strip() if "." in kategori else str(i+1)

        print(f"[{i+1}/{len(kw_df)}] keyword='{keyword}' | var='{var_name}'")
        tweets = scrape_keyword(keyword, existing_ids)

        for t in tweets:
            t["variable_number"] = var_num
            t["variable_name"]   = var_name
            t["keyword"]         = keyword
        all_rows.extend(tweets)

        print(f"  → {len(tweets)} new tweets | total: {len(all_rows)}")
        pd.DataFrame(all_rows).to_csv(OUTPUT, index=False)
        time.sleep(SLEEP_KW)

    print(f"\n[DONE] {len(all_rows)} tweets → {OUTPUT}")


if __name__ == "__main__":
    main()
