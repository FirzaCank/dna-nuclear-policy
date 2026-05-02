"""
STEP 7 - BUZZER / BOT DETECTION
=================================
Scores each unique account on suspicious activity signals using profile data.
Score 0-4; threshold >= 2 = suspected buzzer.

Signals:
  1. following/followers ratio > 10  (following banyak, followers sedikit)
  2. post_count > 5000               (posting volume ekstrem)
  3. joined_recently == True         (akun baru)
  4. followers < 100 AND post_count > 1000  (bot-like: banyak post, sedikit followers)

Input : output/socmed_cleaned.csv
Output: output/socmed_buzzer_scores.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "output" / "socmed_cleaned.csv"
OUTPUT = ROOT / "output" / "socmed_buzzer_scores.csv"

BUZZER_THRESHOLD = 2


def score_buzzer(row):
    flags = []
    followers = row.get("followers_count")
    following = row.get("following_count")
    posts     = row.get("post_count")
    recent    = row.get("joined_recently")

    if pd.notna(followers) and pd.notna(following) and followers > 0:
        if following / followers > 10:
            flags.append("high_follow_ratio")

    if pd.notna(posts) and posts > 5000:
        flags.append("extreme_post_count")

    if recent is True or str(recent).lower() == "true":
        flags.append("joined_recently")

    if pd.notna(followers) and pd.notna(posts) and followers < 100 and posts > 1000:
        flags.append("low_followers_high_posts")

    return flags


def main():
    df = pd.read_csv(INPUT)

    profile_cols = ["username", "full_name", "followers_count", "following_count",
                    "post_count", "is_verified", "is_business", "joined_recently", "biography"]
    available = [c for c in profile_cols if c in df.columns]
    actors = df[available].drop_duplicates("username").copy()

    actors["buzzer_flags"]  = actors.apply(score_buzzer, axis=1)
    actors["buzzer_score"]  = actors["buzzer_flags"].apply(len)
    actors["is_buzzer"]     = actors["buzzer_score"] >= BUZZER_THRESHOLD
    actors["buzzer_flags"]  = actors["buzzer_flags"].apply(lambda x: ",".join(x))

    # add post count in this dataset
    post_counts = df.groupby("username").size().rename("n_posts_in_dataset")
    actors = actors.merge(post_counts, on="username", how="left")

    actors.sort_values("buzzer_score", ascending=False, inplace=True)
    actors.reset_index(drop=True, inplace=True)

    actors.to_csv(OUTPUT, index=False)

    n_buzzers = actors["is_buzzer"].sum()
    print(f"[INPUT] {len(actors)} unique accounts")
    print(f"[BUZZERS] {n_buzzers} suspected buzzers ({n_buzzers/len(actors)*100:.1f}%)")
    print(f"\nScore distribution:")
    print(actors["buzzer_score"].value_counts().sort_index().to_string())
    print(f"\nTop 15 suspected buzzers:")
    cols = ["username", "buzzer_score", "buzzer_flags", "followers_count", "following_count", "post_count"]
    print(actors[actors["is_buzzer"]][[c for c in cols if c in actors.columns]].head(15).to_string(index=False))
    print(f"\nOutput: {OUTPUT}")


if __name__ == "__main__":
    main()
