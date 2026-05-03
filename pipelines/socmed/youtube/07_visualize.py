"""
STEP 5b — YouTube DNA Analysis Dashboard
=========================================
Input : output/socmed/youtube/youtube_extracted_raw.jsonl
        output/socmed/youtube/youtube_sentiment.csv  (partial OK)
        output/socmed/youtube/youtube_metadata.csv
Output: output/youtube_report.html
        output/youtube_network_yt_<pid>.html  (per-period channel networks)

Run: source venv/bin/activate && python socmed/05_visualize_youtube.py
"""

import json
from itertools import combinations
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT   = Path(__file__).parent.parent.parent.parent
YT_DIR = ROOT / "data" / "processed" / "youtube"
OUTDIR = ROOT / "data" / "processed" / "youtube"
OUTPUT = OUTDIR / "youtube_report.html"

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
with open(YT_DIR / "youtube_extracted_raw.jsonl") as f:
    for line in f:
        rows_ext.append(json.loads(line))
df_ext = pd.DataFrame(rows_ext)
df_ext["published_at"] = pd.to_datetime(df_ext["published_at"], utc=True, errors="coerce")
df_ext["view_count"]   = pd.to_numeric(df_ext["view_count"], errors="coerce").fillna(0).astype(int)
df_ext["like_count"]   = pd.to_numeric(df_ext["like_count"], errors="coerce").fillna(0).astype(int)
df_ext["comment_count"]= pd.to_numeric(df_ext["comment_count"], errors="coerce").fillna(0).astype(int)
df_ext["subscriber_count"] = pd.to_numeric(df_ext["subscriber_count"], errors="coerce").fillna(0).astype(int)

sent_path = YT_DIR / "youtube_sentiment.csv"
has_sent  = sent_path.exists()
if has_sent:
    df_sent = pd.read_csv(sent_path)
    df_sent = df_sent.dropna(subset=["sentiment"])
    df_sent["published_at"] = pd.to_datetime(df_sent["published_at"], utc=True, errors="coerce")
    sent_n = len(df_sent)
    sent_total = len(df_ext)
    print(f"[SENTIMENT] {sent_n}/{sent_total} videos scored")
else:
    df_sent = pd.DataFrame()
    print("[SENTIMENT] file not found — sentiment charts disabled")


def _slice(df, pid):
    _, pstart, pend = PERIODS[pid]
    d = df
    if pstart:
        d = d[d["published_at"] >= pd.Timestamp(pstart, tz="UTC")]
    if pend:
        d = d[d["published_at"] < pd.Timestamp(pend, tz="UTC")]
    return d


def fmt_num(n):
    try:
        n = int(n)
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.0f}K"
        return str(n)
    except Exception:
        return "–"


def dominant_pos(row):
    m = max(row.get("PRO", 0), row.get("KONTRA", 0), row.get("NETRAL", 0))
    if m == 0:
        return "NETRAL"
    if row.get("PRO", 0) == m:
        return "PRO"
    if row.get("KONTRA", 0) == m:
        return "KONTRA"
    return "NETRAL"


