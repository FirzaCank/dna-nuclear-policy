"""
STEP 1e — Scrape Facebook Posts by Keyword Search (Playwright)
===============================================================
Searches Facebook for posts matching each keyword from variable_keywords.csv.
Uses Playwright + browser cookies (Facebook requires login).

Input : input/variable_keywords.csv
        data/raw/facebook/www.facebook.com_cookies.txt  (Netscape format)
Output: output/socmed/facebook/facebook_raw.csv

HOW TO GET COOKIES:
  1. Login to Facebook in Chrome
  2. Install extension: "Get cookies.txt LOCALLY"
  3. Go to facebook.com → click extension → Export
  4. Save as: data/raw/facebook/www.facebook.com_cookies.txt
  5. In .env: FB_COOKIES_FILE=data/raw/facebook/www.facebook.com_cookies.txt

Run: source venv/bin/activate && python socmed/01e_scrape_facebook.py
"""

import os
import re
import time
import urllib.parse
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

ROOT     = Path(__file__).parent.parent.parent.parent
INPUT_KW = ROOT / "data" / "raw" / "variable_keywords.csv"
FB_DIR   = ROOT / "data" / "processed" / "facebook"
OUTPUT   = FB_DIR / "facebook_raw.csv"
FB_DIR.mkdir(parents=True, exist_ok=True)

_ck_env      = os.getenv("FB_COOKIES_FILE", "data/raw/facebook/www.facebook.com_cookies.txt")
COOKIES_PATH = ROOT / _ck_env if not Path(_ck_env).is_absolute() else Path(_ck_env)

MAX_POSTS   = 50     # max posts per keyword
SCROLL_WAIT = 3.0    # seconds between scrolls
MAX_SCROLLS = 20     # max scrolls per keyword
SLEEP_KW    = 5.0    # seconds between keywords
TEST_MODE   = False
TEST_KW     = 2      # keywords in test mode
TEST_POSTS  = 5      # posts per keyword in test mode


def load_netscape_cookies(path: Path) -> list:
    cookies = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            domain, _, path_, secure, expires, name, value = parts[:7]
            cookies.append({
                "name":     name,
                "value":    value,
                "domain":   domain,   # keep leading dot
                "path":     path_,
                "secure":   secure.upper() == "TRUE",
                "httpOnly": False,
            })
    return cookies


def extract_hashtags(text: str) -> str:
    return ",".join(re.findall(r"#(\w+)", text or ""))


def extract_mentions(text: str) -> str:
    return ",".join(re.findall(r"@(\w+)", text or ""))


def scrape_keyword(page, keyword: str, max_posts: int) -> list:
    """Scrape Facebook search results for a keyword. `page` = Playwright page object."""
    url = f"https://www.facebook.com/search/posts/?q={urllib.parse.quote(keyword)}"
    rows = []
    seen = set()

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        time.sleep(6)

        # dismiss dialogs
        for sel in ['[aria-label="Close"]', 'div[role="dialog"] button']:
            try:
                page.click(sel, timeout=2000)
            except Exception:
                pass

        for scroll_n in range(MAX_SCROLLS):
            if len(rows) >= max_posts:
                break

            # Use JS to extract structured data per post card
            posts_data = page.evaluate("""() => {
                const previews = document.querySelectorAll('[data-ad-comet-preview]');
                const out = [];
                for (const el of previews) {
                    try {
                        // walk up to full card
                        let card = el;
                        for (let i = 0; i < 5; i++) card = card.parentElement;

                        // author: first non-search profile link
                        const authorLink = Array.from(card.querySelectorAll('a[href*="facebook.com/"]'))
                            .find(a => !a.href.includes('/search/') && !a.href.includes('/photo') && a.innerText.trim().length > 1);
                        const authorName   = authorLink ? authorLink.innerText.trim() : '';
                        const authorHref   = authorLink ? authorLink.href.split('?')[0] : '';
                        const username     = authorHref ? authorHref.replace(/https?:\\/\\/www\\.facebook\\.com\\//, '').split('/')[0] : '';

                        // like count from aria-label "Suka: N orang"
                        let likeCount = 0, commentCount = 0;
                        const ariaLabels = Array.from(card.querySelectorAll('[aria-label]'))
                            .map(e => e.getAttribute('aria-label'));
                        for (const lbl of ariaLabels) {
                            const m = lbl && lbl.match(/Suka:\\s*([\\d.,]+)/);
                            if (m) { likeCount = parseInt(m[1].replace(/[.,]/g,'')); break; }
                        }
                        for (const lbl of ariaLabels) {
                            const m = lbl && lbl.match(/Komentar:\\s*([\\d.,]+)/);
                            if (m) { commentCount = parseInt(m[1].replace(/[.,]/g,'')); break; }
                        }

                        // post URL: look for fbid or permalink
                        let postUrl = '';
                        const allLinks = Array.from(card.querySelectorAll('a[href]'));
                        for (const a of allLinks) {
                            const h = a.href;
                            if (h.includes('fbid=') || h.includes('/posts/') || h.includes('/permalink/')) {
                                postUrl = h.split('__cft__')[0].replace(/[?&]$/, '');
                                break;
                            }
                        }

                        // caption text (from data-ad-comet-preview)
                        const caption = el.innerText.trim();

                        out.push({ authorName, username, likeCount, commentCount, postUrl, caption });
                    } catch(e) { /* skip */ }
                }
                return out;
            }""")

            for pd_item in posts_data:
                if len(rows) >= max_posts:
                    break
                caption = pd_item.get("caption", "").strip()
                if not caption or len(caption) < 10:
                    continue
                uname = pd_item.get("username", pd_item.get("authorName", ""))
                # unique post_id: always use username + caption hash (not search page URL)
                post_id = f"fb_{uname}_{abs(hash(caption[:200])) % 10**12}"
                real_url = pd_item.get("postUrl", "")
                # discard if post_url is just the search page (not a real post URL)
                if real_url and "/search/posts/" in real_url and "fbid" not in real_url:
                    real_url = ""

                uid = post_id
                if uid in seen:
                    continue
                seen.add(uid)

                rows.append({
                    "post_url"     : real_url,
                    "pub_date"     : "",   # obfuscated by Facebook; left empty
                    "username"     : uname,
                    "full_name"    : pd_item.get("authorName", ""),
                    "caption"      : caption[:3000],
                    "like_count"   : pd_item.get("likeCount", 0),
                    "comment_count": pd_item.get("commentCount", 0),
                    "shares"       : 0,
                    "hashtags"     : extract_hashtags(caption),
                    "mentions"     : extract_mentions(caption),
                    "post_id"      : post_id,
                })

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(SCROLL_WAIT)

    except Exception as e:
        print(f"  [ERROR] keyword='{keyword}': {e}")

    return rows


