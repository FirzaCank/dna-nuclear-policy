"""
STEP 4 - BUILD YOUTUBE DNA EDGE LISTS
=======================================
Flatten channel + concepts into actor-concept rows, then build DNA/SNA edges.

Input : output/socmed/youtube/youtube_extracted_raw.jsonl
Output:
  output/socmed/youtube/yt_01_flat_statements.csv       → one row per channel-concept pair
  output/socmed/youtube/yt_02_nodes_channels.csv        → channel node list
  output/socmed/youtube/yt_03_nodes_concepts.csv        → concept node list
  output/socmed/youtube/yt_04_edges_channel_concept.csv → bipartite DNA edge list
  output/socmed/youtube/yt_05_edges_channel_channel.csv → SNA co-concept similarity
  output/socmed/youtube/yt_05b_edges_channel_variable.csv → channel-to-variable aggregated
  output/socmed/youtube/yt_06a_summary_by_variable.csv  → position distribution per variable

Run: source venv/bin/activate && python socmed/04_build_edgelist_youtube.py
"""

import json
import pandas as pd
from itertools import combinations
from pathlib import Path
from collections import defaultdict

ROOT   = Path(__file__).parent.parent
YT_DIR = ROOT / "output" / "socmed" / "youtube"
INPUT  = YT_DIR / "youtube_extracted_raw.jsonl"

rows_raw = []
with open(INPUT) as f:
    for line in f:
        rows_raw.append(json.loads(line))

print(f"[INPUT] {len(rows_raw)} records")

def parse_concepts(val):
    if isinstance(val, list):
        return [c.strip().lower() for c in val if str(c).strip()]
    if isinstance(val, str):
        try:
            lst = json.loads(val)
            return [c.strip().lower() for c in lst if str(c).strip()]
        except Exception:
            return []
    return []

# ── Flatten to one row per channel-concept pair ───────────────────────────────
flat_rows = []
for rec in rows_raw:
    channel   = str(rec.get("channel_title", "")).strip()
    if not channel:
        continue
    concepts  = parse_concepts(rec.get("concepts", []))
    position  = rec.get("position", "NETRAL")
    variable  = str(rec.get("variable_name", "")).strip()
    keyword   = str(rec.get("keyword", "")).strip()
    video_id  = str(rec.get("video_id", "")).strip()
    pub_at    = str(rec.get("published_at", "")).strip()
    view_count= rec.get("view_count", 0)
    sub_count = rec.get("subscriber_count", 0)

    for concept in concepts:
        flat_rows.append({
            "source_id"       : video_id,
            "channel_title"   : channel,
            "channel_id"      : rec.get("channel_id", ""),
            "variable"        : variable,
            "keyword"         : keyword,
            "date"            : pub_at,
            "concept"         : concept,
            "position"        : position,
            "view_count"      : view_count,
            "subscriber_count": sub_count,
        })

df = pd.DataFrame(flat_rows)
df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
df = df[df["concept"].str.len() > 1].copy()

print(f"[FLAT] {len(df)} channel-concept rows | {df['channel_title'].nunique()} channels | {df['concept'].nunique()} concepts")

# ── 1. Flat statements ────────────────────────────────────────────────────────
flat_path = YT_DIR / "yt_01_flat_statements.csv"
df.to_csv(flat_path, index=False)
print(f"  → {flat_path}")

# ── 2. Node list: channels ────────────────────────────────────────────────────
ch_stats = df.groupby("channel_title").agg(
    channel_id      =("channel_id",       lambda x: x.mode().iloc[0] if len(x) else ""),
    n_concepts      =("concept",          "count"),
    n_videos        =("source_id",        "nunique"),
    n_variables     =("variable",         "nunique"),
    variables       =("variable",         lambda x: "|".join(sorted(set(x)))),
    pro_count       =("position",         lambda x: (x=="PRO").sum()),
    kontra_count    =("position",         lambda x: (x=="KONTRA").sum()),
    netral_count    =("position",         lambda x: (x=="NETRAL").sum()),
    dominant_pos    =("position",         lambda x: x.mode().iloc[0] if len(x) else "NETRAL"),
    avg_views       =("view_count",       "mean"),
    max_subscribers =("subscriber_count", "max"),
).reset_index()
ch_stats = ch_stats.sort_values("n_videos", ascending=False)

ch_path = YT_DIR / "yt_02_nodes_channels.csv"
ch_stats.to_csv(ch_path, index=False)
print(f"  → {ch_path} ({len(ch_stats)} channels)")
print("  Top 5:")
print(ch_stats[["channel_title","n_videos","dominant_pos"]].head(5).to_string(index=False))

# ── 3. Node list: concepts ────────────────────────────────────────────────────
concept_stats = df.groupby("concept").agg(
    n_mentions   =("source_id",  "count"),
    n_channels   =("channel_title","nunique"),
    n_videos     =("source_id",  "nunique"),
    variables    =("variable",   lambda x: "|".join(sorted(set(x)))),
    pro_ratio    =("position",   lambda x: round((x=="PRO").mean(), 3)),
    kontra_ratio =("position",   lambda x: round((x=="KONTRA").mean(), 3)),
).reset_index()
concept_stats = concept_stats.sort_values("n_mentions", ascending=False)

