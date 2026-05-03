"""
STEP 5 — Instagram Social Media Analysis Dashboard
===================================================
Input : output/socmed/instagram/socmed_extracted_raw.jsonl
        output/socmed/instagram/socmed_sentiment.csv
        output/socmed/instagram/socmed_cleaned.csv
        output/socmed/instagram/socmed_nodes_actors.csv
        output/socmed/instagram/socmed_nodes_hashtag.csv
        output/socmed/instagram/socmed_buzzer_scores.csv
Output: output/socmed_report.html
        output/socmed_network_ig_<pid>.html  (per-period mention networks)

Run: source venv/bin/activate && python socmed/05_visualize_socmed.py
"""

import json
from pathlib import Path
from collections import defaultdict

import pandas as pd

ROOT   = Path(__file__).parent.parent
IG_DIR = ROOT / "output" / "socmed" / "instagram"
OUTDIR = ROOT / "output"
OUTPUT = OUTDIR / "socmed_report.html"

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

# ── Load raw data ─────────────────────────────────────────────────────────────
rows_ext = []
with open(IG_DIR / "socmed_extracted_raw.jsonl") as f:
    for line in f:
        rows_ext.append(json.loads(line))
df_ext = pd.DataFrame(rows_ext)
df_ext["pub_date"] = pd.to_datetime(df_ext["pub_date"], utc=True, errors="coerce")

df_sent = pd.read_csv(IG_DIR / "socmed_sentiment.csv")
df_sent["pub_date"] = pd.to_datetime(df_sent["pub_date"], utc=True, errors="coerce")

df_clean = pd.read_csv(IG_DIR / "socmed_cleaned.csv")
df_clean["pub_date"] = pd.to_datetime(df_clean["pub_date"], utc=True, errors="coerce")

df_nodes  = pd.read_csv(IG_DIR / "socmed_nodes_actors.csv")
df_buz    = pd.read_csv(IG_DIR / "socmed_buzzer_scores.csv")


def _slice(df, pid):
    _, pstart, pend = PERIODS[pid]
    d = df
    if pstart:
        d = d[d["pub_date"] >= pd.Timestamp(pstart, tz="UTC")]
    if pend:
        d = d[d["pub_date"] < pd.Timestamp(pend, tz="UTC")]
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


# ── Build per-period mention edges ────────────────────────────────────────────
def build_mention_edges(df_clean_slice):
    edge_count = defaultdict(int)
    for _, row in df_clean_slice.dropna(subset=["mentions"]).iterrows():
        src = str(row["username"]).strip()
        targets = [t.strip() for t in str(row["mentions"]).split(",") if t.strip()]
        for tgt in targets:
            if tgt and tgt != src:
                edge_count[(src, tgt)] += 1
    return [(s, t, w) for (s, t), w in sorted(edge_count.items(), key=lambda x: -x[1])]


# ── Build pyvis network ───────────────────────────────────────────────────────
FREEZE_JS = """
<script>
document.addEventListener("DOMContentLoaded", function() {
  if (typeof network !== "undefined") {
    network.on("stabilizationIterationsDone", function() { network.setOptions({physics:{enabled:false}}); });
    setTimeout(function(){ network.setOptions({physics:{enabled:false}}); }, 8000);
  }
});
</script>"""

