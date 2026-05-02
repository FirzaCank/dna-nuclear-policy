"""
STEP 1d - Fetch YouTube video + channel metadata via YouTube Data API v3.
Batch 50 videos per request — quota-efficient.

Input : output/socmed/youtube/youtube_merged.csv
Output: output/socmed/youtube/youtube_metadata.csv

Run: source venv/bin/activate && python socmed/01d_fetch_youtube_metadata.py
"""

import os
import re
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

ROOT      = Path(__file__).parent.parent
INPUT     = ROOT / "output" / "socmed" / "youtube" / "youtube_merged.csv"
OUTPUT    = ROOT / "output" / "socmed" / "youtube" / "youtube_metadata.csv"

API_KEY   = os.getenv("YT_API_KEY")
BATCH     = 50
SLEEP_SEC = 0.5


def get_video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", str(url))
    return m.group(1) if m else None


def fetch_videos(video_ids: list) -> dict:
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": API_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    out = {}
    for item in resp.json().get("items", []):
        vid   = item["id"]
        snip  = item["snippet"]
        stats = item.get("statistics", {})
        cd    = item.get("contentDetails", {})
        out[vid] = {
            "video_title":        snip.get("title", ""),
            "published_at":       snip.get("publishedAt", ""),
            "channel_id":         snip.get("channelId", ""),
            "channel_title":      snip.get("channelTitle", ""),
            "description":        snip.get("description", ""),
            "tags":               ",".join(snip.get("tags", [])),
            "view_count":         stats.get("viewCount", ""),
            "like_count":         stats.get("likeCount", ""),
            "comment_count":      stats.get("commentCount", ""),
            "duration":           cd.get("duration", ""),
        }
    return out


def fetch_channels(channel_ids: list) -> dict:
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "part": "snippet,statistics",
            "id": ",".join(channel_ids),
            "key": API_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    out = {}
    for item in resp.json().get("items", []):
        cid   = item["id"]
        snip  = item["snippet"]
        stats = item.get("statistics", {})
        out[cid] = {
            "channel_description":   snip.get("description", ""),
            "channel_country":       snip.get("country", ""),
            "channel_created_at":    snip.get("publishedAt", ""),
            "subscriber_count":      stats.get("subscriberCount", ""),
            "channel_video_count":   stats.get("videoCount", ""),
            "channel_view_count":    stats.get("viewCount", ""),
        }
    return out


def main():
    df = pd.read_csv(INPUT)
    df["video_id"] = df["video_url"].apply(get_video_id)
    df = df.dropna(subset=["video_id"]).copy()
    print(f"[INPUT] {len(df)} videos with valid IDs")

    # load already fetched
    done = set()
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT)
        done = set(prev["video_id"].dropna())
        print(f"[RESUME] {len(done)} already fetched")

    pending_ids = [vid for vid in df["video_id"].tolist() if vid not in done]
    print(f"[PENDING] {len(pending_ids)} videos")

    # ── Fetch video metadata in batches ──────────────────────────────────────
    video_meta = {}
    for i in range(0, len(pending_ids), BATCH):
        batch = pending_ids[i:i+BATCH]
        video_meta.update(fetch_videos(batch))
        print(f"  Videos fetched: {min(i+BATCH, len(pending_ids))}/{len(pending_ids)}")
        time.sleep(SLEEP_SEC)

    # ── Fetch channel metadata ────────────────────────────────────────────────
    channel_ids = list({v["channel_id"] for v in video_meta.values() if v.get("channel_id")})
    channel_meta = {}
    for i in range(0, len(channel_ids), BATCH):
        batch = channel_ids[i:i+BATCH]
        channel_meta.update(fetch_channels(batch))
        time.sleep(SLEEP_SEC)
    print(f"  Channels fetched: {len(channel_meta)}")

    # ── Merge into DataFrame ──────────────────────────────────────────────────
    rows = []
    for _, row in df.iterrows():
        vid = row["video_id"]
        vm  = video_meta.get(vid, {})
        cm  = channel_meta.get(vm.get("channel_id", ""), {})
        rows.append({**row.to_dict(), **vm, **cm})

    new_df = pd.DataFrame(rows)

    # merge with existing if resuming
    if done and OUTPUT.exists():
        prev = pd.read_csv(OUTPUT)
        new_df = pd.concat([prev, new_df], ignore_index=True)
        new_df.drop_duplicates(subset="video_id", keep="last", inplace=True)

    new_df.to_csv(OUTPUT, index=False)
    print(f"\n[DONE] {len(new_df)} rows → {OUTPUT}")
    print(f"Columns: {list(new_df.columns)}")


if __name__ == "__main__":
    main()
