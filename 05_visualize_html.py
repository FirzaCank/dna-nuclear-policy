"""
STEP 5 - HTML STAKEHOLDER REPORT
==================================
Generates a single self-contained interactive HTML report containing:
  1. DNA Bipartite Network (pyvis) — Institution → Keyword, embedded as base64 iframe
  2. Position distribution per variable (stacked bar chart)
  3. Top actors by statement count (horizontal bar)
  4. Sentiment distribution (donut chart)
  5. Sentiment × Position cross-tabulation (bar chart)
  6. Article trend per month by position (stacked bar chart)
  7. Actor type distribution (donut chart)
  8. Top 10 KONTRA actors (horizontal bar)
  9. Statement count per analysis variable (horizontal bar)

Input:
  output/02_nodes_actors.csv
  output/03_nodes_concepts.csv
  output/04_edges_actor_concept.csv
  output/06a_summary_by_variable.csv
  output/07_sentiment_scored.csv

Output:
  output/report_dna.html   (single self-contained file — shareable)
  output/network_dna.html  (standalone network file for reference)

INSTALL:
  pip install pyvis pandas
"""

import pandas as pd
import json
from pathlib import Path
from config.institution_mapping import get_institution
from config.keyword_merge import KEYWORD_MERGE

OUTDIR = Path("output")

# ── Load data ──────────────────────────────────────────────────────────────────
nodes_actors   = pd.read_csv(OUTDIR / "02_nodes_actors.csv")
nodes_concepts = pd.read_csv(OUTDIR / "03_nodes_concepts.csv")
edges_ac       = pd.read_csv(OUTDIR / "04_edges_actor_concept.csv")
edges_av       = pd.read_csv(OUTDIR / "05b_edges_actor_variable.csv")  # actor→variable (~5 node)
edges_ak       = pd.read_csv(OUTDIR / "05c_edges_actor_keyword.csv")   # actor→keyword (~50 node)
summary_var    = pd.read_csv(OUTDIR / "06a_summary_by_variable.csv")
sentiment_df   = pd.read_csv(OUTDIR / "07_sentiment_scored.csv")
flat_df        = pd.read_csv(OUTDIR / "01_flat_statements.csv")
flat_df_all    = flat_df.copy()  # unfiltered — untuk trend artikel

MIN_STATEMENTS = 3   # filter actors: show only those with ≥ N statements

edges_ak["keyword"] = edges_ak["keyword"].replace(KEYWORD_MERGE)

# ── Shared actor filter ────────────────────────────────────────────────────
nodes_actors_filtered = nodes_actors[nodes_actors["n_statements"] >= MIN_STATEMENTS].copy()
nodes_actors_filtered["institution"] = nodes_actors_filtered.apply(
    lambda r: get_institution(r["actor"], r.get("actor_type",""), r.get("actor_role","")), axis=1
)
nodes_actors_filtered = nodes_actors_filtered[nodes_actors_filtered["institution"].notna()]
active_actors = set(nodes_actors_filtered["actor"])
actor_to_inst = dict(zip(nodes_actors_filtered["actor"], nodes_actors_filtered["institution"]))

# ── Apply MIN_STATEMENTS filter to all downstream data ────────────────────────
flat_df      = flat_df[flat_df["actor"].isin(active_actors)].copy()
sentiment_df = sentiment_df[sentiment_df["actor"].isin(active_actors)].copy()

# Stats per institution (shared)
inst_stats = (
    nodes_actors_filtered.groupby("institution")
    .agg(
        n_statements=("n_statements", "sum"),
        pro_count=("pro_count", "sum"),
        kontra_count=("kontra_count", "sum"),
        netral_count=("netral_count", "sum"),
    ).reset_index()
)

