"""
STEP 5 — Facebook DNA Analysis Dashboard
==========================================
Input : output/socmed/facebook/facebook_extracted_raw.jsonl
        output/socmed/facebook/facebook_sentiment.csv  (partial OK)
        output/socmed/facebook/facebook_cleaned.csv
Output: output/facebook_report.html
        output/facebook_network_fb.html

Run: source venv/bin/activate && python socmed/05_visualize_facebook.py
"""

import json
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent.parent
FB_DIR  = ROOT / "data" / "processed" / "facebook"
OUTDIR  = ROOT / "data" / "processed" / "facebook"
OUTPUT  = OUTDIR / "facebook_report.html"

C = {
    "pro":      "#69db7c",
    "kontra":   "#ff6b6b",
    "netral":   "#ced4da",
    "concept":  "#d4a6f7",
    "accent":   "#b197fc",
    "info":     "#4dabf7",
    "txt1":     "#e8e8e8",
    "txt2":     "#c9d1d9",
    "bg":       "#0f0f1a",
    "card":     "#1e1e2e",
    "card2":    "#16213e",
    "border":   "#2e3250",
    "hdr_from": "#1a237e",
    "hdr_to":   "#311b92",
}

# ── Load data ─────────────────────────────────────────────────────────────────
rows_ext = []
ext_path = FB_DIR / "facebook_extracted_raw.jsonl"
if ext_path.exists():
    with open(ext_path) as f:
        for line in f:
            rows_ext.append(json.loads(line))
df_ext = pd.DataFrame(rows_ext) if rows_ext else pd.DataFrame()

sent_path = FB_DIR / "facebook_sentiment.csv"
has_sent  = sent_path.exists()
if has_sent:
    df_sent = pd.read_csv(sent_path).dropna(subset=["sentiment"])
    sent_n, sent_total = len(df_sent), len(pd.read_csv(FB_DIR / "facebook_cleaned.csv"))
    print(f"[SENTIMENT] {sent_n}/{sent_total} scored")
else:
    df_sent = pd.DataFrame()
    sent_n = sent_total = 0
    print("[SENTIMENT] not available")

df_clean = pd.read_csv(FB_DIR / "facebook_cleaned.csv")
print(f"[EXTRACTED] {len(df_ext)} records")

def fmt_num(n):
    try:
        n = int(n)
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.0f}K"
        return str(n)
    except: return "–"

def dominant_pos(row):
    m = max(row.get("PRO",0), row.get("KONTRA",0), row.get("NETRAL",0))
    if m == 0: return "NETRAL"
    if row.get("PRO",0) == m: return "PRO"
    if row.get("KONTRA",0) == m: return "KONTRA"
    return "NETRAL"

