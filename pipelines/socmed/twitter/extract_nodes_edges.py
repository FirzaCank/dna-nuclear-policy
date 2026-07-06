"""
Extract nodes + edges CSVs from twitter_cleaned.csv
Output: twitter_nodes.csv, twitter_edges_mention.csv
"""

import csv
from collections import defaultdict
from pathlib import Path

ROOT   = Path(__file__).parent.parent.parent.parent
TW_DIR = ROOT / "data" / "processed" / "twitter"

rows = list(csv.DictReader(open(TW_DIR / "twitter_cleaned.csv")))

# ── Nodes ─────────────────────────────────────────────────────────────────────
node_stats = defaultdict(lambda: {"n_tweets": 0, "followers": 0, "following": 0,
                                   "verified": False, "tweet_count": 0,
                                   "total_likes": 0, "total_retweets": 0,
                                   "total_views": 0})
for r in rows:
    u = r["username"].strip()
    if not u:
        continue
    s = node_stats[u]
    s["n_tweets"] += 1
    s["followers"]      = max(s["followers"],      int(r.get("user_followers_count") or 0))
    s["following"]      = max(s["following"],       int(r.get("user_following_count") or 0))
    s["tweet_count"]    = max(s["tweet_count"],     int(r.get("user_tweet_count") or 0))
    s["verified"]       = s["verified"] or str(r.get("user_verified","")).lower() == "true"
    s["total_likes"]    += int(r.get("favorite_count") or 0)
    s["total_retweets"] += int(r.get("retweet_count") or 0)
    s["total_views"]    += int(r.get("view_count") or 0)

nodes_path = TW_DIR / "twitter_nodes.csv"
with open(nodes_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["username","n_tweets_in_dataset","followers_count","following_count",
                "tweet_count","is_verified","total_likes","total_retweets","total_views"])
    for u, s in sorted(node_stats.items(), key=lambda x: -x[1]["n_tweets"]):
        w.writerow([u, s["n_tweets"], s["followers"], s["following"],
                    s["tweet_count"], s["verified"],
                    s["total_likes"], s["total_retweets"], s["total_views"]])

print(f"Nodes: {len(node_stats)} → {nodes_path}")

# ── Edges (mention) ───────────────────────────────────────────────────────────
edge_count = defaultdict(int)
for r in rows:
    src = r["username"].strip()
    mentions_raw = r.get("user_mentions", "") or ""
    for tgt in mentions_raw.split(","):
        tgt = tgt.strip()
        if tgt and tgt != src:
            edge_count[(src, tgt)] += 1

edges_path = TW_DIR / "twitter_edges_mention.csv"
with open(edges_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source", "target", "weight"])
    for (s, t), w_ in sorted(edge_count.items(), key=lambda x: -x[1]):
        w.writerow([s, t, w_])

print(f"Edges: {len(edge_count)} → {edges_path}")