# Hitung ambigu_count dari flat_df (sebelum difilter posisi)
_ambigu = (
    flat_df[flat_df["position"] == "AMBIGU"]
    .assign(institution=lambda d: d["actor"].map(actor_to_inst))
    .groupby("institution")
    .size().reset_index(name="ambigu_count")
)
inst_stats = inst_stats.merge(_ambigu, on="institution", how="left")
inst_stats["ambigu_count"] = inst_stats["ambigu_count"].fillna(0).astype(int)
def _dominant_pos(r):
    p, k, n = r["pro_count"], r["kontra_count"], r["netral_count"]
    if p == k and p > 0:          # exact tie PRO vs KONTRA → NETRAL (berimbang)
        return "NETRAL"
    if p >= k and p >= n:
        return "PRO"
    if k >= p and k >= n:
        return "KONTRA"
    return "NETRAL"

inst_stats["dominant_pos"] = inst_stats.apply(_dominant_pos, axis=1)
inst_stats["members"] = inst_stats["institution"].map(
    nodes_actors_filtered.groupby("institution")["actor"].apply(lambda x: ", ".join(sorted(set(x))))
)

def build_edges_net(edges_raw):
    """Aggregate raw edges → institution-level edges_net."""
    ef = edges_raw[edges_raw["source"].isin(active_actors)].copy()
    ef["institution"] = ef["source"].map(actor_to_inst)
    ei = ef.groupby(["institution", "target", "position"])["weight"].sum().reset_index()
    return ei.loc[ei.groupby(["institution", "target"])["weight"].idxmax()].reset_index(drop=True)

# Graph 1: variable (compact) — keyword graph disabled
edges_net_var = build_edges_net(edges_av)

print(f"[INPUT] {len(nodes_actors)} aktor total → {len(nodes_actors_filtered)} aktor (≥{MIN_STATEMENTS} statements)")
print(f"        → {len(inst_stats)} institusi | variable graph: {len(edges_net_var)} edges {edges_net_var['target'].nunique()} nodes")

# ── 1. Pyvis Networks (Graph 1: Keyword detail, Graph 2: Variable compact) ───
FREEZE_JS = """
<script type="text/javascript">
document.addEventListener("DOMContentLoaded", function() {
  var _frozen = false;

  function layoutNodes() {
    if (typeof network === "undefined" || typeof nodes === "undefined") return;
    var allNodes = nodes.get();
    var kwNodes = allNodes.filter(function(n) { return n.group === "concept"; });
    var kwSpacing = 160;
    var kwStartY = -((kwNodes.length - 1) / 2) * kwSpacing;
    nodes.update(kwNodes.map(function(n, i) {
      return { id: n.id, x: 0, y: kwStartY + i * kwSpacing, fixed: { x: true, y: true } };
    }));
    var proNodes    = allNodes.filter(function(n) { return n.group === "inst_pro"; });
    var kontraNodes = allNodes.filter(function(n) { return n.group === "inst_kontra"; });
    var netralNodes = allNodes.filter(function(n) { return n.group === "inst_netral"; });
    var ambiguNodes = allNodes.filter(function(n) { return n.group === "inst_ambigu"; });
    function spreadSide(arr, xBase) {
      var sp = 180, startY = -((arr.length - 1) / 2) * sp;
      return arr.map(function(n, i) {
        return { id: n.id, x: xBase + (Math.random() - 0.5) * 200, y: startY + i * sp };
      });
    }
    nodes.update([].concat(spreadSide(proNodes, -900)).concat(spreadSide(kontraNodes, 900))
      .concat(spreadSide(netralNodes, (Math.random() > 0.5 ? -900 : 900)))
      .concat(spreadSide(ambiguNodes, (Math.random() > 0.5 ? -1200 : 1200))));
  }
  function freezeNetwork() {
    if (_frozen) return; _frozen = true;
    network.setOptions({ physics: { enabled: false } }); network.fit();
  }
  var checkNet = setInterval(function() {
    if (typeof network !== "undefined") {
      clearInterval(checkNet); layoutNodes();
      network.on("stabilizationIterationsDone", freezeNetwork);
      setTimeout(freezeNetwork, 12000);
    }
  }, 100);
});
</script>"""