def pos_color(p):
    return {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(p, C["netral"])

def parse_concepts(val):
    if isinstance(val, list): return [c.strip().lower() for c in val if c.strip()]
    if isinstance(val, str):
        try: return [c.strip().lower() for c in json.loads(val) if c.strip()]
        except: return []
    return []

# ── Stats ─────────────────────────────────────────────────────────────────────
n_pro    = int((df_ext["position"] == "PRO").sum())    if len(df_ext) else 0
n_kontra = int((df_ext["position"] == "KONTRA").sum()) if len(df_ext) else 0
n_netral = int((df_ext["position"] == "NETRAL").sum()) if len(df_ext) else 0
n_posts  = len(df_ext)
n_actors = df_ext["username"].nunique() if len(df_ext) else 0
total_likes = int(df_ext["like_count"].sum()) if "like_count" in df_ext.columns else 0

n_pos = n_neg = n_neu = 0
avg_sent = 0.5
if has_sent and len(df_sent):
    n_pos    = int((df_sent["sentiment"] == "POSITIVE").sum())
    n_neg    = int((df_sent["sentiment"] == "NEGATIVE").sum())
    n_neu    = int((df_sent["sentiment"] == "NEUTRAL").sum())
    avg_sent = float(df_sent["sentiment_score"].mean())

# ── Variable distribution ─────────────────────────────────────────────────────
var_data = {"labels":[], "pro":[], "kontra":[], "netral":[]}
if len(df_ext):
    var_pos = df_ext.groupby(["variable_name","position"]).size().unstack(fill_value=0).reset_index()
    for col in ["PRO","KONTRA","NETRAL"]:
        if col not in var_pos.columns: var_pos[col] = 0
    var_pos["total"] = var_pos["PRO"] + var_pos["KONTRA"] + var_pos["NETRAL"]
    var_pos = var_pos.sort_values("total", ascending=False)
    var_data = {
        "labels": var_pos["variable_name"].tolist(),
        "pro":    var_pos["PRO"].tolist(),
        "kontra": var_pos["KONTRA"].tolist(),
        "netral": var_pos["NETRAL"].tolist(),
    }

# ── Keyword distribution ──────────────────────────────────────────────────────
kw_counts = df_clean["keyword"].value_counts().head(20)
kw_data = {"labels": kw_counts.index.tolist(), "counts": kw_counts.tolist()}

# ── Top concepts ──────────────────────────────────────────────────────────────
concept_counts = defaultdict(int)
for _, row in df_ext.iterrows():
    for c in parse_concepts(row.get("concepts",[])):
        concept_counts[c] += 1
top_concepts = sorted(concept_counts.items(), key=lambda x: -x[1])[:25]
concept_data = {"labels":[c for c,_ in top_concepts], "counts":[n for _,n in top_concepts]}

# ── Top actors ────────────────────────────────────────────────────────────────
actor_stance = df_ext.groupby(["username","position"]).size().unstack(fill_value=0).reset_index() if len(df_ext) else pd.DataFrame()
if len(actor_stance):
    for col in ["PRO","KONTRA","NETRAL"]:
        if col not in actor_stance.columns: actor_stance[col] = 0
    actor_stance["total"] = actor_stance["PRO"] + actor_stance["KONTRA"] + actor_stance["NETRAL"]

    like_by_user = df_ext.groupby("username")["like_count"].sum().reset_index(name="total_likes") if "like_count" in df_ext.columns else pd.DataFrame(columns=["username","total_likes"])
    actor_stance = actor_stance.merge(like_by_user, on="username", how="left").sort_values("total", ascending=False).head(20)

    actor_rows_html = ""
    for _, r in actor_stance.iterrows():
        dp = dominant_pos({"PRO":r["PRO"],"KONTRA":r["KONTRA"],"NETRAL":r["NETRAL"]})
        actor_rows_html += (
            f'<tr>'
            f'<td><a href="https://www.facebook.com/{r["username"]}" target="_blank" '
            f'style="color:{C["accent"]};text-decoration:none;">{r["username"]}</a></td>'
            f'<td style="text-align:center;">{fmt_num(r.get("total_likes",0))}</td>'
            f'<td style="text-align:center;">{int(r["total"])}</td>'
            f'<td style="text-align:center;color:{C["pro"]};">{int(r["PRO"])}</td>'
            f'<td style="text-align:center;color:{C["kontra"]};">{int(r["KONTRA"])}</td>'
            f'<td style="text-align:center;color:{C["netral"]};">{int(r["NETRAL"])}</td>'
            f'<td style="text-align:center;color:{pos_color(dp)};font-weight:700;">{dp}</td>'
            f'</tr>\n'
        )
else:
    actor_rows_html = '<tr><td colspan="7" style="text-align:center;color:#888;">Belum ada data</td></tr>'

# ── SNA mention network ───────────────────────────────────────────────────────
def build_mention_edges(df_clean_slice):
    edge_count = defaultdict(int)
    for _, row in df_clean_slice.dropna(subset=["mentions"]).iterrows():
        src = str(row["username"]).strip()
        targets = [t.strip() for t in str(row["mentions"]).split(",") if t.strip()]
        for tgt in targets:
            if tgt and tgt != src:
                edge_count[(src, tgt)] += 1
    return [(s, t, w) for (s,t), w in sorted(edge_count.items(), key=lambda x: -x[1])]

def build_network_html(edges, actor_stance_map, out_path):
    try:
        from pyvis.network import Network
    except ImportError:
        out_path.write_text("<p style='color:#aaa;padding:20px'>pip install pyvis</p>")
        return
    edges_top = sorted(edges, key=lambda x: -x[2])[:80]
    all_nodes  = set(n for s,t,_ in edges_top for n in (s,t))
    net = Network(height="600px", width="100%", bgcolor="#0f0f1a", directed=True, notebook=False)
    net.set_options(json.dumps({
        "physics": {"forceAtlas2Based": {"gravitationalConstant":-200,"springLength":200,"springConstant":0.05,"damping":0.9},"solver":"forceAtlas2Based","stabilization":{"enabled":True,"iterations":300,"fit":True}},
        "edges": {"smooth":{"type":"curvedCW","roundness":0.15},"arrows":{"to":{"enabled":True,"scaleFactor":0.5}}},
        "interaction": {"hover":True,"dragNodes":True},
    }))
    for node in all_nodes:
        stance = actor_stance_map.get(node, "NETRAL")
        col = {"PRO":C["pro"],"KONTRA":C["kontra"]}.get(stance, C["netral"])
        net.add_node(node, label=f"@{node}", color={"background":col,"border":col},
                     shape="dot", size=20, title=f"@{node} | {stance}",
                     font={"color":"#ffffff","size":13,"strokeWidth":2,"strokeColor":"#000000"})
    for s, t, w in edges_top:
        col = {"PRO":C["pro"],"KONTRA":C["kontra"]}.get(actor_stance_map.get(s,"NETRAL"), C["netral"])
        net.add_edge(s, t, width=max(1,min(8,w)), color=col, title=f"{s}→{t} | n={w}")
    net.save_graph(str(out_path))

actor_stance_map = {}
if len(actor_stance):
    for _, r in actor_stance.iterrows():
        actor_stance_map[r["username"]] = dominant_pos({"PRO":r["PRO"],"KONTRA":r["KONTRA"],"NETRAL":r["NETRAL"]})

edges = build_mention_edges(df_clean)
net_path = OUTDIR / "facebook_network_fb.html"
build_network_html(edges, actor_stance_map, net_path)
print(f"[NETWORK] {len(edges)} mention edges")

sent_note = f"({sent_n}/{sent_total} post terskor)" if has_sent else "(belum tersedia)"

ALL_DATA = {
    "n_posts":   n_posts,
    "n_actors":  n_actors,
    "n_pro":     n_pro,
    "n_kontra":  n_kontra,
    "n_netral":  n_netral,
    "n_pos":     n_pos,
    "n_neg":     n_neg,
    "n_neu":     n_neu,
    "avg_sent":  round(avg_sent, 3),
    "total_likes": total_likes,
    "var":       var_data,
    "kw":        kw_data,
    "concepts":  concept_data,
}
ALL_DATA_JSON = json.dumps(ALL_DATA, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DNA — Facebook Kebijakan Nuklir Indonesia</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{C['bg']};color:{C['txt1']};line-height:1.5}}
a{{color:inherit}}
.tab-nav{{background:#161622;border-bottom:2px solid {C['border']};display:flex;gap:2px;padding:0 48px}}
.tab-link{{color:{C['txt2']};padding:11px 22px;text-decoration:none;border-bottom:3px solid transparent;font-size:0.9rem;font-weight:700;letter-spacing:0.5px;margin-bottom:-2px;transition:color .15s;display:inline-block;}}
.tab-link:hover{{color:{C['txt1']}}}
.tab-active{{color:{C['accent']};border-bottom-color:{C['accent']}}}
.header{{background:linear-gradient(135deg,{C['hdr_from']},{C['hdr_to']});padding:28px 48px}}
.header h1{{font-size:1.85rem;color:#fff;letter-spacing:-0.5px}}
.header p{{color:{C['txt2']};margin-top:6px;font-size:0.95rem}}
.container{{max-width:1400px;margin:0 auto;padding:28px 48px}}
.stats-row{{display:grid;grid-template-columns:repeat(8,1fr);gap:14px;margin-bottom:28px}}
.stat-card{{background:{C['card']};border-radius:12px;padding:18px 12px;text-align:center;border:1px solid {C['border']}}}
.stat-card .number{{font-size:1.9rem;font-weight:700;color:{C['accent']}}}
.stat-card .slabel{{font-size:0.78rem;color:{C['txt2']};margin-top:5px;line-height:1.3}}
.section{{background:{C['card']};border-radius:12px;padding:22px;margin-bottom:22px;border:1px solid {C['border']}}}
.section h2{{font-size:1.1rem;color:{C['concept']};margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid {C['border']};font-weight:600}}
.chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
canvas{{max-height:320px}}
.tbl{{width:100%;border-collapse:collapse;font-size:0.88rem}}
.tbl th{{color:{C['txt2']};font-weight:600;padding:8px 12px;border-bottom:1px solid {C['border']};text-align:left}}
.tbl td{{padding:7px 12px;border-bottom:1px solid {C['border']}40;color:{C['txt1']}}}
.tbl tr:hover td{{background:{C['card2']}}}
.net-legend{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;font-size:0.82rem}}
.leg{{display:flex;align-items:center;gap:6px;color:{C['txt2']}}}
.dot{{width:11px;height:11px;border-radius:50%;flex-shrink:0}}
.note{{color:{C['txt2']};font-size:0.8rem;margin-top:4px;font-style:italic}}
@media(max-width:900px){{
  .chart-row{{grid-template-columns:1fr}}
  .stats-row{{grid-template-columns:repeat(2,1fr)}}
  .container,.header,.tab-nav{{padding:16px 20px}}
}}
</style>
</head>
<body>

<div class="header">
  <h1>Discourse Network Analysis — Facebook</h1>
  <p>Kebijakan Energi Nuklir Indonesia · Analisis Konten Facebook</p>
</div>

<nav class="tab-nav">
  <a href="report_dna.html" class="tab-link">BERITA NASIONAL</a>
  <a href="socmed_report.html" class="tab-link">INSTAGRAM</a>
  <a href="youtube_report.html" class="tab-link">YOUTUBE</a>
  <a href="facebook_report.html" class="tab-link tab-active">FACEBOOK</a>
  <a href="twitter_report.html" class="tab-link">TWITTER/X</a>
</nav>

<div class="container">

<div class="stats-row">
  <div class="stat-card"><div class="number" id="statPosts">{n_posts}</div><div class="slabel">Total Post</div></div>
  <div class="stat-card"><div class="number" id="statActors">{n_actors}</div><div class="slabel">Akun Unik</div></div>
  <div class="stat-card"><div class="number" style="color:{C['pro']};">{n_pro}</div><div class="slabel">PRO Nuklir</div></div>
  <div class="stat-card"><div class="number" style="color:{C['kontra']};">{n_kontra}</div><div class="slabel">KONTRA Nuklir</div></div>
  <div class="stat-card"><div class="number" style="color:{C['netral']};">{n_netral}</div><div class="slabel">NETRAL</div></div>
  <div class="stat-card"><div class="number">{fmt_num(total_likes)}</div><div class="slabel">Total Likes</div></div>
  <div class="stat-card"><div class="number" style="color:{C['info']};">{n_pos}</div><div class="slabel">Sentimen Positif</div></div>
  <div class="stat-card"><div class="number">{round(avg_sent,2)}</div><div class="slabel">Rata-rata Skor Sentimen</div></div>
</div>

<div class="section">
  <h2>Distribusi Sikap &amp; Sentimen <span class="note">{sent_note}</span></h2>
  <div class="chart-row">
    <div><canvas id="chartStance"></canvas></div>
    <div><canvas id="chartSentiment"></canvas></div>
  </div>
</div>

<div class="section">
  <h2>Distribusi Variabel Diskursus</h2>
  <canvas id="chartVar" style="max-height:340px;"></canvas>
</div>

<div class="section">
  <h2>Distribusi per Keyword Pencarian</h2>
  <canvas id="chartKw" style="max-height:400px;"></canvas>
</div>

<div class="section">
  <h2>Top 20 Akun berdasarkan Jumlah Post</h2>
  <table class="tbl">
    <thead><tr>
      <th>Akun</th><th>Total Likes</th><th>Post</th>
      <th style="color:{C['pro']};">PRO</th>
      <th style="color:{C['kontra']};">KONTRA</th>
      <th style="color:{C['netral']};">NETRAL</th>
      <th>Dominan</th>
    </tr></thead>
    <tbody>{actor_rows_html}</tbody>
  </table>
</div>

<div class="section">
  <h2>Social Network Analysis — Jaringan Mention</h2>
  <div class="net-legend">
    <span class="leg"><span class="dot" style="background:{C['pro']};"></span>PRO</span>
    <span class="leg"><span class="dot" style="background:{C['kontra']};"></span>KONTRA</span>
    <span class="leg"><span class="dot" style="background:{C['netral']};"></span>NETRAL</span>
    <span style="color:{C['txt2']};font-size:0.82rem;">Node = akun Facebook · Edge = mention dalam post</span>
  </div>
  <iframe src="facebook_network_fb.html"
    style="width:100%;height:620px;border:none;border-radius:8px;background:{C['bg']};"></iframe>
</div>

</div>

<script>
const D = {ALL_DATA_JSON};
const PRO_C="{C['pro']}",KON_C="{C['kontra']}",NET_C="{C['netral']}",
      POS_C="{C['info']}",ACC_C="{C['accent']}",TXT1="{C['txt1']}",
      TXT2="{C['txt2']}",BORDER="{C['border']}";
const TICK={{color:TXT2,font:{{size:11}}}},GRID={{color:BORDER}},LEG={{labels:{{color:TXT1}},position:'bottom'}};

new Chart(document.getElementById('chartStance'),{{
  type:'doughnut',
  data:{{labels:['PRO','KONTRA','NETRAL'],datasets:[{{data:[D.n_pro,D.n_kontra,D.n_netral],backgroundColor:[PRO_C,KON_C,NET_C],borderWidth:0}}]}},
  options:{{plugins:{{legend:LEG,title:{{display:true,text:'Sikap terhadap Nuklir/PLTN',color:TXT1,font:{{size:14}}}}}},cutout:'62%'}},
}});
new Chart(document.getElementById('chartSentiment'),{{
  type:'doughnut',
  data:{{labels:['POSITIVE','NEGATIVE','NEUTRAL'],datasets:[{{data:[D.n_pos,D.n_neg,D.n_neu],backgroundColor:[POS_C,KON_C,NET_C],borderWidth:0}}]}},
  options:{{plugins:{{legend:LEG,title:{{display:true,text:'Distribusi Sentimen Post',color:TXT1,font:{{size:14}}}}}},cutout:'62%'}},
}});
new Chart(document.getElementById('chartVar'),{{
  type:'bar',
  data:{{labels:D.var.labels,datasets:[
    {{label:'PRO',data:D.var.pro,backgroundColor:PRO_C,stack:'a',borderRadius:2}},
    {{label:'KONTRA',data:D.var.kontra,backgroundColor:KON_C,stack:'a',borderRadius:2}},
    {{label:'NETRAL',data:D.var.netral,backgroundColor:NET_C,stack:'a',borderRadius:2}},
  ]}},
  options:{{indexAxis:'y',responsive:true,plugins:{{legend:LEG}},scales:{{x:{{stacked:true,ticks:TICK,grid:GRID}},y:{{stacked:true,ticks:{{color:TXT2,font:{{size:11}}}}}}}}}},
}});
new Chart(document.getElementById('chartKw'),{{
  type:'bar',
  data:{{labels:D.kw.labels,datasets:[{{label:'Post',data:D.kw.counts,backgroundColor:ACC_C,borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:TICK,grid:GRID}},y:{{ticks:{{color:TXT2,font:{{size:11}}}}}}}}}},
}});
</script>
</body>
</html>"""

OUTPUT.write_text(HTML, encoding="utf-8")
print(f"\n[DONE] {OUTPUT}")
print(f"  posts={n_posts}, actors={n_actors}, PRO={n_pro}, KONTRA={n_kontra}, NETRAL={n_netral}")
print(f"  mention edges={len(edges)}")
