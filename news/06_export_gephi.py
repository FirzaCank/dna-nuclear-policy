"""
STEP 6 - GEPHI EXPORT
======================
Prepares files ready to import into Gephi for formal/academic DNA visualization.

Gephi requires:
  - Node table: Id, Label, + attributes
  - Edge table: Source, Target, Type, Weight, + attributes

Output:
  output/gephi/nodes_actors_gephi.csv       → import as "Node table"
  output/gephi/nodes_concepts_gephi.csv     → import as "Node table" (merge)
  output/gephi/edges_actor_concept_gephi.csv → import as "Edge table"
  output/gephi/edges_actor_actor_gephi.csv   → import as "Edge table"
  output/gephi/all_nodes_gephi.csv          → combined actors+concepts (single import)
  output/gephi/GEPHI_GUIDE.txt              → step-by-step import guide

How to import into Gephi:
  1. File > Import Spreadsheet
  2. Import edges_actor_concept_gephi.csv as Edge Table
  3. Gephi will auto-create nodes from Source/Target columns
  4. (Optional) Import all_nodes_gephi.csv as Node Table for attribute enrichment
  5. Layout: ForceAtlas2 or Fruchterman-Reingold
  6. Appearance: Color nodes by 'dominant_pos', size by 'n_statements'
"""