def build_pyvis_html(edges_net, concept_color, out_path):
    """Build a pyvis network HTML string for given edges_net."""
    from pyvis.network import Network
    import base64
    net = Network(height="1100px", width="100%", bgcolor="#1a1a2e",
                  directed=True, notebook=False)
    net.set_options(json.dumps({
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -250, "springLength": 500,
                "springConstant": 0.04, "damping": 0.9,
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"enabled": True, "iterations": 400, "fit": True},
        },
        "edges": {"smooth": {"type": "curvedCW", "roundness": 0.15}},
        "interaction": {"hover": True, "dragNodes": True},
        "groups": {
            "inst_pro":    {"color": {"background": "#66bb6a", "border": "#66bb6a"}},
            "inst_kontra": {"color": {"background": "#ef5350", "border": "#ef5350"}},
            "inst_netral": {"color": {"background": "#bdbdbd", "border": "#bdbdbd"}},
            "inst_ambigu": {"color": {"background": "#ffd54f", "border": "#ffd54f"}},
            "concept":     {"color": {"background": "#ce93d8", "border": "#ce93d8"}},
        },
    }))
    COLOR_POS = {"PRO": "#66bb6a", "KONTRA": "#ef5350", "NETRAL": "#bdbdbd", "AMBIGU": "#ffd54f"}
    keyword_degree = edges_net.groupby("target")["institution"].nunique()
    target_nodes = sorted(edges_net["target"].unique(),
                          key=lambda t: keyword_degree.get(t, 0), reverse=True)
    for t in target_nodes:
        deg = int(keyword_degree.get(t, 1))
        net.add_node(f"V::{t}", label=t, color=concept_color, shape="box", size=50,
                    title=f"{t}\nConnected to {deg} institutions", group="concept",
                    font={"color": "#000000", "size": 18, "face": "arial", "bold": True, "strokeWidth": 0})
    active_institutions = set(edges_net["institution"])
    for _, row in inst_stats[inst_stats["institution"].isin(active_institutions)].iterrows():
        dom_pos = str(row.get("dominant_pos", "NETRAL")).strip().upper()
        color = {"PRO": "#66bb6a", "KONTRA": "#ef5350", "NETRAL": "#bdbdbd", "AMBIGU": "#ffd54f"}.get(dom_pos, "#bdbdbd")
        title = (f"{row['institution']}\nTotal pernyataan: {row.get('n_statements',0)}\n"
                f"Posisi dominan: {dom_pos}\n"
                f"PRO: {row.get('pro_count',0)} | KONTRA: {row.get('kontra_count',0)} | NETRAL: {row.get('netral_count',0)} | AMBIGU: {row.get('ambigu_count',0)}\n"
                f"Anggota: {row.get('members','')}")
        group_name = {"PRO": "inst_pro", "KONTRA": "inst_kontra", "AMBIGU": "inst_ambigu"}.get(dom_pos, "inst_netral")
        size = max(14, min(50, int(row.get("n_statements", 1)) * 2))
        node_color = {"background": color, "border": color, "highlight": {"background": color, "border": color}}
        net.add_node(f"A::{row['institution']}", label=row["institution"], color=node_color,
                    shape="dot", size=size, title=title,
                    font={"color": "#ffffff", "size": 16, "strokeWidth": 2, "strokeColor": "#000000"},
                    group=group_name)
    for _, row in edges_net.iterrows():
        color = COLOR_POS.get(str(row.get("position", "NETRAL")), "#bdbdbd")
        net.add_edge(f"A::{row['institution']}", f"V::{row['target']}",
                    color=color, width=max(1, min(8, int(row.get("weight", 1)))),
                    title=f"{row.get('position','')} | n={row.get('weight',1)}")
    net.save_graph(str(out_path))
    with open(out_path, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("</body>", FREEZE_JS + "\n</body>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html

try:
    import base64
    html_var = build_pyvis_html(edges_net_var, "#ce93d8", OUTDIR / "network_dna_var.html")
    b64_var = base64.b64encode(html_var.encode("utf-8")).decode("ascii")
    network_section = f'''
<div id="graph-var" style="display:block"><iframe src="data:text/html;base64,{b64_var}" width="100%" height="1100px" style="border:none;display:block;"></iframe></div>
'''
    network_head = ""
    print("  [OK] Network graph (compact) dibuat → network_dna_var.html")
except ImportError:
    print("  [SKIP] pyvis tidak terinstall — jalankan: pip install pyvis")
    network_section = "<p style='color:#aaa'>Install pyvis untuk network graph: <code>pip install pyvis</code></p>"
    network_head = ""


# ── 2. Chart data (JSON untuk Chart.js — no matplotlib dependency) ────────────

# Bar: posisi per variabel — gunakan flat_df yang sudah difilter (≥MIN_STATEMENTS)
pos_cols = [c for c in summary_var.columns if c in ("PRO", "KONTRA", "NETRAL")]
_summary_var_filtered = flat_df.pivot_table(
    index=["actor", "variable"], columns="position", values="source_id",
    aggfunc="count", fill_value=0
).reset_index()
variables = sorted(flat_df["variable"].unique().tolist())
chart_pos_data = {
    "labels": variables,
    "pro":    [int(_summary_var_filtered[_summary_var_filtered["variable"]==v]["PRO"].sum())    if "PRO"    in _summary_var_filtered.columns else 0 for v in variables],
    "kontra": [int(_summary_var_filtered[_summary_var_filtered["variable"]==v]["KONTRA"].sum()) if "KONTRA" in _summary_var_filtered.columns else 0 for v in variables],
    "netral": [int(_summary_var_filtered[_summary_var_filtered["variable"]==v]["NETRAL"].sum()) if "NETRAL" in _summary_var_filtered.columns else 0 for v in variables],
}

# Bar: top 15 aktor — hanya aktor ≥ MIN_STATEMENTS
top_actors = nodes_actors_filtered.nlargest(15, "n_statements").copy()

def actor_label(row):
    org = get_institution(row["actor"], row.get("actor_type",""), row.get("actor_role",""))
    if org and org.lower() != row["actor"].lower():
        return f"{row['actor']} ({org})"
    return row["actor"]

top_actors["label"] = top_actors.apply(actor_label, axis=1)
chart_actors_data = {
    "labels": top_actors["label"].tolist(),
    "values": top_actors["n_statements"].tolist(),
    "colors": [{"PRO": "#66bb6a", "KONTRA": "#ef5350", "NETRAL": "#bdbdbd"}.get(p, "#4fc3f7")
              for p in top_actors["dominant_pos"].tolist()],
}

# Donut: sentimen
sent_counts = sentiment_df["sentiment_label"].value_counts()
chart_sent_data = {
    "labels": sent_counts.index.tolist(),
    "values": sent_counts.values.tolist(),
}

# Bar: sentimen × posisi
cross = pd.crosstab(sentiment_df["position"], sentiment_df["sentiment_label"]).reset_index()
positions = cross["position"].tolist()
sent_labels = [c for c in cross.columns if c != "position"]
chart_cross_data = {
    "positions": positions,
    "datasets": [{"label": sl, "data": cross[sl].tolist() if sl in cross.columns else []} for sl in sent_labels],
}

# Trend: artikel per bulan — pakai semua data (unfiltered) agar periode awal tidak hilang
flat_df_all["date_parsed"] = pd.to_datetime(flat_df_all["date"], errors="coerce")
flat_df_all["year_month"]  = flat_df_all["date_parsed"].dt.to_period("M").astype(str)
trend = (
    flat_df_all.groupby(["year_month", "position"])["source_url"]
    .nunique().reset_index(name="n_articles")
)
trend_months = sorted(trend["year_month"].dropna().unique().tolist())
trend_pro    = {r["year_month"]: r["n_articles"] for _, r in trend[trend["position"]=="PRO"].iterrows()}
trend_kontra = {r["year_month"]: r["n_articles"] for _, r in trend[trend["position"]=="KONTRA"].iterrows()}
trend_netral = {r["year_month"]: r["n_articles"] for _, r in trend[trend["position"]=="NETRAL"].iterrows()}
chart_trend_data = {
    "labels":  trend_months,
    "pro":     [trend_pro.get(m, 0)    for m in trend_months],
    "kontra":  [trend_kontra.get(m, 0) for m in trend_months],
    "netral":  [trend_netral.get(m, 0) for m in trend_months],
}

# Actor type distribution
actor_type_counts = flat_df["actor_type"].value_counts()
chart_actor_type_data = {
    "labels": actor_type_counts.index.tolist(),
    "values": actor_type_counts.values.tolist(),
}

# Top 10 KONTRA aktor — hanya aktor ≥ MIN_STATEMENTS
top_kontra = nodes_actors_filtered[nodes_actors_filtered["kontra_count"] > 0].nlargest(10, "kontra_count").copy()

def short_role(actor, actor_type, actor_role):
    """Ambil nama institusi singkat untuk label kurung."""
    inst = get_institution(actor, actor_type, actor_role)
    if inst:
        return inst
    # fallback: ambil kata kunci dari role
    role_str = str(actor_role) if pd.notna(actor_role) else ""
    for kw in ["IESR","WALHI","JATAM","ICEL","CELIOS","BRIN","ESDM","DPR","DEN","PLN","UGM","ITB","UI","CERAH","Greenpeace","Ekomarin","ReforMiner"]:
        if kw.lower() in role_str.lower():
            return kw
    return None

def kontra_label(row):
    org = short_role(row["actor"], row.get("actor_type",""), row.get("actor_role",""))
    if org and org.lower() != row["actor"].lower():
        return f"{row['actor']} ({org})"
    return row["actor"]

top_kontra["label"] = top_kontra.apply(kontra_label, axis=1)
chart_kontra_data = {
    "labels": top_kontra["label"].tolist(),
    "values": top_kontra["kontra_count"].tolist(),
}

# Statements per variabel
var_counts = flat_df["variable"].value_counts()
chart_var_data = {
    "labels": var_counts.index.tolist(),
    "values": var_counts.values.tolist(),
}

# Stats summary — semua dari data yang sudah difilter ≥ MIN_STATEMENTS
total_stmt    = len(sentiment_df)
total_actors  = len(nodes_actors_filtered["actor"].unique())
total_concepts = nodes_concepts["concept"].nunique()
total_news    = flat_df["source_url"].nunique()
if "position" in sentiment_df.columns:
    _pos_counts = sentiment_df["position"].value_counts()
    _total      = len(sentiment_df)
    _labels     = ["PRO", "KONTRA", "NETRAL", "AMBIGU"]
    _exact      = {k: (_pos_counts.get(k, 0) / _total) * 100 for k in _labels}
    _floors     = {k: int(v) for k, v in _exact.items()}
    _remainders = sorted(_labels, key=lambda k: -(_exact[k] - _floors[k]))
    _leftover   = 100 - sum(_floors.values())
    for k in _remainders[:_leftover]:
        _floors[k] += 1
    pro_pct, kontra_pct, netral_pct, ambigu_pct = (_floors[k] for k in _labels)
else:
    pro_pct = kontra_pct = netral_pct = ambigu_pct = 0


# ── 3. Build HTML ──────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DNA Report — Kebijakan Nuklir Indonesia</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; }}
  .header {{ background: linear-gradient(135deg, #1a237e, #311b92); padding: 32px 48px; }}
  .header h1 {{ font-size: 2rem; color: #fff; }}
  .header p {{ color: #b0bec5; margin-top: 8px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 32px 48px; }}
  .stats-row {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 16px; margin-bottom: 32px; }}
  .stat-card {{ background: #1e1e2e; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #2a2a3e; }}
  .stat-card .number {{ font-size: 2.4rem; font-weight: 700; color: #7c4dff; }}
  .stat-card .label {{ font-size: 0.85rem; color: #90a4ae; margin-top: 4px; }}
  .section {{ background: #1e1e2e; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #2a2a3e; }}
  .section h2 {{ font-size: 1.2rem; color: #ce93d8; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #2a2a3e; }}
  .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; font-size: 0.8rem; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  canvas {{ max-height: 320px; }}
  @media (max-width: 768px) {{ .chart-row {{ grid-template-columns: 1fr; }} .stats-row {{ grid-template-columns: 1fr 1fr; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>Discourse Network Analysis</h1>
  <p>Kebijakan Energi Nuklir Indonesia — Laporan Analisis Wacana Aktor-Konsep</p>
</div>
<div class="container">

  <!-- Stats Row -->
  <div class="stats-row">
    <div class="stat-card"><div class="number">{total_news}</div><div class="label">Total Artikel Berita</div></div>
    <div class="stat-card"><div class="number">{total_stmt}</div><div class="label">Total Pernyataan</div></div>
    <div class="stat-card"><div class="number">{total_actors}</div><div class="label">Aktor Unik</div></div>
    <div class="stat-card"><div class="number">{total_concepts}</div><div class="label">Konsep/Wacana</div></div>
    <div class="stat-card"><div class="number" style="color:#66bb6a">{pro_pct}%</div><div class="label">Pernyataan PRO</div></div>
    <div class="stat-card"><div class="number" style="color:#ef5350">{kontra_pct}%</div><div class="label">Pernyataan KONTRA</div></div>
    <div class="stat-card"><div class="number" style="color:#bdbdbd">{netral_pct}%</div><div class="label">Pernyataan NETRAL (Berimbang)</div></div>
    <div class="stat-card"><div class="number" style="color:#ffa726">{ambigu_pct}%</div><div class="label">Pernyataan AMBIGU (Dua Sisi)</div></div>
  </div>

  <!-- Network -->
  <div class="section">
    <h2>DNA Bipartite Network</h2>
    {network_head}
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#66bb6a"></div>Institusi PRO</div>
      <div class="legend-item"><div class="legend-dot" style="background:#ef5350"></div>Institusi KONTRA</div>
      <div class="legend-item"><div class="legend-dot" style="background:#bdbdbd"></div>Institusi NETRAL (PRO=KONTRA)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#ffd54f"></div>Institusi AMBIGU (pernyataan dua sisi)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#ce93d8"></div>Aktor → 7 Variabel Kebijakan</div>
      <div class="legend-item"><span style="color:#aaa;font-size:0.75rem">— EDGE HIJAU: PRO,   MERAH: KONTRA,   ABU: NETRAL,   KUNING: AMBIGU</span></div>
    </div>
    <div style="width:100%;overflow:hidden;">{network_section}</div>
  </div>

  <!-- Posisi & Top Aktor -->
  <div class="chart-row">
    <div class="section">
      <h2>Distribusi Posisi per Variabel</h2>
      <canvas id="chartPos"></canvas>
    </div>
    <div class="section">
      <h2>Top 15 Aktor by Jumlah Pernyataan</h2>
      <canvas id="chartActors"></canvas>
    </div>
  </div>

  <!-- Sentimen -->
  <div class="chart-row">
    <div class="section">
      <h2>Distribusi Sentimen</h2>
      <canvas id="chartSent"></canvas>
    </div>
    <div class="section">
      <h2>Sentimen × Posisi Aktor</h2>
      <canvas id="chartCross"></canvas>
    </div>
  </div>

  <!-- Trend -->
  <div class="section">
    <h2>Tren Artikel per Bulan (Berdasarkan Posisi)</h2>
    <canvas id="chartTrend" style="max-height:300px;"></canvas>
  </div>

  <!-- Deskriptif tambahan -->
  <div class="chart-row">
    <div class="section">
      <h2>Distribusi Tipe Aktor</h2>
      <canvas id="chartActorType"></canvas>
    </div>
    <div class="section">
      <h2>Top 10 Aktor KONTRA Nuklir</h2>
      <canvas id="chartKontra"></canvas>
    </div>
  </div>


</div>

<script>
const posData = {json.dumps(chart_pos_data)};
const actorsData = {json.dumps(chart_actors_data)};
const sentData = {json.dumps(chart_sent_data)};
const crossData = {json.dumps(chart_cross_data)};
const trendData = {json.dumps(chart_trend_data)};
const actorTypeData = {json.dumps(chart_actor_type_data)};
const kontraData = {json.dumps(chart_kontra_data)};
const varData = {json.dumps(chart_var_data)};

// Chart 1: Posisi per variabel
new Chart(document.getElementById('chartPos'), {{
  type: 'bar',
  data: {{
    labels: posData.labels,
    datasets: [
      {{ label: 'PRO',    data: posData.pro,    backgroundColor: '#66bb6a' }},
      {{ label: 'KONTRA', data: posData.kontra, backgroundColor: '#ef5350' }},
      {{ label: 'NETRAL', data: posData.netral, backgroundColor: '#bdbdbd' }},
    ]
  }},
  options: {{
    responsive: true, plugins: {{ legend: {{ labels: {{ color: '#e0e0e0' }} }} }},
    scales: {{
      x: {{ stacked: true, ticks: {{ color: '#90a4ae', maxRotation: 30 }} }},
      y: {{ stacked: true, ticks: {{ color: '#90a4ae' }} }}
    }}
  }}
}});

// Chart 2: Top aktor
new Chart(document.getElementById('chartActors'), {{
  type: 'bar',
  data: {{
    labels: actorsData.labels,
    datasets: [{{ data: actorsData.values, backgroundColor: actorsData.colors, borderRadius: 4 }}]
  }},
  options: {{
    indexAxis: 'y', responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#90a4ae' }} }},
      y: {{ ticks: {{ color: '#90a4ae', font: {{ size: 10 }} }} }}
    }}
  }}
}});

// Chart 3: Donut sentimen
new Chart(document.getElementById('chartSent'), {{
  type: 'doughnut',
  data: {{
    labels: sentData.labels,
    datasets: [{{ data: sentData.values, backgroundColor: ['#66bb6a','#ef5350','#bdbdbd','#ffb74d'] }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e0e0e0' }} }} }}
  }}
}});

// Chart 4: Sentimen × Posisi
const crossColors = ['#66bb6a','#ef5350','#bdbdbd','#ffb74d'];
new Chart(document.getElementById('chartCross'), {{
  type: 'bar',
  data: {{
    labels: crossData.positions,
    datasets: crossData.datasets.map((ds, i) => ({{
      label: ds.label, data: ds.data,
      backgroundColor: crossColors[i % crossColors.length]
    }}))
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e0e0e0' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#90a4ae' }} }},
      y: {{ ticks: {{ color: '#90a4ae' }} }}
    }}
  }}
}});

// Chart 5: Tren artikel per bulan

new Chart(document.getElementById('chartTrend'), {{
  type: 'bar',
  data: {{
    labels: trendData.labels,
    datasets: [
      {{ label: 'PRO',    data: trendData.pro,    backgroundColor: 'rgba(102,187,106,0.8)', stack: 'a' }},
      {{ label: 'KONTRA', data: trendData.kontra, backgroundColor: 'rgba(239,83,80,0.8)',   stack: 'a' }},
      {{ label: 'NETRAL', data: trendData.netral, backgroundColor: 'rgba(189,189,189,0.6)', stack: 'a' }},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e0e0e0' }} }} }},
    scales: {{
      x: {{ stacked: true, ticks: {{ color: '#90a4ae', maxRotation: 45, font: {{ size: 10 }} }} }},
      y: {{ stacked: true, ticks: {{ color: '#90a4ae' }}, title: {{ display: true, text: 'Jumlah Artikel', color: '#90a4ae' }} }}
    }}
  }}
}});

// Chart 6: Distribusi tipe aktor
new Chart(document.getElementById('chartActorType'), {{
  type: 'doughnut',
  data: {{
    labels: actorTypeData.labels,
    datasets: [{{ data: actorTypeData.values,
      backgroundColor: ['#7c4dff','#4fc3f7','#ffb74d','#66bb6a','#ef5350','#bdbdbd'] }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e0e0e0' }} }} }}
  }}
}});

// Chart 7: Top 10 KONTRA aktor
new Chart(document.getElementById('chartKontra'), {{
  type: 'bar',
  data: {{
    labels: kontraData.labels,
    datasets: [{{ data: kontraData.values, backgroundColor: '#ef5350', borderRadius: 4 }}]
  }},
  options: {{
    indexAxis: 'y', responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#90a4ae' }} }},
      y: {{ ticks: {{ color: '#90a4ae', font: {{ size: 10 }} }} }}
    }}
  }}
}});

// Chart 8: Statements per variabel
</script>
</body>
</html>"""

report_path = OUTDIR / "report_dna.html"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n[OUTPUT] → {report_path}")
print("[DONE] Buka file di browser untuk melihat report")