def main():
    if not COOKIES_PATH.exists():
        print(f"[ERROR] Cookies not found: {COOKIES_PATH}")
        print("  Export from Chrome with 'Get cookies.txt LOCALLY'")
        return

    cookies = load_netscape_cookies(COOKIES_PATH)
    print(f"[AUTH] {len(cookies)} cookies loaded")

    df_kw = pd.read_csv(INPUT_KW, sep="\t")
    df_kw.columns = [c.strip() for c in df_kw.columns]
    if TEST_MODE:
        df_kw = df_kw.head(TEST_KW)
        print(f"[TEST MODE] {TEST_KW} keywords, {TEST_POSTS} posts each")

    # load already-done post_ids
    done_ids = set()
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT, dtype=str)
        done_ids = set(prev["post_id"].dropna())
        print(f"[RESUME] {len(done_ids)} posts already scraped")

    all_rows = []
    total = len(df_kw)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="id-ID",
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        for i, (_, row) in enumerate(df_kw.iterrows()):
            keyword      = str(row["Keyword"]).strip()
            variable     = str(row["Variabel"]).strip()
            category     = str(row["Kategori"]).strip()
            var_num      = i + 1
            max_p        = TEST_POSTS if TEST_MODE else MAX_POSTS

            print(f"[{i+1}/{total}] keyword='{keyword}' | var='{variable}'")
            posts = scrape_keyword(page, keyword, max_p)
            new   = [p for p in posts if p["post_id"] not in done_ids]
            print(f"  → {len(posts)} scraped | {len(new)} new")

            for post in new:
                post["variable_number"] = var_num
                post["category"]        = category
                post["variable_name"]   = variable
                post["keyword"]         = keyword
                all_rows.append(post)
                done_ids.add(post["post_id"])

            # checkpoint save every 3 keywords
            if (i + 1) % 3 == 0 and all_rows:
                _save(all_rows, done_ids)

            if i < total - 1:
                time.sleep(SLEEP_KW)

        browser.close()

    if not all_rows:
        print("[DONE] No new posts.")
        return

    _save(all_rows, done_ids)


def _save(all_rows, done_ids):
    new_df = pd.DataFrame(all_rows)
    if OUTPUT.exists():
        prev  = pd.read_csv(OUTPUT, dtype=str)
        combined = pd.concat([prev, new_df], ignore_index=True)
        combined.drop_duplicates(subset="post_id", keep="last", inplace=True)
    else:
        combined = new_df
    combined.to_csv(OUTPUT, index=False)
    print(f"  [SAVED] {len(combined)} total posts → {OUTPUT}")


if __name__ == "__main__":
    main()