def build_network_html(edges, actor_stance_map, out_path):
    try:
        from pyvis.network import Network
    except ImportError:
        print("  [WARN] pyvis not installed — skipping network")
        out_path.write_text("<p style='color:#aaa;padding:20px'>pip install pyvis</p>")
        return

    # keep top 80 edges by weight, limit to nodes that appear
    edges_top = sorted(edges, key=lambda x: -x[2])[:80]
    all_nodes = set()
    for s, t, _ in edges_top:
        all_nodes.add(s)
        all_nodes.add(t)

    net = Network(height="600px", width="100%", bgcolor="#0f0f1a",
                  directed=True, notebook=False)
    net.set_options(json.dumps({
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -200, "springLength": 200,
                "springConstant": 0.05, "damping": 0.9,
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"enabled": True, "iterations": 300, "fit": True},
        },
        "edges": {"smooth": {"type": "curvedCW", "roundness": 0.15}, "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}}},
        "interaction": {"hover": True, "dragNodes": True},
    }))

    for node in all_nodes:
        stance = actor_stance_map.get(node, "NETRAL")
        col = {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(stance, C["netral"])
        net.add_node(
            node, label=f"@{node}", color={"background": col, "border": col},
            shape="dot", size=20, title=f"@{node} | {stance}",
            font={"color": "#ffffff", "size": 13, "strokeWidth": 2, "strokeColor": "#000000"},
        )

    for s, t, w in edges_top:
        col = {"PRO": C["pro"], "KONTRA": C["kontra"]}.get(
            actor_stance_map.get(s, "NETRAL"), C["netral"])
        net.add_edge(s, t, width=max(1, min(8, w)), color=col,
                     title=f"{s} → {t} | n={w}")

    net.save_graph(str(out_path))
    html = out_path.read_text(encoding="utf-8")
    out_path.write_text(html, encoding="utf-8")


# ── Precompute per-period data ────────────────────────────────────────────────
period_data   = {}
network_paths = {}

for pid in PERIOD_ORDER:
    ext_s   = _slice(df_ext, pid)
    sent_s  = _slice(df_sent, pid)
    clean_s = _slice(df_clean, pid)

    n_pro    = int((ext_s["position"] == "PRO").sum())
    n_kontra = int((ext_s["position"] == "KONTRA").sum())
    n_netral = int((ext_s["position"] == "NETRAL").sum())
    n_pos    = int((sent_s["sentiment"] == "POSITIVE").sum())
    n_neg    = int((sent_s["sentiment"] == "NEGATIVE").sum())
    n_neu    = int((sent_s["sentiment"] == "NEUTRAL").sum())
    avg_sent = float(sent_s["sentiment_score"].mean()) if len(sent_s) > 0 else 0.0
    n_posts  = len(ext_s)
    n_actors = ext_s["username"].nunique()

    # Monthly trend
    ext_valid = ext_s.dropna(subset=["pub_date"]).copy()
    ext_valid["month"] = ext_valid["pub_date"].dt.to_period("M").astype(str)
    monthly = (
        ext_valid.groupby(["month", "position"])
        .size().unstack(fill_value=0).reset_index()
    )
    for col in ["PRO", "KONTRA", "NETRAL"]:
        if col not in monthly.columns:
            monthly[col] = 0
    monthly["total"] = monthly["PRO"] + monthly["KONTRA"] + monthly["NETRAL"]
    monthly = monthly[monthly["total"] >= 2].sort_values("month").tail(36)

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

    # Top actors
    actor_stance = (
        ext_s.groupby(["username", "position"])
        .size().unstack(fill_value=0).reset_index()
    )
    for col in ["PRO", "KONTRA", "NETRAL"]:
        if col not in actor_stance.columns:
            actor_stance[col] = 0
    actor_stance["total"] = actor_stance["PRO"] + actor_stance["KONTRA"] + actor_stance["NETRAL"]
    actor_stance = actor_stance.merge(
        df_nodes[["username", "followers_count", "is_verified"]].drop_duplicates("username"),
        on="username", how="left",
    ).sort_values("total", ascending=False).head(20)

    # Top hashtags from cleaned slice
    htag_counts = defaultdict(int)
    for _, row in clean_s.dropna(subset=["hashtags"]).iterrows():
        for h in str(row["hashtags"]).split(","):
            h = h.strip().lower()
            if h:
                htag_counts[h] += 1
    top_htags = sorted(htag_counts.items(), key=lambda x: -x[1])[:25]

    # Actor stance map for network
    actor_stance_map = {}
    for _, r in actor_stance.iterrows():
        actor_stance_map[r["username"]] = dominant_pos({
            "PRO": r["PRO"], "KONTRA": r["KONTRA"], "NETRAL": r["NETRAL"]
        })

    # Build mention network
    edges = build_mention_edges(clean_s)
    net_path = OUTDIR / f"socmed_network_ig_{pid}.html"
    build_network_html(edges, actor_stance_map, net_path)
    network_paths[pid] = net_path.name

    # Build actor rows HTML
    actor_rows_html = ""
    for _, r in actor_stance.iterrows():
        dp = dominant_pos({"PRO": r["PRO"], "KONTRA": r["KONTRA"], "NETRAL": r["NETRAL"]})
        v_badge = ' <span style="color:#ffd43b;font-size:0.7rem;">✓</span>' if r.get("is_verified") else ""
        actor_rows_html += (
            f'<tr>'
            f'<td><a href="https://instagram.com/{r["username"]}" target="_blank" '
            f'style="color:{C["accent"]};text-decoration:none;">@{r["username"]}</a>{v_badge}</td>'
            f'<td style="text-align:center;">{fmt_num(r.get("followers_count","–"))}</td>'
            f'<td style="text-align:center;">{int(r["total"])}</td>'
            f'<td style="text-align:center;color:{C["pro"]};">{int(r["PRO"])}</td>'
            f'<td style="text-align:center;color:{C["kontra"]};">{int(r["KONTRA"])}</td>'
            f'<td style="text-align:center;color:{C["netral"]};">{int(r["NETRAL"])}</td>'
            f'<td style="text-align:center;color:{pos_color(dp)};font-weight:700;">{dp}</td>'
            f'</tr>\n'
        )

    period_data[pid] = {
        "n_posts":    n_posts,
        "n_actors":   n_actors,
        "n_pro":      n_pro,
        "n_kontra":   n_kontra,
        "n_netral":   n_netral,
        "n_pos":      n_pos,
        "n_neg":      n_neg,
        "n_neu":      n_neu,
        "avg_sent":   round(avg_sent, 3),
        "monthly":    {
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
        "htag": {
            "labels":  [h for h, _ in top_htags],
            "counts":  [c for _, c in top_htags],
        },
        "actor_rows": actor_rows_html,
        "net_file":   network_paths[pid],
    }
    print(f"  [{pid}] posts={n_posts}, actors={n_actors}, edges={len(edges)}")


ALL_DATA_JSON = json.dumps(period_data)

# ── Buzzer table (static) ─────────────────────────────────────────────────────
df_buz_sorted = df_buz.sort_values("buzzer_score", ascending=False).head(15)
buzzer_rows_html = ""
for _, r in df_buz_sorted.iterrows():
    score = int(r["buzzer_score"])
    color = C["kontra"] if score >= 2 else ("#ffd43b" if score == 1 else C["txt2"])
    flags = str(r.get("buzzer_flags", "")).replace("{", "").replace("}", "").replace("'", "")
    buzzer_rows_html += (
        f'<tr>'
        f'<td><a href="https://instagram.com/{r["username"]}" target="_blank" '
        f'style="color:{C["accent"]};text-decoration:none;">@{r["username"]}</a></td>'
        f'<td style="text-align:center;">{fmt_num(r.get("followers_count","–"))}</td>'
        f'<td style="text-align:center;">{fmt_num(r.get("following_count","–"))}</td>'
        f'<td style="text-align:center;">{fmt_num(r.get("post_count","–"))}</td>'
        f'<td style="text-align:center;color:{color};font-weight:700;">{score}</td>'
        f'<td style="font-size:0.78rem;color:{C["txt2"]};">{flags[:80]}</td>'
        f'</tr>\n'
    )

# ── Period selector HTML ──────────────────────────────────────────────────────
period_options = "".join(
    f'<option value="{pid}">{label}</option>'
    for pid, (label, _, _) in PERIODS.items()
)

# ── Build HTML ────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DNA — Instagram Kebijakan Nuklir Indonesia</title>
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
@media(max-width:900px){{
  .chart-row{{grid-template-columns:1fr}}
  .stats-row{{grid-template-columns:repeat(2,1fr)}}
  .container,.header,.tab-nav{{padding:16px 20px}}
}}
</style>
</head>
<body>

<div class="header">
  <h1>Discourse Network Analysis — Instagram</h1>
  <p>Kebijakan Energi Nuklir Indonesia · Analisis Media Sosial Instagram</p>
</div>

<nav class="tab-nav">
  <a href="report_dna.html" class="tab-link">BERITA NASIONAL</a>
  <a href="socmed_report.html" class="tab-link tab-active">INSTAGRAM</a>
  <a href="youtube_report.html" class="tab-link">YOUTUBE</a>
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

<!-- Stats row -->
<div class="stats-row">
  <div class="stat-card"><div class="number" id="statPosts">–</div><div class="slabel">Total Post</div></div>
  <div class="stat-card"><div class="number" id="statActors">–</div><div class="slabel">Akun Unik</div></div>
  <div class="stat-card"><div class="number" id="statPro" style="color:{C['pro']};"></div><div class="slabel">PRO Nuklir</div></div>
  <div class="stat-card"><div class="number" id="statKontra" style="color:{C['kontra']};"></div><div class="slabel">KONTRA Nuklir</div></div>
  <div class="stat-card"><div class="number" id="statNetral" style="color:{C['netral']};"></div><div class="slabel">NETRAL</div></div>
  <div class="stat-card"><div class="number" id="statPos" style="color:{C['info']};"></div><div class="slabel">Sentimen Positif</div></div>
  <div class="stat-card"><div class="number" id="statNeg" style="color:{C['kontra']};"></div><div class="slabel">Sentimen Negatif</div></div>
  <div class="stat-card"><div class="number" id="statSent">–</div><div class="slabel">Rata-rata Skor Sentimen</div></div>
</div>

<!-- Stance + Sentiment donuts -->
<div class="section">
  <h2>Distribusi Sikap &amp; Sentimen</h2>
  <div class="chart-row">
    <div><canvas id="chartStance"></canvas></div>
    <div><canvas id="chartSentiment"></canvas></div>
  </div>
</div>

<!-- Monthly trend -->
<div class="section">
  <h2>Tren Sikap per Bulan</h2>
  <canvas id="chartMonthly" style="max-height:280px;"></canvas>
</div>

<!-- Variable distribution -->
<div class="section">
  <h2>Distribusi Variabel Diskursus</h2>
  <canvas id="chartVar" style="max-height:300px;"></canvas>
</div>

<!-- Top accounts -->
<div class="section">
  <h2>Top 20 Akun berdasarkan Jumlah Post</h2>
  <table class="tbl">
    <thead><tr>
      <th>Akun</th><th>Followers</th><th>Post</th>
      <th style="color:{C['pro']};">PRO</th>
      <th style="color:{C['kontra']};">KONTRA</th>
      <th style="color:{C['netral']};">NETRAL</th>
      <th>Dominan</th>
    </tr></thead>
    <tbody id="actorTableBody"></tbody>
  </table>
</div>

<!-- Top hashtags -->
<div class="section">
  <h2>Top 25 Hashtag</h2>
  <canvas id="chartHashtag" style="max-height:400px;"></canvas>
</div>

<!-- SNA Mention Network -->
<div class="section">
  <h2>Social Network Analysis — Jaringan Mention</h2>
  <div class="net-legend">
    <span class="leg"><span class="dot" style="background:{C['pro']};"></span>PRO</span>
    <span class="leg"><span class="dot" style="background:{C['kontra']};"></span>KONTRA</span>
    <span class="leg"><span class="dot" style="background:{C['netral']};"></span>NETRAL</span>
    <span style="color:{C['txt2']};font-size:0.82rem;">Node = akun Instagram · Edge = mention · Ukuran edge = frekuensi</span>
  </div>
  <iframe id="networkFrame" src="socmed_network_ig_all.html"
    style="width:100%;height:620px;border:none;border-radius:8px;background:{C['bg']};"></iframe>
</div>


</div><!-- /container -->

<script>
const ALL_DATA = {ALL_DATA_JSON};

const PRO_C  = "{C['pro']}";
const KON_C  = "{C['kontra']}";
const NET_C  = "{C['netral']}";
const POS_C  = "{C['info']}";
const TXT1   = "{C['txt1']}";
const TXT2   = "{C['txt2']}";
const BORDER = "{C['border']}";
const TICK   = {{ color: TXT2, font: {{ size: 11 }} }};
const GRID   = {{ color: BORDER }};
const LEG    = {{ labels: {{ color: TXT1 }}, position: 'bottom' }};

let chartStance, chartSentiment, chartMonthly, chartVar, chartHashtag;

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
        title: {{ display: true, text: 'Distribusi Sentimen Caption', color: TXT1, font: {{ size: 14 }} }},
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

  chartHashtag = new Chart(document.getElementById('chartHashtag'), {{
    type: 'bar',
    data: {{ labels: [], datasets: [{{
      label: 'Post', data: [], backgroundColor: "{C['accent']}", borderRadius: 4
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

function updatePeriod(pid) {{
  var d = ALL_DATA[pid];
  if (!d) return;

  // stats
  document.getElementById('statPosts').textContent   = d.n_posts.toLocaleString();
  document.getElementById('statActors').textContent  = d.n_actors.toLocaleString();
  document.getElementById('statPro').textContent     = d.n_pro;
  document.getElementById('statKontra').textContent  = d.n_kontra;
  document.getElementById('statNetral').textContent  = d.n_netral;
  document.getElementById('statPos').textContent     = d.n_pos;
  document.getElementById('statNeg').textContent     = d.n_neg;
  document.getElementById('statSent').textContent    = d.avg_sent.toFixed(2);

  // donuts
  chartStance.data.datasets[0].data   = [d.n_pro, d.n_kontra, d.n_netral];
  chartSentiment.data.datasets[0].data = [d.n_pos, d.n_neg, d.n_neu];
  chartStance.update();
  chartSentiment.update();

  // monthly
  chartMonthly.data.labels                  = d.monthly.labels;
  chartMonthly.data.datasets[0].data        = d.monthly.pro;
  chartMonthly.data.datasets[1].data        = d.monthly.kontra;
  chartMonthly.data.datasets[2].data        = d.monthly.netral;
  chartMonthly.update();

  // variable
  chartVar.data.labels               = d.var.labels;
  chartVar.data.datasets[0].data     = d.var.pro;
  chartVar.data.datasets[1].data     = d.var.kontra;
  chartVar.data.datasets[2].data     = d.var.netral;
  chartVar.update();

  // hashtag
  chartHashtag.data.labels           = d.htag.labels;
  chartHashtag.data.datasets[0].data = d.htag.counts;
  chartHashtag.update();

  // actor table
  document.getElementById('actorTableBody').innerHTML = d.actor_rows;

  // network iframe
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
    print(f"  {pid}: posts={d['n_posts']}, actors={d['n_actors']}")
