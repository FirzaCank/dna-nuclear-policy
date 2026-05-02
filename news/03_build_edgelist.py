"""
STEP 3 - BUILD EDGE LISTS & ANALYSIS TABLES
=============================================
Input : output/extracted_raw.jsonl
Output:
  output/01_flat_statements.csv       → all statements in flat format (for sentiment)
  output/02_nodes_actors.csv          → actor node list for SNA/DNA
  output/03_nodes_concepts.csv        → concept/discourse node list
  output/04_edges_actor_concept.csv   → bipartite edge list (main DNA)
  output/05_edges_actor_actor.csv     → co-concept actor similarity (SNA)
  output/05b_edges_actor_variable.csv → actor-to-variable aggregated edges
  output/05c_edges_actor_keyword.csv  → actor-to-keyword edges (for visualization)
  output/06a_summary_by_variable.csv  → position distribution per variable
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "output" / "extracted_raw.jsonl"
OUTDIR = ROOT / "output"
OUTDIR.mkdir(exist_ok=True)

# ── Scope: variables included in analysis ─────────────────────────────────────
EXCLUDED_VARS = ["Subordinasi Oposisi", "Sinkronisasi Regulasi"]

# ── Source of truth ───────────────────────────────────────────────────────────
# If stakeholders have reviewed & edited the CSV, place it at:
#   input/flat_statements_reviewed.csv
# Pipeline will use it directly (skip JSONL re-parsing).
# If the file does not exist, pipeline parses from extracted_raw.jsonl as usual.
REVIEWED_FILE = ROOT / "input" / "flat_statements_reviewed.csv"

if REVIEWED_FILE.exists():
    print(f"[SOURCE] Using reviewed CSV: {REVIEWED_FILE}")
    df = pd.read_csv(REVIEWED_FILE, dtype={"source_id": str})
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[~df["variable"].isin(EXCLUDED_VARS)].copy()
    # ── Filter: hanya ambil data dari 20 Oktober 2014 ke atas ─────────────────
    cutoff_date = pd.Timestamp('2014-10-20')
    n_before_filter = len(df)
    df = df[df['date'] >= cutoff_date].copy()
    n_after_filter = len(df)
    print(f"[DATE FILTER] Filtered dari {n_before_filter} → {n_after_filter} statements (cutoff: {cutoff_date.date()})")
    print(f"[STATEMENTS] {len(df)} statements from {df['actor'].nunique()} unique actors")
else:
    # ── Load JSONL ────────────────────────────────────────────────────────────
    TEST_MODE = False   # Set False untuk full run
    TEST_LIMIT = 10

    records = []
    with open(INPUT) as f:
        for line in f:
            if TEST_MODE and len(records) >= TEST_LIMIT:
                break
            try:
                records.append(json.loads(line.strip()))
            except:
                pass

    if TEST_MODE:
        print(f"[TEST MODE] Hanya membaca {TEST_LIMIT} baris pertama")

    print(f"[INPUT] {len(records)} records from {INPUT}")
    print("  First 3 records:")
    for r in records[:3]:
        print(f"    source_id={r.get('source_id')} | actor={r.get('actor')} | position={r.get('position')} | concept={str(r.get('concept',''))[:50]}")

    # ── Flatten to one row per statement ──────────────────────────────────────
    rows = []
    for rec in records:
        if rec.get('actor') is None:  # sentinel row for empty articles
            continue
        rows.append({
            "source_id"    : rec['source_id'],
            "variable"     : rec['variable'],
            "keyword"      : rec.get('keyword', ''),
            "source_url"   : rec['source'],
            "date"         : rec['date'],
            "actor"        : rec.get('actor', '').strip(),
            "actor_type"   : rec.get('actor_type', ''),
            "actor_role"   : rec.get('actor_role', ''),
            "statement"    : rec.get('statement', ''),
            "concept"      : rec.get('concept', '').strip(),
            "position"     : rec.get('position', 'NETRAL'),
            "evidence_type": rec.get('evidence_type', ''),
            "confidence"   : float(rec.get('confidence', 0.5)),
        })

    df = pd.DataFrame(rows)
    df = df[df['actor'].str.len() > 1]  # drop empty actors
    df = df[~df['variable'].isin(EXCLUDED_VARS)].copy()  # scope to 7 variables

    # ── Apply manual corrections ──────────────────────────────────────────────
    CORRECTIONS_FILE = ROOT / "input" / "manual_corrections.csv"
    if CORRECTIONS_FILE.exists():
        corr = pd.read_csv(CORRECTIONS_FILE, dtype=str).dropna(subset=["source_id","actor","action"])
        corr["source_id"] = corr["source_id"].astype(str).str.strip()
        df["source_id"]   = df["source_id"].astype(str).str.strip()
        n_before = len(df)
        for _, c in corr.iterrows():
            mask = (df["source_id"] == c["source_id"]) & (df["actor"] == c["actor"])
            if pd.notna(c.get("concept","")) and str(c["concept"]).strip():
                mask &= df["concept"] == c["concept"]
            if c["action"] == "delete":
                df = df[~mask].copy()
            elif c["action"] == "change" and pd.notna(c.get("field")) and pd.notna(c.get("new_value")):
                df.loc[mask, c["field"]] = c["new_value"]
        n_after = len(df)
        print(f"[CORRECTIONS] Applied {len(corr)} corrections: {n_before - n_after} deleted, {len(corr) - (n_before - n_after)} changed")
    else:
        print("[CORRECTIONS] No manual_corrections.csv found — skipping")

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    cutoff_date = pd.Timestamp('2014-10-20')
    n_before_filter = len(df)
    df = df[df['date'] >= cutoff_date].copy()
    n_after_filter = len(df)
    print(f"[DATE FILTER] Filtered dari {n_before_filter} → {n_after_filter} statements (cutoff: {cutoff_date.date()})")

    print(f"[STATEMENTS] {len(df)} statements from {df['actor'].nunique()} unique actors")
    print("  First 3 rows:")
    print(df[['source_id','actor','concept','position','confidence']].head(3).to_string(index=False))

# ── 1. FLAT STATEMENTS (input for sentiment analysis) ──────────────────────────────
flat_path = OUTDIR / "01_flat_statements.csv"
df.to_csv(flat_path, index=False)
print(f"  → {flat_path}")


# ── 2. NODE LIST: ACTORS ──────────────────────────────────────────────────────
actor_stats = df.groupby('actor').agg(
    actor_type   =('actor_type',    lambda x: x.mode().iloc[0] if len(x) else ''),
    actor_role   =('actor_role',    lambda x: x.mode().iloc[0] if len(x) else ''),
    n_statements =('statement',     'count'),
    n_articles   =('source_id',     'nunique'),
    variables    =('variable',      lambda x: '|'.join(sorted(set(x)))),
    pro_count    =('position',      lambda x: (x=='PRO').sum()),
    kontra_count =('position',      lambda x: (x=='KONTRA').sum()),
    netral_count =('position',      lambda x: (x=='NETRAL').sum()),
    dominant_pos =('position',      lambda x: x.mode().iloc[0] if len(x) else 'NETRAL'),
).reset_index()

actor_nodes_path = OUTDIR / "02_nodes_actors.csv"
actor_stats.to_csv(actor_nodes_path, index=False)
print(f"  → {actor_nodes_path} ({len(actor_stats)} actors)")
print("  First 3 actors:")
print(actor_stats[['actor','actor_type','n_statements','dominant_pos']].head(3).to_string(index=False))

# ── Export: flat statements for stakeholder review (actors ≥ MIN_STATEMENTS) ──
MIN_STATEMENTS = 3
active_actors = set(actor_stats[actor_stats["n_statements"] >= MIN_STATEMENTS]["actor"])
df_review = df[df["actor"].isin(active_actors)].copy()
review_path = OUTDIR / "flat_statements_for_review.csv"
df_review.to_csv(review_path, index=False)
print(f"  → {review_path} ({len(df_review)} rows, {df_review['actor'].nunique()} actors with ≥{MIN_STATEMENTS} statements)")


# ── 3. NODE LIST: CONCEPTS ────────────────────────────────────────────────────
concept_stats = df.groupby('concept').agg(
    n_statements =('statement',     'count'),
    n_actors     =('actor',         'nunique'),
    n_articles   =('source_id',     'nunique'),
    variables    =('variable',      lambda x: '|'.join(sorted(set(x)))),
    pro_ratio    =('position',      lambda x: (x=='PRO').mean().round(3)),
    kontra_ratio =('position',      lambda x: (x=='KONTRA').mean().round(3)),
).reset_index()
concept_stats = concept_stats.sort_values('n_statements', ascending=False)

concept_nodes_path = OUTDIR / "03_nodes_concepts.csv"
concept_stats.to_csv(concept_nodes_path, index=False)
print(f"  → {concept_nodes_path} ({len(concept_stats)} concepts)")
print("  First 3 concepts:")
print(concept_stats[['concept','n_statements','n_actors','pro_ratio']].head(3).to_string(index=False))


# ── 4. EDGE LIST: ACTOR → CONCEPT (DNA bipartite) ───────────────────────────────────────
# Aggregate per actor-concept pair (weight = co-occurrence count)
edge_ac = df.groupby(['actor', 'concept', 'position', 'variable']).agg(
    weight       =('source_id',   'count'),
    avg_confidence=('confidence', 'mean'),
).reset_index()
edge_ac.columns = ['source', 'target', 'position', 'variable', 'weight', 'avg_confidence']
edge_ac['edge_type'] = 'actor_concept'

ac_path = OUTDIR / "04_edges_actor_concept.csv"
edge_ac.to_csv(ac_path, index=False)
print(f"  → {ac_path} ({len(edge_ac)} edges)")
print("  First 3 actor→concept edges:")
print(edge_ac[['source','target','position','weight']].head(3).to_string(index=False))


# ── 5. EDGE LIST: ACTOR → ACTOR (SNA — shared concept co-occurrence) ───────────────────
# Two actors are connected if they share the same concept in the same context
from itertools import combinations

actor_concept_sets = df.groupby('actor')['concept'].apply(set)
actor_pairs = []

actors = actor_concept_sets.index.tolist()
for a1, a2 in combinations(actors, 2):
    shared = actor_concept_sets[a1] & actor_concept_sets[a2]
    if shared:
        # Posisi masing-masing aktor untuk shared concepts
        pos_a1 = df[df['actor']==a1].set_index('concept')['position']
        pos_a2 = df[df['actor']==a2].set_index('concept')['position']

        shared_with_pos = []
        for c in shared:
            p1 = pos_a1.get(c, 'NETRAL')
            p2 = pos_a2.get(c, 'NETRAL')
            if isinstance(p1, pd.Series): p1 = p1.iloc[0]
            if isinstance(p2, pd.Series): p2 = p2.iloc[0]
            shared_with_pos.append((c, p1, p2))

        # Agreement: kedua aktor punya posisi sama
        agree = sum(1 for _, p1, p2 in shared_with_pos if p1 == p2)

        actor_pairs.append({
            "source"         : a1,
            "target"         : a2,
            "shared_concepts": len(shared),
            "shared_list"    : '|'.join(shared),
            "agreement"      : agree,
            "weight"         : len(shared),
            "edge_type"      : "actor_actor",
        })

edge_aa = pd.DataFrame(actor_pairs)
if len(edge_aa):
    edge_aa = edge_aa.sort_values('shared_concepts', ascending=False)

aa_path = OUTDIR / "05_edges_actor_actor.csv"
edge_aa.to_csv(aa_path, index=False)
print(f"  → {aa_path} ({len(edge_aa)} edges)")
if len(edge_aa):
    print("  First 3 actor→actor edges:")
    print(edge_aa[['source','target','shared_concepts','agreement']].head(3).to_string(index=False))


# ── 5b. EDGE LIST: ACTOR → VARIABLE (aggregated — used for main visualization) ─────────────
edge_av = df.groupby(['actor', 'variable']).agg(
    weight        =('source_id',   'count'),
    pro_count     =('position',    lambda x: (x=='PRO').sum()),
    kontra_count  =('position',    lambda x: (x=='KONTRA').sum()),
    netral_count  =('position',    lambda x: (x=='NETRAL').sum()),
    avg_confidence=('confidence',  'mean'),
).reset_index()
edge_av['dominant_pos'] = edge_av.apply(
    lambda r: 'PRO' if r['pro_count'] >= r['kontra_count'] and r['pro_count'] >= r['netral_count']
    else ('KONTRA' if r['kontra_count'] >= r['pro_count'] and r['kontra_count'] >= r['netral_count']
    else 'NETRAL'), axis=1
)
edge_av.columns = ['source', 'target', 'weight', 'pro_count', 'kontra_count',
                   'netral_count', 'avg_confidence', 'position']
edge_av['edge_type'] = 'actor_variable'

av_path = OUTDIR / "05b_edges_actor_variable.csv"
edge_av.to_csv(av_path, index=False)
print(f"  → {av_path} ({len(edge_av)} edges, {edge_av['target'].nunique()} variabel)")
print("  Sample 3 edges actor→variable:")
print(edge_av[['source','target','position','weight']].head(3).to_string(index=False))

# ── 5c. EDGE LIST: ACTOR → KEYWORD (DNA meso — ~50 keywords) ──────────────────
edge_ak = df.groupby(['actor', 'keyword']).agg(
    weight        =('source_id',   'count'),
    pro_count     =('position',    lambda x: (x=='PRO').sum()),
    kontra_count  =('position',    lambda x: (x=='KONTRA').sum()),
    netral_count  =('position',    lambda x: (x=='NETRAL').sum()),
    avg_confidence=('confidence',  'mean'),
    variable      =('variable',    lambda x: x.mode().iloc[0]),
).reset_index()
edge_ak['dominant_pos'] = edge_ak.apply(
    lambda r: 'PRO' if r['pro_count'] >= r['kontra_count'] and r['pro_count'] >= r['netral_count']
    else ('KONTRA' if r['kontra_count'] >= r['pro_count'] and r['kontra_count'] >= r['netral_count']
    else 'NETRAL'), axis=1
)
edge_ak.rename(columns={'dominant_pos': 'position', 'actor': 'source'}, inplace=True)
edge_ak['edge_type'] = 'actor_keyword'

ak_path = OUTDIR / "05c_edges_actor_keyword.csv"
edge_ak.to_csv(ak_path, index=False)
print(f"  → {ak_path} ({len(edge_ak)} edges, {edge_ak['keyword'].nunique()} keyword unik)")
print("  Sample 3 edges actor→keyword:")
print(edge_ak[['source','keyword','position','weight']].head(3).to_string(index=False))


# 6a. Per actor + variable (high-level)
summary_var = df.pivot_table(
    index=['actor', 'variable'],
    columns='position',
    values='source_id',
    aggfunc='count',
    fill_value=0
).reset_index()

summary_var_path = OUTDIR / "06a_summary_by_variable.csv"
summary_var.to_csv(summary_var_path, index=False)
print(f"  → {summary_var_path} ({len(summary_var)} baris)")
print("  Sample 3 baris:")
print(summary_var.head(3).to_string(index=False))

# 6b. Per actor + keyword (tema scraping)
summary_kw = df.pivot_table(
    index=['actor', 'keyword'],
    columns='position',
    values='source_id',
    aggfunc='count',
    fill_value=0
).reset_index()

summary_kw_path = OUTDIR / "06b_summary_by_keyword.csv"
summary_kw.to_csv(summary_kw_path, index=False)
print(f"  → {summary_kw_path} ({len(summary_kw)} baris)")
print("  Sample 3 baris:")
print(summary_kw.head(3).to_string(index=False))

# 6c. Per actor + concept (granular — posisi aktor per isu spesifik)
summary_concept = df.groupby(['actor', 'concept', 'position']).agg(
    n=('source_id', 'count'),
    avg_confidence=('confidence', 'mean'),
).reset_index().sort_values(['actor', 'n'], ascending=[True, False])

summary_concept_path = OUTDIR / "06c_summary_by_concept.csv"
summary_concept.to_csv(summary_concept_path, index=False)
print(f"  → {summary_concept_path} ({len(summary_concept)} baris)")
print("  Sample 3 baris:")
print(summary_concept[['actor','concept','position','n']].head(3).to_string(index=False))


# ── 7. PRINT SUMMARY STATS ────────────────────────────────────────────────────
print("\n" + "="*55)
print("RINGKASAN HASIL EKSTRAKSI")
print("="*55)
print(f"Total pernyataan  : {len(df)}")
print(f"Aktor unik        : {df['actor'].nunique()}")
print(f"Konsep unik       : {df['concept'].nunique()}")
print(f"\nDistribusi POSISI:")
print(df['position'].value_counts().to_string())
print(f"\nTop 15 Aktor (by n_statements):")
print(actor_stats.nlargest(15, 'n_statements')[['actor','actor_type','n_statements','dominant_pos']].to_string(index=False))
print(f"\nTop 15 Konsep (by n_statements):")
print(concept_stats.head(15)[['concept','n_statements','n_actors','pro_ratio','kontra_ratio']].to_string(index=False))
print("\n[DONE] Semua file tersimpan di output/")
print("Import ke Gephi: 04_edges_actor_concept.csv (bipartite) atau 05_edges_actor_actor.csv")
