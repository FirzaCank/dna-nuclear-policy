"""
STEP 5 — Twitter/X DNA Analysis Dashboard
==========================================
Input : data/processed/twitter/twitter_extracted_raw.jsonl
        data/processed/twitter/twitter_sentiment.csv  (partial OK)
        data/processed/twitter/twitter_cleaned.csv
Output: data/processed/twitter/twitter_report.html
        data/processed/twitter/twitter_network_tw_{pid}.html  (per-period)

Run: source venv/bin/activate && python pipelines/socmed/twitter/05_visualize.py
"""

import json
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent.parent
TW_DIR  = ROOT / "data" / "processed" / "twitter"
OUTDIR  = TW_DIR
OUTPUT  = OUTDIR / "twitter_report.html"
TW_DIR.mkdir(parents=True, exist_ok=True)

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

PERIODS = {
    "all":     ("Semua Periode",     None,         None),
    "jokowi1": ("Jokowi Periode 1",  "2014-10-20", "2019-10-20"),
    "jokowi2": ("Jokowi Periode 2",  "2019-10-20", "2024-10-20"),
    "prabowo": ("Prabowo",           "2024-10-20", None),
}
PERIOD_ORDER = ["all", "jokowi1", "jokowi2", "prabowo"]

# ── Load data ─────────────────────────────────────────────────────────────────
rows_ext = []
ext_path = TW_DIR / "twitter_extracted_raw.jsonl"
if ext_path.exists():
    with open(ext_path) as f:
        for line in f:
            rows_ext.append(json.loads(line))
df_ext = pd.DataFrame(rows_ext) if rows_ext else pd.DataFrame()

if len(df_ext) and "pub_date" in df_ext.columns:
    df_ext["pub_date"] = pd.to_datetime(df_ext["pub_date"], errors="coerce")

sent_path = TW_DIR / "twitter_sentiment.csv"
has_sent  = sent_path.exists()
if has_sent:
    df_sent = pd.read_csv(sent_path).dropna(subset=["sentiment"])
    df_sent["pub_date"] = pd.to_datetime(df_sent["pub_date"], errors="coerce")
    sent_n = len(df_sent)
    sent_total = len(pd.read_csv(TW_DIR / "twitter_cleaned.csv"))
    print(f"[SENTIMENT] {sent_n}/{sent_total} scored")
else:
    df_sent = pd.DataFrame()
    sent_n = sent_total = 0
    print("[SENTIMENT] not available")

df_clean = pd.read_csv(TW_DIR / "twitter_cleaned.csv")
df_clean["pub_date"] = pd.to_datetime(df_clean["pub_date"], errors="coerce")
print(f"[EXTRACTED] {len(df_ext)} records")


def _slice_ext(pid):
    if not len(df_ext) or "pub_date" not in df_ext.columns:
        return df_ext
    _, pstart, pend = PERIODS[pid]
    d = df_ext.copy()
    if pstart:
        d = d[d["pub_date"] >= pd.Timestamp(pstart)]
    if pend:
        d = d[d["pub_date"] < pd.Timestamp(pend)]
    return d


def _slice_sent(pid):
    if not has_sent or not len(df_sent):
        return df_sent
    _, pstart, pend = PERIODS[pid]
    d = df_sent.copy()
    if pstart:
        d = d[d["pub_date"] >= pd.Timestamp(pstart)]
    if pend:
        d = d[d["pub_date"] < pd.Timestamp(pend)]
    return d


def _slice_clean(pid):
    _, pstart, pend = PERIODS[pid]
    d = df_clean.copy()
    if pstart:
        d = d[d["pub_date"] >= pd.Timestamp(pstart)]
    if pend:
        d = d[d["pub_date"] < pd.Timestamp(pend)]
    return d


def fmt_num(n):
    try:
        n = int(n)
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.0f}K"
        return str(n)
    except Exception:
        return "–"


def dominant_pos(row):
    m = max(row.get("PRO", 0), row.get("KONTRA", 0), row.get("NETRAL", 0))
    if m == 0:     return "NETRAL"
    if row.get("PRO", 0) == m:     return "PRO"
    if row.get("KONTRA", 0) == m:  return "KONTRA"
    return "NETRAL"


