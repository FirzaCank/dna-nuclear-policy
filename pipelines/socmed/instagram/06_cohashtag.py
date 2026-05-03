"""
STEP 6 - CO-HASHTAG NETWORK
=============================
Builds hashtag co-occurrence network: two hashtags are connected if they
appear together in the same post. Edge weight = co-occurrence frequency.

Input : output/socmed_cleaned.csv
Output: output/socmed_edges_hashtag.csv   (hashtag_a, hashtag_b, weight)
        output/socmed_nodes_hashtag.csv   (hashtag, total_posts, variable_top)
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict
from itertools import combinations

ROOT      = Path(__file__).parent.parent.parent.parent
IG_DIR    = ROOT / "data" / "processed" / "instagram"
INPUT     = IG_DIR / "socmed_cleaned.csv"
OUT_EDGES = IG_DIR / "socmed_edges_hashtag.csv"
OUT_NODES = IG_DIR / "socmed_nodes_hashtag.csv"

MIN_COOCCURRENCE = 3   # minimum co-occurrence to include edge
MIN_POSTS        = 2   # minimum posts for a hashtag node


def main():
    df = pd.read_csv(INPUT)
    print(f"[INPUT] {len(df)} posts")

    cooccur = defaultdict(int)
    hashtag_posts = defaultdict(int)
    hashtag_variables = defaultdict(lambda: defaultdict(int))

    for _, row in df.iterrows():
        raw = str(row.get("hashtags", "")).strip()
        if not raw or raw == "nan":
            continue
        tags = list({t.strip().lower().lstrip("#") for t in raw.split(",") if t.strip()})
        tags = [t for t in tags if t]
        var = str(row.get("variable_name", ""))

        for tag in tags:
            hashtag_posts[tag] += 1
            hashtag_variables[tag][var] += 1

        for a, b in combinations(sorted(tags), 2):
            cooccur[(a, b)] += 1

    # edges
    edges = pd.DataFrame(
        [{"hashtag_a": a, "hashtag_b": b, "weight": w}
         for (a, b), w in cooccur.items() if w >= MIN_COOCCURRENCE]
    ).sort_values("weight", ascending=False).reset_index(drop=True)

    # nodes
    nodes = pd.DataFrame([
        {
            "hashtag":     tag,
            "total_posts": count,
            "variable_top": max(hashtag_variables[tag], key=hashtag_variables[tag].get),
        }
        for tag, count in hashtag_posts.items() if count >= MIN_POSTS
    ]).sort_values("total_posts", ascending=False).reset_index(drop=True)

    edges.to_csv(OUT_EDGES, index=False)
    nodes.to_csv(OUT_NODES, index=False)

    print(f"[NODES] {len(nodes)} hashtags (min_posts={MIN_POSTS})")
    print(f"[EDGES] {len(edges)} co-occurrences (min={MIN_COOCCURRENCE})")
    print(f"\nTop 10 hashtags:")
    print(nodes.head(10)[["hashtag","total_posts","variable_top"]].to_string(index=False))
    print(f"\nOutput:")
    print(f"  {OUT_EDGES}")
    print(f"  {OUT_NODES}")


if __name__ == "__main__":
    main()
