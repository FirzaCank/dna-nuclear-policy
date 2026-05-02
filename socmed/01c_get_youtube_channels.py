"""
Get YouTube channel URLs from video URLs.
Fetches one video page per unique channel_name to extract @handle or channel_id.
Resumable: skips already-resolved channels.

Input : output/socmed/youtube/youtube_merged.csv
Output: output/socmed/youtube/youtube_channel_urls.csv
         columns: channel_name, channel_url, domain
Run   : source venv/bin/activate && python socmed/01c_get_youtube_channels.py
"""

import re
import time
import requests
import pandas as pd
from pathlib import Path

ROOT      = Path(__file__).parent.parent
INPUT     = ROOT / "output" / "socmed" / "youtube" / "youtube_merged.csv"
OUTPUT    = ROOT / "output" / "socmed" / "youtube" / "youtube_channel_urls.csv"

SLEEP_SEC = 1.5
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# patterns to extract channel path from YouTube video page HTML
CHANNEL_PATTERNS = [
    re.compile(r'"canonicalBaseUrl":"(/@[^"]+)"'),       # @handle (preferred)
    re.compile(r'"channelUrl":"(/@[^"]+)"'),
    re.compile(r'"ownerProfileUrl":"(http[^"]+)"'),
    re.compile(r'"externalChannelId":"(UC[^"]+)"'),      # fallback: channel ID
]


def extract_channel_url(video_url: str) -> str | None:
    try:
        resp = requests.get(video_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        html = resp.text
        for pat in CHANNEL_PATTERNS:
            m = pat.search(html)
            if m:
                val = m.group(1)
                if val.startswith("/@"):
                    return f"https://www.youtube.com{val}"
                if val.startswith("UC"):
                    return f"https://www.youtube.com/channel/{val}"
                if val.startswith("http"):
                    return val
        return None
    except Exception as e:
        print(f"    ERROR fetching {video_url}: {e}")
        return None


def main():
    df = pd.read_csv(INPUT)
    print(f"[INPUT] {len(df)} rows, {df['channel_name'].nunique()} unique channels")

    # load already resolved
    done = {}
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT)
        done = dict(zip(prev["channel_name"], prev["channel_url"]))
        print(f"[RESUME] {len(done)} already resolved")

    # pick one video per channel (first occurrence)
    channel_video = (
        df.dropna(subset=["video_url"])
        .drop_duplicates(subset=["channel_name"])
        .set_index("channel_name")["video_url"]
        .to_dict()
    )

    pending = {ch: url for ch, url in channel_video.items() if ch not in done}
    print(f"[PENDING] {len(pending)} channels to resolve")

    results = dict(done)

    for i, (channel_name, video_url) in enumerate(pending.items()):
        if not isinstance(channel_name, str) or not channel_name.strip():
            continue
        print(f"  [{i+1}/{len(pending)}] {channel_name[:50]}")
        channel_url = extract_channel_url(video_url)
        results[channel_name] = channel_url or ""
        if channel_url:
            print(f"    → {channel_url}")
        else:
            print(f"    → not found")
        time.sleep(SLEEP_SEC)

    out_df = pd.DataFrame([
        {"channel_name": ch, "channel_url": url, "domain": "YouTube"}
        for ch, url in results.items()
    ]).sort_values("channel_name").reset_index(drop=True)

    out_df.to_csv(OUTPUT, index=False)

    resolved = (out_df["channel_url"] != "").sum()
    print(f"\n[DONE] {resolved}/{len(out_df)} channels resolved")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