def pos_color(p):
    return {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(p, C["netral"])


def parse_concepts(val):
    if isinstance(val, list): return [c.strip().lower() for c in val if c.strip()]
    if isinstance(val, str):
        try: return [c.strip().lower() for c in json.loads(val) if c.strip()]
        except: return []
    return []


def compute_period_data(pid):
    de = _slice_ext(pid)
    ds = _slice_sent(pid)
    dc = _slice_clean(pid)

    n_pro    = int((de["position"] == "PRO").sum())    if len(de) else 0
    n_kontra = int((de["position"] == "KONTRA").sum()) if len(de) else 0
    n_netral = int((de["position"] == "NETRAL").sum()) if len(de) else 0
    n_tweets = len(de)
    n_actors = de["username"].nunique() if len(de) else 0
    total_fav = int(de["favorite_count"].sum()) if "favorite_count" in de.columns and len(de) else 0

    n_pos = n_neg = n_neu = 0
    avg_sent = 0.5
    if has_sent and len(ds):
        n_pos    = int((ds["sentiment"] == "POSITIVE").sum())
        n_neg    = int((ds["sentiment"] == "NEGATIVE").sum())
        n_neu    = int((ds["sentiment"] == "NEUTRAL").sum())
        avg_sent = float(ds["sentiment_score"].mean())

    # variable distribution
    var_data = {"labels": [], "pro": [], "kontra": [], "netral": []}
    if len(de):
        vp = de.groupby(["variable_name","position"]).size().unstack(fill_value=0).reset_index()
        for col in ["PRO","KONTRA","NETRAL"]:
            if col not in vp.columns: vp[col] = 0
        vp["total"] = vp["PRO"] + vp["KONTRA"] + vp["NETRAL"]
        vp = vp.sort_values("total", ascending=False)
        var_data = {"labels": vp["variable_name"].tolist(), "pro": vp["PRO"].tolist(),
                    "kontra": vp["KONTRA"].tolist(), "netral": vp["NETRAL"].tolist()}

    # keyword distribution
    kw_counts = dc["keyword"].value_counts().head(20) if len(dc) else pd.Series([], dtype=int)
    kw_data = {"labels": kw_counts.index.tolist(), "counts": kw_counts.tolist()}

    # top concepts
    cc = defaultdict(int)
    for _, row in de.iterrows():
        for c in parse_concepts(row.get("concepts", [])):
            cc[c] += 1
    top_c = sorted(cc.items(), key=lambda x: -x[1])[:25]
    concept_data = {"labels": [c for c,_ in top_c], "counts": [n for _,n in top_c]}

    # top actors table
    actor_rows_html = ""
    if len(de):
        as_ = de.groupby(["username","position"]).size().unstack(fill_value=0).reset_index()
        for col in ["PRO","KONTRA","NETRAL"]:
            if col not in as_.columns: as_[col] = 0
        as_["total"] = as_["PRO"] + as_["KONTRA"] + as_["NETRAL"]
        fav_by_user = de.groupby("username")["favorite_count"].sum().reset_index(name="total_fav") if "favorite_count" in de.columns else pd.DataFrame(columns=["username","total_fav"])
        as_ = as_.merge(fav_by_user, on="username", how="left").sort_values("total", ascending=False).head(20)
        for _, r in as_.iterrows():
            dp = dominant_pos({"PRO": r["PRO"], "KONTRA": r["KONTRA"], "NETRAL": r["NETRAL"]})
            actor_rows_html += (
                f'<tr>'
                f'<td><a href="https://twitter.com/{r["username"]}" target="_blank" '
                f'style="color:{C["accent"]};text-decoration:none;">@{r["username"]}</a></td>'
                f'<td style="text-align:center;">{fmt_num(r.get("total_fav",0))}</td>'
                f'<td style="text-align:center;">{int(r["total"])}</td>'
                f'<td style="text-align:center;color:{C["pro"]};">{int(r["PRO"])}</td>'
                f'<td style="text-align:center;color:{C["kontra"]};">{int(r["KONTRA"])}</td>'
                f'<td style="text-align:center;color:{C["netral"]};">{int(r["NETRAL"])}</td>'
                f'<td style="text-align:center;color:{pos_color(dp)};font-weight:700;">{dp}</td>'
                f'</tr>\n'
            )
    if not actor_rows_html:
        actor_rows_html = '<tr><td colspan="7" style="text-align:center;color:#888;">Belum ada data</td></tr>'

    return {
        "n_tweets": n_tweets, "n_actors": n_actors,
        "n_pro": n_pro, "n_kontra": n_kontra, "n_netral": n_netral,
        "n_pos": n_pos, "n_neg": n_neg, "n_neu": n_neu,
        "avg_sent": round(avg_sent, 3), "total_fav": total_fav,
        "var": var_data, "kw": kw_data, "concepts": concept_data,
        "actor_rows_html": actor_rows_html,
    }


# ── Build per-period data + networks ──────────────────────────────────────────
def build_network_html(edges, actor_stance_map, out_path):
    try:
        from pyvis.network import Network
    except ImportError:
        out_path.write_text("<p style='color:#aaa;padding:20px'>pip install pyvis</p>")
        return
    edges_top = sorted(edges, key=lambda x: -x[2])[:80]
    all_nodes = set(n for s, t, _ in edges_top for n in (s, t))
    net = Network(height="600px", width="100%", bgcolor="#0f0f1a", directed=True, notebook=False)
    net.set_options(json.dumps({
        "physics": {"forceAtlas2Based": {"gravitationalConstant": -200, "springLength": 200, "springConstant": 0.05, "damping": 0.9}, "solver": "forceAtlas2Based", "stabilization": {"enabled": True, "iterations": 300, "fit": True}},
        "edges": {"smooth": {"type": "curvedCW", "roundness": 0.15}, "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}}},
        "interaction": {"hover": True, "dragNodes": True},
    }))
    for node in all_nodes:
        stance = actor_stance_map.get(node, "NETRAL")
        col = {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(stance, C["netral"])
        net.add_node(node, label=f"@{node}", color={"background": col, "border": col},
                     shape="dot", size=20, title=f"@{node} | {stance}",
                     font={"color": "#ffffff", "size": 13, "strokeWidth": 2, "strokeColor": "#000000"})
    for s, t, w in edges_top:
        col = {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(actor_stance_map.get(s, "NETRAL"), C["netral"])
        net.add_edge(s, t, width=max(1, min(8, w)), color=col, title=f"{s}→{t} | n={w}")
    net.save_graph(str(out_path))


ALL_PERIODS_DATA = {}
net_paths = {}

for pid in PERIOD_ORDER:
    pdata = compute_period_data(pid)
    ALL_PERIODS_DATA[pid] = pdata

    # build mention network
    de = _slice_ext(pid)
    dc = _slice_clean(pid)
    edge_count = defaultdict(int)
    for _, row in dc.dropna(subset=["user_mentions"]).iterrows():
        src = str(row.get("username", "")).strip()
        for m in str(row["user_mentions"]).split(","):
            m = m.strip()
            if m and m != src:
                edge_count[(src, m)] += 1
    edges = [(s, t, w) for (s, t), w in sorted(edge_count.items(), key=lambda x: -x[1])]

    actor_stance_map = {}
    if len(de):
        as_ = de.groupby(["username","position"]).size().unstack(fill_value=0).reset_index()
        for col in ["PRO","KONTRA","NETRAL"]:
            if col not in as_.columns: as_[col] = 0
        for _, r in as_.iterrows():
            actor_stance_map[r["username"]] = dominant_pos({"PRO": r["PRO"], "KONTRA": r["KONTRA"], "NETRAL": r["NETRAL"]})

    net_path = OUTDIR / f"twitter_network_tw_{pid}.html"
    build_network_html(edges, actor_stance_map, net_path)
    net_paths[pid] = net_path.name
    print(f"[NETWORK:{pid}] tweets={pdata['n_tweets']}, actors={pdata['n_actors']}, edges={len(edges)}")


# ── Precompute actor rows per period as JSON ──────────────────────────────────
actor_rows_by_period = {pid: ALL_PERIODS_DATA[pid].pop("actor_rows_html") for pid in PERIOD_ORDER}
ALL_DATA_JSON = json.dumps(ALL_PERIODS_DATA, ensure_ascii=False)

# init display from "all"
D = ALL_PERIODS_DATA["all"]


HTML = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DNA — Twitter/X Kebijakan Nuklir Indonesia</title>
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
.period-bar{{display:flex;gap:10px;margin-bottom:24px;flex-wrap:wrap;align-items:center}}
.period-btn{{padding:7px 18px;border-radius:20px;border:1px solid {C['border']};background:{C['card']};color:{C['txt2']};cursor:pointer;font-size:0.85rem;font-weight:600;transition:all .15s}}
.period-btn:hover,.period-btn.active{{background:{C['accent']};color:#fff;border-color:{C['accent']}}}
.stats-row{{display:grid;grid-template-columns:repeat(8,1fr);gap:14px;margin-bottom:28px}}
.stat-card{{background:{C['card']};border-radius:12px;padding:18px 12px;text-align:center;border:1px solid {C['border']}}}
.stat-card .number{{font-size:1.9rem;font-weight:700;color:{C['accent']}}}
.stat-card .slabel{{font-size:0.78rem;color:{C['txt2']};margin-top:5px;line-height:1.3}}
.section{{background:{C['card']};border-radius:12px;padding:22px;margin-bottom:22px;border:1px solid {C['border']}}}
.section h2{{font-size:1.1rem;color:{C['concept']};margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid {C['border']};font-weight:600}}
.charts-2{{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:22px}}
.chart-box{{background:{C['card']};border-radius:12px;padding:22px;border:1px solid {C['border']}}}
.chart-box h2{{font-size:1.1rem;color:{C['concept']};margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid {C['border']};font-weight:600}}
.network-frame{{width:100%;height:620px;border:none;border-radius:8px;background:{C['bg']}}}
table{{width:100%;border-collapse:collapse;font-size:0.88rem}}
th{{text-align:left;padding:10px 12px;color:{C['txt2']};font-weight:600;border-bottom:1px solid {C['border']};font-size:0.8rem;text-transform:uppercase;letter-spacing:0.5px}}
td{{padding:9px 12px;border-bottom:1px solid {C['border']}20}}
tr:hover td{{background:{C['card2']}}}
@media(max-width:900px){{.stats-row{{grid-template-columns:repeat(4,1fr)}}.charts-2{{grid-template-columns:1fr}}.container,.header,.tab-nav{{padding:16px 20px}}}}
</style>
</head>
<body>

<nav class="tab-nav">
  <a href="report_dna.html" class="tab-link">BERITA NASIONAL</a>
  <a href="socmed_report.html" class="tab-link">INSTAGRAM</a>
  <a href="youtube_report.html" class="tab-link">YOUTUBE</a>
  <a href="facebook_report.html" class="tab-link">FACEBOOK</a>
  <a href="twitter_report.html" class="tab-link tab-active">TWITTER/X</a>
</nav>

<div class="header">
  <h1>Discourse Network Analysis — Twitter/X</h1>
  <p>Kebijakan Energi Nuklir Indonesia | {D['n_tweets']:,} tweets &bull; {D['n_actors']:,} akun unik &bull; 18 keyword / 7 variabel</p>
</div>

<div class="container">

<div class="period-bar">
  <span style="color:{C['txt2']};font-size:0.85rem;font-weight:600;">Periode:</span>
  <button class="period-btn active" data-pid="all">Semua</button>
  <button class="period-btn" data-pid="jokowi1">Jokowi I</button>
  <button class="period-btn" data-pid="jokowi2">Jokowi II</button>
  <button class="period-btn" data-pid="prabowo">Prabowo</button>
</div>

<div class="stats-row">
  <div class="stat-card"><div class="number" id="st-tweets">{D['n_tweets']:,}</div><div class="slabel">Total Tweets</div></div>
  <div class="stat-card"><div class="number" id="st-actors">{D['n_actors']:,}</div><div class="slabel">Akun Unik</div></div>
  <div class="stat-card"><div class="number" style="color:{C['pro']}" id="st-pro">{D['n_pro']:,}</div><div class="slabel">PRO</div></div>
  <div class="stat-card"><div class="number" style="color:{C['kontra']}" id="st-kontra">{D['n_kontra']:,}</div><div class="slabel">KONTRA</div></div>
  <div class="stat-card"><div class="number" id="st-netral">{D['n_netral']:,}</div><div class="slabel">NETRAL</div></div>
  <div class="stat-card"><div class="number" style="color:#69db7c" id="st-pos">{D['n_pos']:,}</div><div class="slabel">Positif</div></div>
  <div class="stat-card"><div class="number" style="color:#ff6b6b" id="st-neg">{D['n_neg']:,}</div><div class="slabel">Negatif</div></div>
  <div class="stat-card"><div class="number" id="st-fav">{fmt_num(D['total_fav'])}</div><div class="slabel">Total Likes</div></div>
</div>

<div class="charts-2">
  <div class="chart-box">
    <h2>Distribusi Sikap (Stance)</h2>
    <canvas id="chartStance" height="220"></canvas>
  </div>
  <div class="chart-box">
    <h2>Distribusi Sentimen</h2>
    <canvas id="chartSent" height="220"></canvas>
  </div>
</div>

<div class="section">
  <h2>Distribusi per Variabel</h2>
  <canvas id="chartVar" height="160"></canvas>
</div>

<div class="section">
  <h2>Distribusi per Keyword</h2>
  <canvas id="chartKw" height="140"></canvas>
</div>

<div class="section">
  <h2>Top 25 Konsep (LLM)</h2>
  <canvas id="chartConcepts" height="180"></canvas>
</div>

<div class="section">
  <h2>Top 20 Akun Twitter</h2>
  <table>
    <thead><tr>
      <th>Username</th><th>Likes</th><th>Tweets</th>
      <th style="color:{C['pro']}">PRO</th>
      <th style="color:{C['kontra']}">KONTRA</th>
      <th>NETRAL</th><th>Sikap</th>
    </tr></thead>
    <tbody id="actorTbody">{actor_rows_by_period['all']}</tbody>
  </table>
</div>

<div class="section">
  <h2>Jaringan Mention (SNA)</h2>
  <iframe id="netFrame" class="network-frame" src="{net_paths['all']}"></iframe>
</div>

</div><!-- /container -->

<script>
const ALL = {ALL_DATA_JSON};
const ACTOR_HTML = {json.dumps(actor_rows_by_period, ensure_ascii=False)};
const NET_PATHS  = {json.dumps(net_paths, ensure_ascii=False)};
const C = {{
  pro:"{C['pro']}", kontra:"{C['kontra']}", netral:"{C['netral']}",
  accent:"{C['accent']}", info:"{C['info']}", concept:"{C['concept']}", txt2:"{C['txt2']}"
}};

let chartStance, chartSent, chartVar, chartKw, chartConcepts;

function fmtNum(n){{
  n=parseInt(n)||0;
  if(n>=1e6) return (n/1e6).toFixed(1)+"M";
  if(n>=1e3) return (n/1e3).toFixed(0)+"K";
  return n.toString();
}}

function initCharts(d){{
  const co=(id,cfg)=>new Chart(document.getElementById(id).getContext('2d'),cfg);
  chartStance=co('chartStance',{{type:'doughnut',data:{{labels:['PRO','KONTRA','NETRAL'],datasets:[{{data:[d.n_pro,d.n_kontra,d.n_netral],backgroundColor:[C.pro,C.kontra,C.netral],borderWidth:0}}]}},options:{{plugins:{{legend:{{labels:{{color:'#e8e8e8'}}}}}},cutout:'65%'}}}});
  chartSent=co('chartSent',{{type:'doughnut',data:{{labels:['Positif','Negatif','Netral'],datasets:[{{data:[d.n_pos,d.n_neg,d.n_neu],backgroundColor:['#69db7c','#ff6b6b','#ced4da'],borderWidth:0}}]}},options:{{plugins:{{legend:{{labels:{{color:'#e8e8e8'}}}}}},cutout:'65%'}}}});
  chartVar=co('chartVar',{{type:'bar',data:{{labels:d.var.labels,datasets:[{{label:'PRO',data:d.var.pro,backgroundColor:C.pro}},{{label:'KONTRA',data:d.var.kontra,backgroundColor:C.kontra}},{{label:'NETRAL',data:d.var.netral,backgroundColor:C.netral}}]}},options:{{indexAxis:'y',plugins:{{legend:{{labels:{{color:'#e8e8e8'}}}}}},scales:{{x:{{stacked:true,ticks:{{color:'#c9d1d9'}},grid:{{color:'#2e325033'}}}},y:{{stacked:true,ticks:{{color:'#c9d1d9'}},grid:{{color:'#2e325033'}}}}}}}}}});
  chartKw=co('chartKw',{{type:'bar',data:{{labels:d.kw.labels,datasets:[{{data:d.kw.counts,backgroundColor:C.accent}}]}},options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#c9d1d9'}},grid:{{color:'#2e325033'}}}},y:{{ticks:{{color:'#c9d1d9'}},grid:{{color:'#2e325033'}}}}}}}}}});
  chartConcepts=co('chartConcepts',{{type:'bar',data:{{labels:d.concepts.labels,datasets:[{{data:d.concepts.counts,backgroundColor:C.concept}}]}},options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#c9d1d9'}},grid:{{color:'#2e325033'}}}},y:{{ticks:{{color:'#c9d1d9',font:{{size:11}}}},grid:{{color:'#2e325033'}}}}}}}}}});
}}

function updateCharts(pid){{
  const d=ALL[pid];
  document.getElementById('st-tweets').textContent=d.n_tweets.toLocaleString();
  document.getElementById('st-actors').textContent=d.n_actors.toLocaleString();
  document.getElementById('st-pro').textContent=d.n_pro.toLocaleString();
  document.getElementById('st-kontra').textContent=d.n_kontra.toLocaleString();
  document.getElementById('st-netral').textContent=d.n_netral.toLocaleString();
  document.getElementById('st-pos').textContent=d.n_pos.toLocaleString();
  document.getElementById('st-neg').textContent=d.n_neg.toLocaleString();
  document.getElementById('st-fav').textContent=fmtNum(d.total_fav);
  chartStance.data.datasets[0].data=[d.n_pro,d.n_kontra,d.n_netral]; chartStance.update();
  chartSent.data.datasets[0].data=[d.n_pos,d.n_neg,d.n_neu]; chartSent.update();
  chartVar.data.labels=d.var.labels;
  chartVar.data.datasets[0].data=d.var.pro;
  chartVar.data.datasets[1].data=d.var.kontra;
  chartVar.data.datasets[2].data=d.var.netral; chartVar.update();
  chartKw.data.labels=d.kw.labels; chartKw.data.datasets[0].data=d.kw.counts; chartKw.update();
  chartConcepts.data.labels=d.concepts.labels; chartConcepts.data.datasets[0].data=d.concepts.counts; chartConcepts.update();
  document.getElementById('actorTbody').innerHTML=ACTOR_HTML[pid];
  document.getElementById('netFrame').src=NET_PATHS[pid];
}}

document.addEventListener('DOMContentLoaded',()=>{{
  initCharts(ALL['all']);
  document.querySelectorAll('.period-btn').forEach(btn=>{{
    btn.addEventListener('click',()=>{{
      document.querySelectorAll('.period-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      updateCharts(btn.dataset.pid);
    }});
  }});
}});
</script>
</body>
</html>"""

OUTPUT.write_text(HTML, encoding="utf-8")

print(f"\n[DONE] {OUTPUT}")
print(f"  tweets={D['n_tweets']}, actors={D['n_actors']}, PRO={D['n_pro']}, KONTRA={D['n_kontra']}, NETRAL={D['n_netral']}")
