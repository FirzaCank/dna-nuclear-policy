"""
STEP 5 - SNA MENTION NETWORK
==============================
Builds actor-actor edges from @mentions in Instagram captions.
Each post where user A mentions user B = directed edge A→B.
Edge weight = number of times A mentioned B.

Input : output/socmed_cleaned.csv
Output: output/socmed_edges_mention.csv   (source, target, weight)
        output/socmed_nodes_actors.csv    (username, followers, post_count, is_verified, n_posts, n_mentions_made, n_mentions_received)
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

ROOT      = Path(__file__).parent.parent.parent.parent
IG_DIR    = ROOT / "data" / "processed" / "instagram"
INPUT     = IG_DIR / "socmed_cleaned.csv"
OUT_EDGES = IG_DIR / "socmed_edges_mention.csv"
OUT_NODES = IG_DIR / "socmed_nodes_actors.csv"

MIN_WEIGHT = 1  # minimum mentions to include edge


def main():
    df = pd.read_csv(INPUT)
    print(f"[INPUT] {len(df)} posts, {df['username'].nunique()} unique actors")

    # build edges: poster → mentioned_user
    edge_counts = defaultdict(int)

    for _, row in df.iterrows():
        source = str(row.get("username", "")).strip().lower()
        mentions_raw = str(row.get("mentions", "")).strip()
        if not source or not mentions_raw or mentions_raw == "nan":
            continue
        targets = [m.strip().lower().lstrip("@") for m in mentions_raw.split(",") if m.strip()]
        for target in targets:
            if target and target != source:
                edge_counts[(source, target)] += 1

    edges = pd.DataFrame(
        [{"source": s, "target": t, "weight": w} for (s, t), w in edge_counts.items() if w >= MIN_WEIGHT]
    ).sort_values("weight", ascending=False).reset_index(drop=True)

    # build nodes from socmed_cleaned profile data
    profile_cols = ["username", "followers_count", "following_count", "post_count", "is_verified", "is_business", "biography"]
    available = [c for c in profile_cols if c in df.columns]
    nodes = df[available].drop_duplicates("username").copy()
    nodes["username_lower"] = nodes["username"].str.lower()

    # enrich with post count per actor and mention stats
    post_counts = df.groupby(df["username"].str.lower()).size().rename("n_posts")
    mentions_made = edges.groupby("source")["weight"].sum().rename("n_mentions_made")
    mentions_received = edges.groupby("target")["weight"].sum().rename("n_mentions_received")

    nodes = nodes.merge(post_counts, left_on="username_lower", right_index=True, how="left")
    nodes = nodes.merge(mentions_made, left_on="username_lower", right_index=True, how="left")
    nodes = nodes.merge(mentions_received, left_on="username_lower", right_index=True, how="left")
    nodes.drop(columns=["username_lower"], inplace=True)
    nodes.fillna({"n_posts": 0, "n_mentions_made": 0, "n_mentions_received": 0}, inplace=True)

    edges.to_csv(OUT_EDGES, index=False)
    nodes.to_csv(OUT_NODES, index=False)

    print(f"[EDGES] {len(edges)} mention edges (min_weight={MIN_WEIGHT})")
    print(f"[NODES] {len(nodes)} actors")
    print(f"\nTop 10 most-mentioned:")
    print(edges.groupby("target")["weight"].sum().sort_values(ascending=False).head(10).to_string())
    print(f"\nOutput:")
    print(f"  {OUT_EDGES}")
    print(f"  {OUT_NODES}")


if __name__ == "__main__":
    main()