concept_path = YT_DIR / "yt_03_nodes_concepts.csv"
concept_stats.to_csv(concept_path, index=False)
print(f"  → {concept_path} ({len(concept_stats)} concepts)")
print("  Top 5:")
print(concept_stats[["concept","n_mentions","n_channels","pro_ratio"]].head(5).to_string(index=False))

# ── 4. Edge list: channel → concept (bipartite DNA) ───────────────────────────
edge_cc = df.groupby(["channel_title","concept","position","variable"]).agg(
    weight=("source_id","count"),
).reset_index()
edge_cc.columns = ["source","target","position","variable","weight"]
edge_cc["edge_type"] = "channel_concept"
edge_cc = edge_cc.sort_values("weight", ascending=False)

cc_path = YT_DIR / "yt_04_edges_channel_concept.csv"
edge_cc.to_csv(cc_path, index=False)
print(f"  → {cc_path} ({len(edge_cc)} edges)")
print("  Top 3 edges:")
print(edge_cc[["source","target","position","weight"]].head(3).to_string(index=False))

# ── 5. Edge list: channel → channel (SNA — shared concept co-occurrence) ──────
ch_concept_sets = df.groupby("channel_title")["concept"].apply(set)
channels_list   = ch_concept_sets.index.tolist()

pairs = []
for a, b in combinations(channels_list, 2):
    shared = ch_concept_sets[a] & ch_concept_sets[b]
    if not shared:
        continue
    pos_a = df[df["channel_title"]==a].set_index("concept")["position"]
    pos_b = df[df["channel_title"]==b].set_index("concept")["position"]
    agree = 0
    for c in shared:
        pa = pos_a.get(c, "NETRAL")
        pb = pos_b.get(c, "NETRAL")
        if isinstance(pa, pd.Series): pa = pa.iloc[0]
        if isinstance(pb, pd.Series): pb = pb.iloc[0]
        if pa == pb:
            agree += 1
    pairs.append({
        "source"         : a,
        "target"         : b,
        "shared_concepts": len(shared),
        "shared_list"    : "|".join(sorted(shared)),
        "agreement"      : agree,
        "weight"         : len(shared),
        "edge_type"      : "channel_channel",
    })

edge_aa = pd.DataFrame(pairs).sort_values("shared_concepts", ascending=False) if pairs else pd.DataFrame()
aa_path = YT_DIR / "yt_05_edges_channel_channel.csv"
edge_aa.to_csv(aa_path, index=False)
print(f"  → {aa_path} ({len(edge_aa)} edges)")
if len(edge_aa):
    print("  Top 3:")
    print(edge_aa[["source","target","shared_concepts","agreement"]].head(3).to_string(index=False))

# ── 5b. Edge list: channel → variable ─────────────────────────────────────────
edge_av = df.groupby(["channel_title","variable"]).agg(
    weight      =("source_id",   "count"),
    pro_count   =("position",    lambda x: (x=="PRO").sum()),
    kontra_count=("position",    lambda x: (x=="KONTRA").sum()),
    netral_count=("position",    lambda x: (x=="NETRAL").sum()),
).reset_index()
edge_av["position"] = edge_av.apply(
    lambda r: "PRO" if r["pro_count"] >= r["kontra_count"] and r["pro_count"] >= r["netral_count"]
    else ("KONTRA" if r["kontra_count"] >= r["pro_count"] and r["kontra_count"] >= r["netral_count"]
    else "NETRAL"), axis=1
)
edge_av.rename(columns={"channel_title":"source","variable":"target"}, inplace=True)
edge_av["edge_type"] = "channel_variable"

av_path = YT_DIR / "yt_05b_edges_channel_variable.csv"
edge_av.to_csv(av_path, index=False)
print(f"  → {av_path} ({len(edge_av)} edges, {edge_av['target'].nunique()} variabel)")

# ── 6a. Summary: position per variable ────────────────────────────────────────
summary_var = df.pivot_table(
    index=["channel_title","variable"],
    columns="position",
    values="source_id",
    aggfunc="count",
    fill_value=0,
).reset_index()
summary_var.to_csv(YT_DIR / "yt_06a_summary_by_variable.csv", index=False)
print(f"  → yt_06a_summary_by_variable.csv ({len(summary_var)} rows)")

# ── Summary stats ─────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("RINGKASAN DNA YOUTUBE")
print("="*55)
print(f"Total channel-concept rows : {len(df)}")
print(f"Channel unik               : {df['channel_title'].nunique()}")
print(f"Konsep unik                : {df['concept'].nunique()}")
print(f"Variabel unik              : {df['variable'].nunique()}")
print(f"\nDistribusi POSISI:")
print(df["position"].value_counts().to_string())
print(f"\nTop 10 Channel (by n_videos):")
print(ch_stats[["channel_title","n_videos","dominant_pos"]].head(10).to_string(index=False))
print(f"\nTop 10 Konsep:")
print(concept_stats[["concept","n_mentions","n_channels","pro_ratio","kontra_ratio"]].head(10).to_string(index=False))
print("\n[DONE] Semua file tersimpan di output/socmed/youtube/")
print("Import ke Gephi: yt_04_edges_channel_concept.csv (bipartite) atau yt_05_edges_channel_channel.csv")
