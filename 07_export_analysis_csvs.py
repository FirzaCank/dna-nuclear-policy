"""
STEP 7 - ANALYSIS HELPER EXPORTS
==================================
Generates two supplementary CSVs for manual review:

1. output/excluded_actors.csv
   - Actors filtered out from the DNA graph and why
   - Reasons: too few statements (<MIN_STATEMENTS) and/or not mappable to institution

2. output/actor_detail.csv
   - Full actor list with: institution guess, meaning/expansion, notes
   - Highlights ambiguous actors like "Pemerintah", "Indonesia", "PSLH UGM"

Input : output/01_flat_statements.csv
        output/02_nodes_actors.csv
        output/05c_edges_actor_keyword.csv
"""

import pandas as pd
from pathlib import Path
from config.institution_mapping import get_institution
from config.actor_notes import get_notes

OUTDIR = Path("output")
MIN_STATEMENTS = 3

# ── Load data ─────────────────────────────────────────────────────────────────
nodes_actors = pd.read_csv(OUTDIR / "02_nodes_actors.csv")
flat_df      = pd.read_csv(OUTDIR / "01_flat_statements.csv")

# ── Apply institution mapping ─────────────────────────────────────────────────
nodes_actors["institution_mapped"] = nodes_actors.apply(
    lambda r: get_institution(r["actor"], r.get("actor_type",""), r.get("actor_role","")), axis=1
)

# ── Actor notes ───────────────────────────────────────────────────────────────
nodes_actors["notes"] = nodes_actors["actor"].apply(get_notes)

# ════════════════════════════════════════════════════════════════
# CSV 1: EXCLUDED ACTORS
# ════════════════════════════════════════════════════════════════
nodes_actors["below_min_statements"] = nodes_actors["n_statements"] < MIN_STATEMENTS
nodes_actors["no_institution_mapped"] = nodes_actors["institution_mapped"].isna()

excluded = nodes_actors[
    nodes_actors["below_min_statements"] | nodes_actors["no_institution_mapped"]
].copy()

excluded["exclusion_reason"] = excluded.apply(lambda r: " | ".join([
    x for x in [
        f"< {MIN_STATEMENTS} statements" if r["below_min_statements"] else "",
        "no institution mapping" if r["no_institution_mapped"] else "",
    ] if x
]), axis=1)

excluded_out = excluded[[
    "actor", "actor_type", "actor_role", "n_statements", "n_articles",
    "dominant_pos", "institution_mapped", "exclusion_reason", "notes"
]].sort_values(["exclusion_reason", "n_statements"], ascending=[True, False])

excluded_out.to_csv(OUTDIR / "excluded_actors.csv", index=False)
print(f"[CSV 1] excluded_actors.csv → {len(excluded_out)} actors excluded")
print(f"        - Below min statements only: {excluded['below_min_statements'].sum()}")
print(f"        - No institution mapping only: {(~excluded['below_min_statements'] & excluded['no_institution_mapped']).sum()}")
print(f"        - Both: {(excluded['below_min_statements'] & excluded['no_institution_mapped']).sum()}")

# ════════════════════════════════════════════════════════════════
# CSV 2: ACTOR DETAIL (ALL actors with explanation)
# ════════════════════════════════════════════════════════════════

# Count statements per actor per source_url to get unique articles
url_per_actor = flat_df.groupby("actor")["source_url"].nunique().reset_index()
url_per_actor.columns = ["actor", "n_unique_urls"]

actor_detail = nodes_actors.merge(url_per_actor, on="actor", how="left")

actor_detail["in_graph"] = (
    (actor_detail["n_statements"] >= MIN_STATEMENTS) &
    (actor_detail["institution_mapped"].notna())
)

# Ambiguous actors flag
AMBIGUOUS_NAMES = ["pemerintah", "indonesia", "negara", "masyarakat", "publik",
                   "akademisi", "pakar", "pengamat", "tokoh"]
actor_detail["is_ambiguous"] = actor_detail["actor"].str.lower().apply(
    lambda x: any(amb in x for amb in AMBIGUOUS_NAMES)
)

actor_detail_out = actor_detail[[
    "actor", "actor_type", "actor_role", "n_statements", "n_unique_urls",
    "dominant_pos", "pro_count", "kontra_count", "netral_count",
    "institution_mapped", "in_graph", "is_ambiguous", "notes"
]].sort_values("n_statements", ascending=False)

actor_detail_out.to_csv(OUTDIR / "actor_detail.csv", index=False)
print(f"\n[CSV 2] actor_detail.csv → {len(actor_detail_out)} total actors")
print(f"        - In graph: {actor_detail_out['in_graph'].sum()}")
print(f"        - Ambiguous: {actor_detail_out['is_ambiguous'].sum()}")

# ════════════════════════════════════════════════════════════════
# Summary: statements (2084) vs unique concepts (explain)
# ════════════════════════════════════════════════════════════════
print("\n=== STATEMENTS vs CONCEPTS ===")
print(f"Total statements (rows in 01_flat_statements):  {len(flat_df)}")
print(f"Unique source articles (source_id):              {flat_df['source_id'].nunique()}")
print(f"Unique source URLs:                              {flat_df['source_url'].nunique()}")
print(f"Unique keywords/concepts (before merge):         {flat_df['keyword'].nunique()}")
print(f"Unique keywords/concepts (after merge):          {flat_df['keyword'].replace({'RUU EBET DIM':'RUU EBET','RUU EBET PP 40 2025 harmonisasi':'RUU EBET','panja EBET nuklir':'RUU EBET','DIM nuklir fraksi sidang':'RUU EBET','just transition nuklir Indonesia':'just transition nuklir','PLTU nuklir just transition':'just transition nuklir'}).nunique()}")
print(f"Unique concepts (concept col):                   {flat_df['concept'].nunique()}")
print(f"Unique actors:                                   {flat_df['actor'].nunique()}")
print()
print("NOTE: '1893 konsep' likely = unique (actor, keyword) pairs, not raw row count.")
print("      Each statement = 1 row. An actor can make multiple statements about same keyword.")
print("      Each article can contain many statements from different actors.")