import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).parent.parent
OUTDIR      = ROOT / "output"
GEPHI_DIR   = OUTDIR / "gephi"
GEPHI_DIR.mkdir(exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
nodes_actors   = pd.read_csv(OUTDIR / "02_nodes_actors.csv")
nodes_concepts = pd.read_csv(OUTDIR / "03_nodes_concepts.csv")
edges_ac       = pd.read_csv(OUTDIR / "04_edges_actor_concept.csv")
edges_aa       = pd.read_csv(OUTDIR / "05_edges_actor_actor.csv")

print(f"[INPUT] {len(nodes_actors)} aktor | {len(nodes_concepts)} konsep")
print(f"        {len(edges_ac)} actor→concept edges | {len(edges_aa)} actor→actor edges")


# ── 1. NODES: ACTORS ──────────────────────────────────────────────────────────
# Gephi requires: Id, Label
# Convention: prefix "A::" untuk aktor agar tidak bentrok dengan konsep
actors_gephi = nodes_actors.copy()
actors_gephi.insert(0, "Id",    "A::" + actors_gephi["actor"].astype(str))
actors_gephi.insert(1, "Label", actors_gephi["actor"])
actors_gephi.insert(2, "node_type", "actor")
# Rename dominant_pos → color_group untuk mudah di Gephi
actors_gephi["color_group"] = actors_gephi["dominant_pos"]

out_actors = GEPHI_DIR / "nodes_actors_gephi.csv"
actors_gephi.to_csv(out_actors, index=False)
print(f"  → {out_actors} ({len(actors_gephi)} nodes)")


# ── 2. NODES: CONCEPTS ────────────────────────────────────────────────────────
concepts_gephi = nodes_concepts.copy()
concepts_gephi.insert(0, "Id",    "C::" + concepts_gephi["concept"].astype(str))
concepts_gephi.insert(1, "Label", concepts_gephi["concept"])
concepts_gephi.insert(2, "node_type", "concept")
concepts_gephi["actor_type"]    = "CONCEPT"
concepts_gephi["dominant_pos"]  = concepts_gephi.apply(
    lambda r: "PRO" if r.get("pro_ratio", 0) >= 0.6
    else ("KONTRA" if r.get("kontra_ratio", 0) >= 0.6 else "MIXED"),
    axis=1
)
concepts_gephi["color_group"]   = concepts_gephi["dominant_pos"]
concepts_gephi["n_statements_actor"] = concepts_gephi.get("n_statements", 0)

out_concepts = GEPHI_DIR / "nodes_concepts_gephi.csv"
concepts_gephi.to_csv(out_concepts, index=False)
print(f"  → {out_concepts} ({len(concepts_gephi)} nodes)")


# ── 3. NODES: ALL (gabungan untuk 1x import) ──────────────────────────────────
KEEP_ACTOR = ["Id", "Label", "node_type", "actor_type", "n_statements", "n_articles",
              "pro_count", "kontra_count", "netral_count", "dominant_pos", "color_group", "variables"]
KEEP_CONCEPT = ["Id", "Label", "node_type", "n_statements", "n_actors", "n_articles",
                "pro_ratio", "kontra_ratio", "dominant_pos", "color_group", "variables"]

all_nodes = pd.concat([
    actors_gephi[[c for c in KEEP_ACTOR   if c in actors_gephi.columns]],
    concepts_gephi[[c for c in KEEP_CONCEPT if c in concepts_gephi.columns]],
], ignore_index=True).fillna("")

out_all = GEPHI_DIR / "all_nodes_gephi.csv"
all_nodes.to_csv(out_all, index=False)
print(f"  → {out_all} ({len(all_nodes)} nodes total)")


# ── 4. EDGES: ACTOR → CONCEPT ─────────────────────────────────────────────────
# Gephi requires: Source, Target, (Type: Directed/Undirected), Weight
edges_ac_gephi = edges_ac.copy()
edges_ac_gephi["Source"]    = "A::" + edges_ac_gephi["source"].astype(str)
edges_ac_gephi["Target"]    = "C::" + edges_ac_gephi["target"].astype(str)
edges_ac_gephi["Type"]      = "Directed"
edges_ac_gephi["Weight"]    = edges_ac_gephi["weight"]
edges_ac_gephi["Label"]     = edges_ac_gephi["position"]
# Drop original cols, keep enriched
out_cols = ["Source", "Target", "Type", "Weight", "Label",
            "position", "variable", "avg_confidence", "edge_type"]
edges_ac_gephi = edges_ac_gephi[[c for c in out_cols if c in edges_ac_gephi.columns]]

out_edges_ac = GEPHI_DIR / "edges_actor_concept_gephi.csv"
edges_ac_gephi.to_csv(out_edges_ac, index=False)
print(f"  → {out_edges_ac} ({len(edges_ac_gephi)} edges)")


# ── 5. EDGES: ACTOR → ACTOR ───────────────────────────────────────────────────
if len(edges_aa) > 0:
    edges_aa_gephi = edges_aa.copy()
    edges_aa_gephi["Source"] = "A::" + edges_aa_gephi["source"].astype(str)
    edges_aa_gephi["Target"] = "A::" + edges_aa_gephi["target"].astype(str)
    edges_aa_gephi["Type"]   = "Undirected"
    edges_aa_gephi["Weight"] = edges_aa_gephi["shared_concepts"]
    edges_aa_gephi["Label"]  = edges_aa_gephi["shared_concepts"].astype(str) + " shared concepts"
    out_cols_aa = ["Source", "Target", "Type", "Weight", "Label",
                   "shared_concepts", "agreement", "edge_type"]
    edges_aa_gephi = edges_aa_gephi[[c for c in out_cols_aa if c in edges_aa_gephi.columns]]

    out_edges_aa = GEPHI_DIR / "edges_actor_actor_gephi.csv"
    edges_aa_gephi.to_csv(out_edges_aa, index=False)
    print(f"  → {out_edges_aa} ({len(edges_aa_gephi)} edges)")
else:
    print("  [SKIP] edges_actor_actor kosong — jalankan full run di 03_build_edgelist.py")


# ── 6. GEPHI GUIDE ────────────────────────────────────────────────────────────
guide = """
=======================================================
PANDUAN IMPORT KE GEPHI — DNA Kebijakan Nuklir Indonesia
=======================================================

LANGKAH 1 — Import Edge List (DNA Bipartite):
  File > Import Spreadsheet
  → Pilih: edges_actor_concept_gephi.csv
  → Separator: Comma
  → Charset: UTF-8
  → Graph Type: Directed
  → Centang: "Create missing nodes"
  → Klik Next > Finish

LANGKAH 2 — Enrich Nodes (opsional tapi direkomendasikan):
  File > Import Spreadsheet
  → Pilih: all_nodes_gephi.csv
  → Import as: Node Table
  → Strategy: Merge (bukan Replace)
  → Klik Finish

LANGKAH 3 — Layout:
  Untuk DNA bipartite:
    Layout > ForceAtlas 2
    → Scaling: 10.0
    → Edge Weight Influence: 1.0
    → Run sampai stabil, lalu Stop

  Alternatif: Fruchterman-Reingold (lebih rapi untuk sedikit nodes)

LANGKAH 4 — Appearance (Warna & Ukuran):
  Nodes — Color:
    → Attribute: color_group (PRO/KONTRA/MIXED/NETRAL)
    → PRO    = #66bb6a (hijau)
    → KONTRA = #ef5350 (merah)
    → NETRAL/MIXED = #9e9e9e (abu)

  Nodes — Size:
    → Attribute: n_statements
    → Min size: 5, Max size: 30

  Edges — Color:
    → Attribute: position
    → PRO    = #66bb6a
    → KONTRA = #ef5350
    → NETRAL = #bdbdbd

  Nodes — Shape:
    → node_type = "actor"   → Circle
    → node_type = "concept" → Square (via Gephi plugin atau manual partition)

LANGKAH 5 — Label:
  Nodes > Show Node Labels
  Font: 8–10pt
  Centang: Label adjust (hindari overlap)

LANGKAH 6 — Filter (opsional):
  Untuk hanya tampilkan aktor dengan ≥2 pernyataan:
    Filters > Attributes > Range > n_statements ≥ 2

LANGKAH 7 — Export:
  File > Export > SVG/PDF  (untuk publikasi)
  File > Export > PNG      (untuk laporan)

KOLOM PENTING:
  Nodes:
    - Id           : unique identifier (A:: = aktor, C:: = konsep)
    - Label        : nama tampil di graph
    - node_type    : "actor" atau "concept"
    - actor_type   : INDIVIDU / INSTITUSI / CONCEPT
    - n_statements : jumlah pernyataan (untuk ukuran node)
    - color_group  : PRO/KONTRA/NETRAL/MIXED (untuk warna)
    - variables    : variabel DNA (pipe-separated)

  Edges:
    - Source    : node aktor (A::...)
    - Target    : node konsep (C::...) atau aktor lain
    - Weight    : jumlah co-occurrence
    - position  : PRO / KONTRA / NETRAL
    - variable  : tema/variabel DNA

=======================================================
"""

guide_path = GEPHI_DIR / "GEPHI_GUIDE.txt"
guide_path.write_text(guide, encoding="utf-8")
print(f"  → {guide_path}")

print(f"\n[DONE] Semua file Gephi tersimpan di {GEPHI_DIR}/")
print("  Import pertama: edges_actor_concept_gephi.csv → sebagai Edge Table")