def pos_color(p):
    return {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(p, C["netral"])


def parse_concepts(val):
    if isinstance(val, list):
        return [c.strip().lower() for c in val if c.strip()]
    if isinstance(val, str):
        try:
            lst = json.loads(val)
            return [c.strip().lower() for c in lst if c.strip()]
        except Exception:
            return []
    return []


def build_channel_network(df_ext_slice):
    """Channels as nodes, edges = shared variable_name coverage."""
    ch_vars = defaultdict(set)
    ch_stance = {}
    for _, row in df_ext_slice.iterrows():
        ch = str(row["channel_title"]).strip()
        var = str(row.get("variable_name", "")).strip()
        if ch and var:
            ch_vars[ch].add(var)
        if ch not in ch_stance:
            ch_stance[ch] = defaultdict(int)
        ch_stance[ch][row.get("position", "NETRAL")] += 1

    channels = list(ch_vars.keys())
    edge_count = defaultdict(int)
    for a, b in combinations(channels, 2):
        shared = len(ch_vars[a] & ch_vars[b])
        if shared >= 1:
            edge_count[(a, b)] += shared

    edges = [(a, b, w) for (a, b), w in edge_count.items()]
    dom_map = {}
    for ch, counts in ch_stance.items():
        dom_map[ch] = dominant_pos({"PRO": counts.get("PRO", 0),
                                    "KONTRA": counts.get("KONTRA", 0),
                                    "NETRAL": counts.get("NETRAL", 0)})
    return edges, dom_map


def build_network_html(edges, dom_map, ch_video_counts, out_path):
    try:
        from pyvis.network import Network
    except ImportError:
        out_path.write_text("<p style='color:#aaa;padding:20px'>pip install pyvis</p>")
        return

    edges_top = sorted(edges, key=lambda x: -x[2])[:100]
    all_nodes = set()
    for s, t, _ in edges_top:
        all_nodes.add(s)
        all_nodes.add(t)

    net = Network(height="600px", width="100%", bgcolor="#0f0f1a",
                  directed=False, notebook=False)
    net.set_options(json.dumps({
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -180, "springLength": 200,
                "springConstant": 0.05, "damping": 0.9,
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"enabled": True, "iterations": 300, "fit": True},
        },
        "edges": {"smooth": {"type": "curvedCW", "roundness": 0.1}},
        "interaction": {"hover": True, "dragNodes": True},
    }))

    for node in all_nodes:
        stance = dom_map.get(node, "NETRAL")
        col = {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(stance, C["netral"])
        vcount = ch_video_counts.get(node, 1)
        size = max(10, min(35, 10 + vcount * 2))
        net.add_node(
            node, label=node[:25], color={"background": col, "border": col},
            shape="dot", size=size, title=f"{node} | {stance} | {vcount} video",
            font={"color": "#ffffff", "size": 12, "strokeWidth": 2, "strokeColor": "#000000"},
        )

    for s, t, w in edges_top:
        net.add_edge(s, t, width=max(1, min(6, w)), color="#3d3d6b",
                     title=f"{s} ↔ {t} | shared topics={w}")

    net.save_graph(str(out_path))


# ── Precompute per-period data ────────────────────────────────────────────────
period_data = {}

for pid in PERIOD_ORDER:
    ext_s  = _slice(df_ext, pid)
    sent_s = _slice(df_sent, pid) if has_sent and len(df_sent) > 0 else pd.DataFrame()

    n_pro    = int((ext_s["position"] == "PRO").sum())
    n_kontra = int((ext_s["position"] == "KONTRA").sum())
    n_netral = int((ext_s["position"] == "NETRAL").sum())
    n_videos = len(ext_s)
    n_channels = ext_s["channel_title"].nunique()
    total_views = int(ext_s["view_count"].sum())

    n_pos = n_neg = n_neu = 0
    avg_sent = 0.5
    has_sent_period = has_sent and len(sent_s) > 0
    if has_sent_period:
        n_pos = int((sent_s["sentiment"] == "POSITIVE").sum())
        n_neg = int((sent_s["sentiment"] == "NEGATIVE").sum())
        n_neu = int((sent_s["sentiment"] == "NEUTRAL").sum())
        avg_sent = float(sent_s["sentiment_score"].mean()) if len(sent_s) > 0 else 0.5

    # Monthly trend
    ext_valid = ext_s.dropna(subset=["published_at"]).copy()
    ext_valid["month"] = ext_valid["published_at"].dt.to_period("M").astype(str)
    monthly = (
        ext_valid.groupby(["month", "position"])
        .size().unstack(fill_value=0).reset_index()
    )
    for col in ["PRO", "KONTRA", "NETRAL"]:
        if col not in monthly.columns:
            monthly[col] = 0
    monthly["total"] = monthly["PRO"] + monthly["KONTRA"] + monthly["NETRAL"]
    monthly = monthly[monthly["total"] >= 1].sort_values("month").tail(36)

    # Variable distribution
    var_pos = (
        ext_s.groupby(["variable_name", "position"])
        .size().unstack(fill_value=0).reset_index()
    )
    for col in ["PRO", "KONTRA", "NETRAL"]:
        if col not in var_pos.columns:
            var_pos[col] = 0
    var_pos["total"] = var_pos["PRO"] + var_pos["KONTRA"] + var_pos["NETRAL"]
    var_pos = var_pos.sort_values("total", ascending=False)

    # Top channels
    ch_stance = (
        ext_s.groupby(["channel_title", "position"])
        .size().unstack(fill_value=0).reset_index()
    )
    for col in ["PRO", "KONTRA", "NETRAL"]:
        if col not in ch_stance.columns:
            ch_stance[col] = 0
    ch_stance["total"] = ch_stance["PRO"] + ch_stance["KONTRA"] + ch_stance["NETRAL"]

    ch_views = ext_s.groupby("channel_title")["view_count"].sum().reset_index(name="total_views")
    ch_subs  = ext_s.groupby("channel_title")["subscriber_count"].max().reset_index(name="subscribers")
    ch_stance = ch_stance.merge(ch_views, on="channel_title", how="left")
    ch_stance = ch_stance.merge(ch_subs, on="channel_title", how="left")
    ch_stance = ch_stance.sort_values("total", ascending=False).head(20)

    # Top concepts
    concept_counts = defaultdict(int)
    for _, row in ext_s.iterrows():
        for c in parse_concepts(row.get("concepts", [])):
            concept_counts[c] += 1
    top_concepts = sorted(concept_counts.items(), key=lambda x: -x[1])[:25]

    # Channel network
    ch_video_counts = ext_s.groupby("channel_title").size().to_dict()
    edges, dom_map = build_channel_network(ext_s)
    net_path = OUTDIR / f"youtube_network_yt_{pid}.html"
    build_network_html(edges, dom_map, ch_video_counts, net_path)

    # Build channel table HTML
    ch_rows_html = ""
    for _, r in ch_stance.iterrows():
        dp = dominant_pos({"PRO": r["PRO"], "KONTRA": r["KONTRA"], "NETRAL": r["NETRAL"]})
        ch_rows_html += (
            f'<tr>'
            f'<td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{r["channel_title"]}</td>'
            f'<td style="text-align:center;">{fmt_num(r.get("subscribers", 0))}</td>'
            f'<td style="text-align:center;">{fmt_num(r.get("total_views", 0))}</td>'
            f'<td style="text-align:center;">{int(r["total"])}</td>'
            f'<td style="text-align:center;color:{C["pro"]};">{int(r["PRO"])}</td>'
            f'<td style="text-align:center;color:{C["kontra"]};">{int(r["KONTRA"])}</td>'
            f'<td style="text-align:center;color:{C["netral"]};">{int(r["NETRAL"])}</td>'
            f'<td style="text-align:center;color:{pos_color(dp)};font-weight:700;">{dp}</td>'
            f'</tr>\n'
        )

    period_data[pid] = {
        "n_videos":   n_videos,
        "n_channels": n_channels,
        "n_pro":      n_pro,
        "n_kontra":   n_kontra,
        "n_netral":   n_netral,
        "n_pos":      n_pos,
        "n_neg":      n_neg,
        "n_neu":      n_neu,
        "avg_sent":   round(avg_sent, 3),
        "total_views": total_views,
        "has_sent":   has_sent_period,
        "monthly": {
            "labels":  monthly["month"].tolist(),
            "pro":     monthly["PRO"].tolist(),
            "kontra":  monthly["KONTRA"].tolist(),
            "netral":  monthly["NETRAL"].tolist(),
        },
        "var": {
            "labels":  var_pos["variable_name"].tolist(),
            "pro":     var_pos["PRO"].tolist(),
            "kontra":  var_pos["KONTRA"].tolist(),
            "netral":  var_pos["NETRAL"].tolist(),
        },
        "concepts": {
            "labels":  [c for c, _ in top_concepts],
            "counts":  [n for _, n in top_concepts],
        },
        "ch_rows":    ch_rows_html,
        "net_file":   net_path.name,
    }
    print(f"  [{pid}] videos={n_videos}, channels={n_channels}, edges={len(edges)}")


ALL_DATA_JSON = json.dumps(period_data, ensure_ascii=False)

period_options = "".join(
    f'<option value="{pid}">{label}</option>'
    for pid, (label, _, _) in PERIODS.items()
)

sent_note = f"({sent_n}/{sent_total} video terskor)" if has_sent else "(belum tersedia)"

HTML = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DNA — YouTube Kebijakan Nuklir Indonesia</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{C['bg']};color:{C['txt1']};line-height:1.5}}
a{{color:inherit}}
.tab-nav{{background:#161622;border-bottom:2px solid {C['border']};display:flex;gap:2px;padding:0 48px}}
.tab-link{{
  color:{C['txt2']};padding:11px 22px;text-decoration:none;
  border-bottom:3px solid transparent;font-size:0.9rem;font-weight:700;
  letter-spacing:0.5px;margin-bottom:-2px;transition:color .15s;display:inline-block;
}}
.tab-link:hover{{color:{C['txt1']}}}
.tab-active{{color:{C['accent']};border-bottom-color:{C['accent']}}}
.header{{background:linear-gradient(135deg,{C['hdr_from']},{C['hdr_to']});padding:28px 48px}}
.header h1{{font-size:1.85rem;color:#fff;letter-spacing:-0.5px}}
.header p{{color:{C['txt2']};margin-top:6px;font-size:0.95rem}}
.container{{max-width:1400px;margin:0 auto;padding:28px 48px}}
.period-bar{{
  display:flex;align-items:center;gap:14px;
  background:{C['card']};border:1px solid {C['border']};
  border-radius:12px;padding:14px 20px;margin-bottom:28px;flex-wrap:wrap;
}}
.period-bar label{{font-size:0.88rem;color:{C['txt2']};font-weight:600;white-space:nowrap}}
.period-select{{
  background:{C['card2']};color:{C['txt1']};border:2px solid {C['accent']};
  border-radius:8px;padding:8px 14px;font-size:0.95rem;cursor:pointer;
  font-family:inherit;min-width:220px;outline-offset:2px;
}}
.period-select:focus{{outline:3px solid {C['accent']}}}
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
.note{{color:{C['txt2']};font-size:0.8rem;margin-top:6px;font-style:italic}}
@media(max-width:900px){{
  .chart-row{{grid-template-columns:1fr}}
  .stats-row{{grid-template-columns:repeat(2,1fr)}}
  .container,.header,.tab-nav{{padding:16px 20px}}
}}
</style>
</head>
<body>

<div class="header">
  <h1>Discourse Network Analysis — YouTube</h1>
  <p>Kebijakan Energi Nuklir Indonesia · Analisis Konten YouTube</p>
</div>

<nav class="tab-nav">
  <a href="report_dna.html" class="tab-link">BERITA NASIONAL</a>
  <a href="socmed_report.html" class="tab-link">INSTAGRAM</a>
  <a href="youtube_report.html" class="tab-link tab-active">YOUTUBE</a>
  <a href="facebook_report.html" class="tab-link">FACEBOOK</a>
</nav>

<div class="container">

<div class="period-bar">
  <label>Pilih Periode Pemerintahan:</label>
  <select class="period-select" id="periodSelect" onchange="updatePeriod(this.value)">
    {period_options}
  </select>
  <span id="periodSummary" style="color:{C['txt2']};font-size:0.88rem;"></span>
</div>

<div class="stats-row">
  <div class="stat-card"><div class="number" id="statVideos">–</div><div class="slabel">Total Video</div></div>
  <div class="stat-card"><div class="number" id="statChannels">–</div><div class="slabel">Channel Unik</div></div>
  <div class="stat-card"><div class="number" id="statPro" style="color:{C['pro']};"></div><div class="slabel">PRO Nuklir</div></div>
  <div class="stat-card"><div class="number" id="statKontra" style="color:{C['kontra']};"></div><div class="slabel">KONTRA Nuklir</div></div>
  <div class="stat-card"><div class="number" id="statNetral" style="color:{C['netral']};"></div><div class="slabel">NETRAL</div></div>
  <div class="stat-card"><div class="number" id="statViews">–</div><div class="slabel">Total Views</div></div>
  <div class="stat-card"><div class="number" id="statPos" style="color:{C['info']};"></div><div class="slabel">Sentimen Positif</div></div>
  <div class="stat-card"><div class="number" id="statSent">–</div><div class="slabel">Rata-rata Skor Sentimen</div></div>
</div>

<div class="section">
  <h2>Distribusi Sikap &amp; Sentimen <span class="note">{sent_note}</span></h2>
  <div class="chart-row">
    <div><canvas id="chartStance"></canvas></div>
    <div><canvas id="chartSentiment"></canvas></div>
  </div>
</div>

<div class="section">
  <h2>Tren Sikap per Bulan</h2>
  <canvas id="chartMonthly" style="max-height:280px;"></canvas>
</div>

<div class="section">
  <h2>Distribusi Variabel Diskursus</h2>
  <canvas id="chartVar" style="max-height:340px;"></canvas>
</div>

<div class="section">
  <h2>Top 20 Channel berdasarkan Jumlah Video</h2>
  <table class="tbl">
    <thead><tr>
      <th>Channel</th><th>Subscribers</th><th>Total Views</th><th>Video</th>
      <th style="color:{C['pro']};">PRO</th>
      <th style="color:{C['kontra']};">KONTRA</th>
      <th style="color:{C['netral']};">NETRAL</th>
      <th>Dominan</th>
    </tr></thead>
    <tbody id="chTableBody"></tbody>
  </table>
</div>

<div class="section">
  <h2>Top 25 Konsep (Ekstraksi LLM)</h2>
  <canvas id="chartConcepts" style="max-height:500px;"></canvas>
</div>

<div class="section">
  <h2>Social Network Analysis — Jaringan Channel</h2>
  <div class="net-legend">
    <span class="leg"><span class="dot" style="background:{C['pro']};"></span>PRO</span>
    <span class="leg"><span class="dot" style="background:{C['kontra']};"></span>KONTRA</span>
    <span class="leg"><span class="dot" style="background:{C['netral']};"></span>NETRAL</span>
    <span style="color:{C['txt2']};font-size:0.82rem;">Node = channel · Edge = topik/variabel yang sama dibahas · Ukuran = jumlah video</span>
  </div>
  <iframe id="networkFrame" src="youtube_network_yt_all.html"
    style="width:100%;height:620px;border:none;border-radius:8px;background:{C['bg']};"></iframe>
</div>

</div>

<script>
const ALL_DATA = {ALL_DATA_JSON};

const PRO_C  = "{C['pro']}";
const KON_C  = "{C['kontra']}";
const NET_C  = "{C['netral']}";
const POS_C  = "{C['info']}";
const ACC_C  = "{C['accent']}";
const TXT1   = "{C['txt1']}";
const TXT2   = "{C['txt2']}";
const BORDER = "{C['border']}";
const TICK   = {{ color: TXT2, font: {{ size: 11 }} }};
const GRID   = {{ color: BORDER }};
const LEG    = {{ labels: {{ color: TXT1 }}, position: 'bottom' }};

let chartStance, chartSentiment, chartMonthly, chartVar, chartConcepts;

function makeCharts() {{
  chartStance = new Chart(document.getElementById('chartStance'), {{
    type: 'doughnut',
    data: {{ labels: ['PRO','KONTRA','NETRAL'], datasets: [{{
      data: [0,0,0], backgroundColor: [PRO_C, KON_C, NET_C], borderWidth: 0
    }}] }},
    options: {{
      plugins: {{
        legend: LEG,
        title: {{ display: true, text: 'Sikap terhadap Nuklir/PLTN', color: TXT1, font: {{ size: 14 }} }},
      }},
      cutout: '62%',
    }},
  }});

  chartSentiment = new Chart(document.getElementById('chartSentiment'), {{
    type: 'doughnut',
    data: {{ labels: ['POSITIVE','NEGATIVE','NEUTRAL'], datasets: [{{
      data: [0,0,0], backgroundColor: [POS_C, KON_C, NET_C], borderWidth: 0
    }}] }},
    options: {{
      plugins: {{
        legend: LEG,
        title: {{ display: true, text: 'Distribusi Sentimen Video', color: TXT1, font: {{ size: 14 }} }},
      }},
      cutout: '62%',
    }},
  }});

  chartMonthly = new Chart(document.getElementById('chartMonthly'), {{
    type: 'bar',
    data: {{ labels: [], datasets: [
      {{ label: 'PRO',    data: [], backgroundColor: PRO_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'KONTRA', data: [], backgroundColor: KON_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'NETRAL', data: [], backgroundColor: NET_C, stack: 'a', borderRadius: 2 }},
    ] }},
    options: {{
      responsive: true,
      plugins: {{ legend: LEG }},
      scales: {{
        x: {{ stacked: true, ticks: TICK, grid: {{ color: BORDER }} }},
        y: {{ stacked: true, ticks: TICK, grid: GRID }},
      }},
    }},
  }});

  chartVar = new Chart(document.getElementById('chartVar'), {{
    type: 'bar',
    data: {{ labels: [], datasets: [
      {{ label: 'PRO',    data: [], backgroundColor: PRO_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'KONTRA', data: [], backgroundColor: KON_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'NETRAL', data: [], backgroundColor: NET_C, stack: 'a', borderRadius: 2 }},
    ] }},
    options: {{
      indexAxis: 'y', responsive: true,
      plugins: {{ legend: LEG }},
      scales: {{
        x: {{ stacked: true, ticks: TICK, grid: GRID }},
        y: {{ stacked: true, ticks: {{ color: TXT2, font: {{ size: 11 }} }} }},
      }},
    }},
  }});

  chartConcepts = new Chart(document.getElementById('chartConcepts'), {{
    type: 'bar',
    data: {{ labels: [], datasets: [{{
      label: 'Video', data: [], backgroundColor: ACC_C, borderRadius: 4
    }}] }},
    options: {{
      indexAxis: 'y', responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: TICK, grid: GRID }},
        y: {{ ticks: {{ color: TXT2, font: {{ size: 11 }} }} }},
      }},
    }},
  }});
}}

