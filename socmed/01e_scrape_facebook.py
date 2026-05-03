"""
STEP 1e — Scrape Facebook Public Pages
========================================
Scrapes posts from public Facebook pages using facebook-scraper.
Requires browser cookies (Facebook now blocks scraping without login).

Input : input/Facebook/facebook_pages.csv
          columns: page_name, variable_number, category, variable_name, keyword
        input/Facebook/facebook_cookies.txt  (Netscape cookie format)
Output: output/socmed/facebook/facebook_raw.csv

HOW TO GET COOKIES:
  1. Login to Facebook in Chrome/Firefox
  2. Install Chrome extension: "Get cookies.txt LOCALLY"
  3. Go to facebook.com → click extension → Export
  4. Save as: input/Facebook/facebook_cookies.txt
  5. Add to .env: FB_COOKIES_FILE=input/Facebook/facebook_cookies.txt

Run: source venv/bin/activate && python socmed/01e_scrape_facebook.py
"""

import os
import re
import time
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

ROOT     = Path(__file__).parent.parent
INPUT    = ROOT / "input" / "Facebook" / "facebook_pages.csv"
FB_DIR   = ROOT / "output" / "socmed" / "facebook"
OUTPUT   = FB_DIR / "facebook_raw.csv"
FB_DIR.mkdir(parents=True, exist_ok=True)

# ── Config ─────────────────────────────────────────────────────────────────────
MAX_POSTS    = 200   # max posts per page (set lower for testing)
SLEEP_SEC    = 3.0   # between pages
TEST_MODE    = False
TEST_PAGES   = 1
TEST_POSTS   = 5

# Cookies file — required for modern Facebook scraping
_cookies_env = os.getenv("FB_COOKIES_FILE", "input/Facebook/facebook_cookies.txt")
FB_COOKIES   = str(ROOT / _cookies_env) if not Path(_cookies_env).is_absolute() else _cookies_env


def extract_hashtags(text: str) -> str:
    if not text:
        return ""
    tags = re.findall(r"#(\w+)", text)
    return ",".join(tags)


def extract_mentions(text: str) -> str:
    if not text:
        return ""
    mentions = re.findall(r"@(\w+)", text)
    return ",".join(mentions)


def get_scraper_options() -> dict:
    opts = {
        "reactions": False,
        "allow_extra_requests": False,
    }
    if Path(FB_COOKIES).exists():
        opts["cookies"] = FB_COOKIES
        print(f"  [AUTH] Using cookies: {FB_COOKIES}")
    else:
        print(f"  [WARN] No cookies file at {FB_COOKIES} — scraping may fail")
    return opts


def scrape_page(page_name: str, max_posts: int) -> list:
    from facebook_scraper import get_posts, exceptions
    rows = []
    options = get_scraper_options()
    kwargs = {"pages": max(3, max_posts // 10 + 1), "options": options}

    try:
        count = 0
        for post in get_posts(page_name, **kwargs):  # noqa
            if count >= max_posts:
                break
            text = str(post.get("text") or post.get("post_text") or "").strip()
            rows.append({
                "post_url"    : post.get("post_url", ""),
                "pub_date"    : str(post.get("time", "")),
                "username"    : page_name,
                "full_name"   : str(post.get("username") or page_name),
                "caption"     : text,
                "like_count"  : post.get("likes", 0) or 0,
                "comment_count": post.get("comments", 0) or 0,
                "shares"      : post.get("shares", 0) or 0,
                "hashtags"    : extract_hashtags(text),
                "mentions"    : extract_mentions(text),
                "post_id"     : str(post.get("post_id", "")),
            })
            count += 1
    except exceptions.TemporarilyBanned:
        print(f"  [BANNED] Temporarily banned — wait before retrying")
    except exceptions.LoginRequired:
        print(f"  [LOGIN] Page '{page_name}' requires login — set FB_EMAIL/FB_PASSWORD in .env")
    except Exception as e:
        print(f"  [ERROR] {page_name}: {e}")

    return rows


def main():
    df_pages = pd.read_csv(INPUT)
    if TEST_MODE:
        df_pages = df_pages.head(TEST_PAGES)
        print(f"[TEST MODE] {TEST_PAGES} pages, {TEST_POSTS} posts each")

    # load already-scraped post_ids
    done_ids = set()
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT, dtype=str)
        done_ids = set(prev["post_id"].dropna().tolist())
        print(f"[RESUME] {len(done_ids)} posts already scraped")

    all_rows = []
    total_pages = len(df_pages)

    for i, (_, page_row) in enumerate(df_pages.iterrows()):
        page_name = str(page_row["page_name"]).strip()
        max_p     = TEST_POSTS if TEST_MODE else MAX_POSTS

        print(f"[{i+1}/{total_pages}] Scraping: {page_name} (max {max_p} posts)...")
        posts = scrape_page(page_name, max_p)

        new_posts = [p for p in posts if p["post_id"] not in done_ids]
        print(f"  → {len(posts)} fetched | {len(new_posts)} new")

        for post in new_posts:
            post["variable_number"] = page_row.get("variable_number", "")
            post["category"]        = page_row.get("category", "")
            post["variable_name"]   = page_row.get("variable_name", "")
            post["keyword"]         = page_row.get("keyword", "")
            all_rows.append(post)
            done_ids.add(post["post_id"])

        time.sleep(SLEEP_SEC)

    if not all_rows:
        print("[DONE] No new posts scraped.")
        return

    new_df = pd.DataFrame(all_rows)

    # merge with existing
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT, dtype=str)
        combined = pd.concat([prev, new_df], ignore_index=True)
        combined.drop_duplicates(subset="post_id", keep="last", inplace=True)
    else:
        combined = new_df

    combined.to_csv(OUTPUT, index=False)
    print(f"\n[DONE] {len(combined)} total posts → {OUTPUT}")
    print(f"Columns: {list(combined.columns)}")


if __name__ == "__main__":
    main()
