"""
Extract nodes + edges CSVs from facebook_cleaned.csv
Output: facebook_nodes.csv, facebook_edges_mention.csv
"""

import csv
from collections import defaultdict
from pathlib import Path

ROOT   = Path(__file__).parent.parent.parent.parent
FB_DIR = ROOT / "data" / "processed" / "facebook"

rows = list(csv.DictReader(open(FB_DIR / "facebook_cleaned.csv")))

# ── Nodes ─────────────────────────────────────────────────────────────────────
node_stats = defaultdict(lambda: {"n_posts": 0, "total_likes": 0,
                                   "total_comments": 0, "total_shares": 0,
                                   "full_name": ""})
for r in rows:
    u = r.get("username", "").strip()
    if not u:
        continue
    s = node_stats[u]
    s["n_posts"] += 1
    s["total_likes"]    += int(r.get("like_count") or 0)
    s["total_comments"] += int(r.get("comment_count") or 0)
    s["total_shares"]   += int(r.get("shares") or 0)
    if not s["full_name"] and r.get("full_name"):
        s["full_name"] = r["full_name"]

nodes_path = FB_DIR / "facebook_nodes.csv"
with open(nodes_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["username","full_name","n_posts_in_dataset",
                "total_likes","total_comments","total_shares"])
    for u, s in sorted(node_stats.items(), key=lambda x: -x[1]["n_posts"]):
        w.writerow([u, s["full_name"], s["n_posts"],
                    s["total_likes"], s["total_comments"], s["total_shares"]])

print(f"Nodes: {len(node_stats)} → {nodes_path}")

# ── Edges (mention) ───────────────────────────────────────────────────────────
edge_count = defaultdict(int)
for r in rows:
    src = r.get("username", "").strip()
    mentions_raw = r.get("mentions", "") or ""
    for tgt in mentions_raw.split(","):
        tgt = tgt.strip()
        if tgt and tgt != src:
            edge_count[(src, tgt)] += 1

edges_path = FB_DIR / "facebook_edges_mention.csv"
with open(edges_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source", "target", "weight"])
    for (s, t), w_ in sorted(edge_count.items(), key=lambda x: -x[1]):
        w.writerow([s, t, w_])

print(f"Edges: {len(edge_count)} → {edges_path}")