function fmtNum(n) {{
  if (n >= 1e6) return (n/1e6).toFixed(1)+'M';
  if (n >= 1e3) return (n/1e3).toFixed(0)+'K';
  return n.toString();
}}

function updatePeriod(pid) {{
  var d = ALL_DATA[pid];
  if (!d) return;

  document.getElementById('statVideos').textContent   = d.n_videos.toLocaleString();
  document.getElementById('statChannels').textContent = d.n_channels.toLocaleString();
  document.getElementById('statPro').textContent      = d.n_pro;
  document.getElementById('statKontra').textContent   = d.n_kontra;
  document.getElementById('statNetral').textContent   = d.n_netral;
  document.getElementById('statViews').textContent    = fmtNum(d.total_views);
  document.getElementById('statPos').textContent      = d.n_pos;
  document.getElementById('statSent').textContent     = d.avg_sent.toFixed(2);

  chartStance.data.datasets[0].data    = [d.n_pro, d.n_kontra, d.n_netral];
  chartSentiment.data.datasets[0].data = [d.n_pos, d.n_neg, d.n_neu];
  chartStance.update();
  chartSentiment.update();

  chartMonthly.data.labels           = d.monthly.labels;
  chartMonthly.data.datasets[0].data = d.monthly.pro;
  chartMonthly.data.datasets[1].data = d.monthly.kontra;
  chartMonthly.data.datasets[2].data = d.monthly.netral;
  chartMonthly.update();

  chartVar.data.labels           = d.var.labels;
  chartVar.data.datasets[0].data = d.var.pro;
  chartVar.data.datasets[1].data = d.var.kontra;
  chartVar.data.datasets[2].data = d.var.netral;
  chartVar.update();

  chartConcepts.data.labels           = d.concepts.labels;
  chartConcepts.data.datasets[0].data = d.concepts.counts;
  chartConcepts.update();

  document.getElementById('chTableBody').innerHTML = d.ch_rows;
  document.getElementById('networkFrame').src = d.net_file;
}}

makeCharts();
updatePeriod('all');
</script>
</body>
</html>"""

OUTPUT.write_text(HTML, encoding="utf-8")
print(f"\n[DONE] {OUTPUT}")
for pid, d in period_data.items():
    print(f"  {pid}: videos={d['n_videos']}, channels={d['n_channels']}")
