"""
STEP 5 — Instagram Social Media Analysis Dashboard
===================================================
Input : output/socmed/instagram/socmed_extracted_raw.jsonl
        output/socmed/instagram/socmed_sentiment.csv
        output/socmed/instagram/socmed_nodes_actors.csv
        output/socmed/instagram/socmed_nodes_hashtag.csv
        output/socmed/instagram/socmed_edges_mention.csv
        output/socmed/instagram/socmed_buzzer_scores.csv
Output: output/socmed_report.html

Run: source venv/bin/activate && python socmed/05_visualize_socmed.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).parent.parent
IG_DIR = ROOT / "output" / "socmed" / "instagram"
OUTPUT = ROOT / "output" / "socmed_report.html"

# ── WCAG AA palette (matches news/05_visualize_html.py) ──────────────────────
C = {
    "pro":      "#69db7c",
    "kontra":   "#ff6b6b",
    "netral":   "#ced4da",
    "pos":      "#4dabf7",
    "neg":      "#ff6b6b",
    "neu":      "#ced4da",
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
rows = []
with open(IG_DIR / "socmed_extracted_raw.jsonl") as f:
    for line in f:
        rows.append(json.loads(line))
df_ext = pd.DataFrame(rows)
df_ext["pub_date"] = pd.to_datetime(df_ext["pub_date"], utc=True, errors="coerce")

df_sent = pd.read_csv(IG_DIR / "socmed_sentiment.csv")
df_nodes = pd.read_csv(IG_DIR / "socmed_nodes_actors.csv")
df_htag = pd.read_csv(IG_DIR / "socmed_nodes_hashtag.csv")
df_edges = pd.read_csv(IG_DIR / "socmed_edges_mention.csv")
df_buz = pd.read_csv(IG_DIR / "socmed_buzzer_scores.csv")

# ── Compute stats ─────────────────────────────────────────────────────────────
total_posts   = len(df_ext)
total_actors  = df_ext["username"].nunique()
n_pro         = (df_ext["position"] == "PRO").sum()
n_kontra      = (df_ext["position"] == "KONTRA").sum()
n_netral      = (df_ext["position"] == "NETRAL").sum()
n_pos         = (df_sent["sentiment"] == "POSITIVE").sum()
n_neg         = (df_sent["sentiment"] == "NEGATIVE").sum()
n_neu         = (df_sent["sentiment"] == "NEUTRAL").sum()
avg_sent      = df_sent["sentiment_score"].mean()
verified_cnt  = df_nodes["is_verified"].sum() if "is_verified" in df_nodes.columns else 0
date_min      = df_ext["pub_date"].min()
date_max      = df_ext["pub_date"].max()
date_range    = f"{date_min.strftime('%b %Y')} – {date_max.strftime('%b %Y')}" if pd.notna(date_min) else "–"

# ── Monthly stance trend (last 30 months with data) ──────────────────────────
df_ext_valid = df_ext.dropna(subset=["pub_date"]).copy()
df_ext_valid["month"] = df_ext_valid["pub_date"].dt.to_period("M").astype(str)
monthly = (
    df_ext_valid.groupby(["month", "position"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
for col in ["PRO", "KONTRA", "NETRAL"]:
    if col not in monthly.columns:
        monthly[col] = 0
monthly = monthly.sort_values("month")
# filter to months with >= 3 posts
monthly["total"] = monthly["PRO"] + monthly["KONTRA"] + monthly["NETRAL"]
monthly = monthly[monthly["total"] >= 3].tail(30)

monthly_labels = monthly["month"].tolist()
monthly_pro    = monthly["PRO"].tolist()
monthly_kontra = monthly["KONTRA"].tolist()
monthly_netral = monthly["NETRAL"].tolist()

# ── Variable + stance ─────────────────────────────────────────────────────────
var_pos = (
    df_ext.groupby(["variable_name", "position"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
for col in ["PRO", "KONTRA", "NETRAL"]:
    if col not in var_pos.columns:
        var_pos[col] = 0
var_pos["total"] = var_pos["PRO"] + var_pos["KONTRA"] + var_pos["NETRAL"]
var_pos = var_pos.sort_values("total", ascending=False)

var_labels = var_pos["variable_name"].tolist()
var_pro    = var_pos["PRO"].tolist()
var_kontra = var_pos["KONTRA"].tolist()
var_netral = var_pos["NETRAL"].tolist()

# ── Top accounts ──────────────────────────────────────────────────────────────
actor_stance = (
    df_ext.groupby(["username", "position"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
for col in ["PRO", "KONTRA", "NETRAL"]:
    if col not in actor_stance.columns:
        actor_stance[col] = 0
actor_stance["total"] = actor_stance["PRO"] + actor_stance["KONTRA"] + actor_stance["NETRAL"]

# merge followers
actor_stance = actor_stance.merge(
    df_nodes[["username", "followers_count", "is_verified"]].drop_duplicates("username"),
    on="username", how="left",
)
top_actors = actor_stance.sort_values("total", ascending=False).head(20)

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
    m = max(row["PRO"], row["KONTRA"], row["NETRAL"])
    if m == 0:
        return "NETRAL"
    if row["PRO"] == m:
        return "PRO"
    if row["KONTRA"] == m:
        return "KONTRA"
    return "NETRAL"

def pos_color(p):
    return {"PRO": C["pro"], "KONTRA": C["kontra"], "NETRAL": C["netral"]}.get(p, C["netral"])

actor_rows_html = ""
for _, r in top_actors.iterrows():
    dp = dominant_pos(r)
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

# ── Top hashtags ──────────────────────────────────────────────────────────────
top_htags = df_htag.sort_values("total_posts", ascending=False).head(25)
htag_labels = top_htags["hashtag"].tolist()
htag_counts = top_htags["total_posts"].tolist()

# ── Buzzer table ──────────────────────────────────────────────────────────────
df_buz_sorted = df_buz.sort_values("buzzer_score", ascending=False).head(15)
buzzer_rows_html = ""
for _, r in df_buz_sorted.iterrows():
    score = int(r["buzzer_score"])
    color = C["kontra"] if score >= 2 else (C["ambigu"] if score == 1 else C["txt2"]) if "ambigu" in C else (C["kontra"] if score >= 2 else C["txt2"])
    color = C["kontra"] if score >= 2 else "#ffd43b" if score == 1 else C["txt2"]
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

# ── Mention network top edges ─────────────────────────────────────────────────
top_edges = df_edges.sort_values("weight", ascending=False).head(20)
edge_rows_html = ""
for _, r in top_edges.iterrows():
    edge_rows_html += (
        f'<tr>'
        f'<td style="color:{C["accent"]};">@{r["source"]}</td>'
        f'<td style="text-align:center;color:{C["txt2"]};">→</td>'
        f'<td style="color:{C["info"]};">@{r["target"]}</td>'
        f'<td style="text-align:center;font-weight:700;">{int(r["weight"])}</td>'
        f'</tr>\n'
    )

# ── Serialize to JSON for JS ──────────────────────────────────────────────────
import json as _json
monthly_json  = _json.dumps({"labels": monthly_labels, "pro": monthly_pro, "kontra": monthly_kontra, "netral": monthly_netral})
var_json      = _json.dumps({"labels": var_labels, "pro": var_pro, "kontra": var_kontra, "netral": var_netral})
stance_json   = _json.dumps({"pro": int(n_pro), "kontra": int(n_kontra), "netral": int(n_netral)})
sent_json     = _json.dumps({"pos": int(n_pos), "neg": int(n_neg), "neu": int(n_neu)})
htag_json     = _json.dumps({"labels": htag_labels, "counts": htag_counts})

# ── Tab nav HTML snippet ──────────────────────────────────────────────────────
TAB_NAV = f"""<nav class="tab-nav">
  <a href="report_dna.html" class="tab-link">📰 Berita Nasional</a>
  <a href="socmed_report.html" class="tab-link tab-active">📸 Instagram</a>
</nav>"""

# ── Build HTML ────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DNA — Analisis Instagram Kebijakan Nuklir Indonesia</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{C['bg']};color:{C['txt1']};line-height:1.5}}
a{{color:inherit}}
/* ── Tab nav ── */
.tab-nav{{background:#161622;border-bottom:2px solid {C['border']};display:flex;gap:2px;padding:0 48px}}
.tab-link{{
  color:{C['txt2']};padding:11px 22px;text-decoration:none;
  border-bottom:3px solid transparent;font-size:0.9rem;font-weight:600;
  margin-bottom:-2px;transition:color .15s;display:inline-block;
}}
.tab-link:hover{{color:{C['txt1']}}}
.tab-active{{color:{C['accent']};border-bottom-color:{C['accent']}}}
/* ── Header ── */
.header{{background:linear-gradient(135deg,{C['hdr_from']},{C['hdr_to']});padding:28px 48px}}
.header h1{{font-size:1.85rem;color:#fff;letter-spacing:-0.5px}}
.header p{{color:{C['txt2']};margin-top:6px;font-size:0.95rem}}
/* ── Layout ── */
.container{{max-width:1400px;margin:0 auto;padding:28px 48px}}
/* ── Stats row ── */
.stats-row{{display:grid;grid-template-columns:repeat(8,1fr);gap:14px;margin-bottom:28px}}
.stat-card{{background:{C['card']};border-radius:12px;padding:18px 12px;text-align:center;border:1px solid {C['border']}}}
.stat-card .number{{font-size:1.9rem;font-weight:700;color:{C['accent']}}}
.stat-card .slabel{{font-size:0.78rem;color:{C['txt2']};margin-top:5px;line-height:1.3}}
/* ── Sections ── */
.section{{background:{C['card']};border-radius:12px;padding:22px;margin-bottom:22px;border:1px solid {C['border']}}}
.section h2{{font-size:1.1rem;color:{C['concept']};margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid {C['border']};font-weight:600}}
.chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
.chart-row-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px}}
canvas{{max-height:320px}}
/* ── Table ── */
.tbl{{width:100%;border-collapse:collapse;font-size:0.88rem}}
.tbl th{{color:{C['txt2']};font-weight:600;padding:8px 12px;border-bottom:1px solid {C['border']};text-align:left}}
.tbl td{{padding:7px 12px;border-bottom:1px solid {C['border']}40;color:{C['txt1']}}}
.tbl tr:hover td{{background:{C['card2']}}}
/* ── Responsive ── */
@media(max-width:900px){{
  .chart-row,.chart-row-3{{grid-template-columns:1fr}}
  .stats-row{{grid-template-columns:repeat(2,1fr)}}
  .container,.header,.tab-nav{{padding:16px 20px}}
}}
</style>
</head>
<body>

<div class="header">
  <h1>Discourse Network Analysis — Instagram</h1>
  <p>Kebijakan Energi Nuklir Indonesia · Analisis Media Sosial Instagram · {date_range}</p>
</div>

{TAB_NAV}

<div class="container">

<!-- ── Stats row ── -->
<div class="stats-row">
  <div class="stat-card"><div class="number">{total_posts:,}</div><div class="slabel">Total Post</div></div>
  <div class="stat-card"><div class="number">{total_actors:,}</div><div class="slabel">Akun Unik</div></div>
  <div class="stat-card"><div class="number" style="color:{C['pro']};">{n_pro}</div><div class="slabel">PRO Nuklir</div></div>
  <div class="stat-card"><div class="number" style="color:{C['kontra']};">{n_kontra}</div><div class="slabel">KONTRA Nuklir</div></div>
  <div class="stat-card"><div class="number" style="color:{C['netral']};">{n_netral}</div><div class="slabel">NETRAL</div></div>
  <div class="stat-card"><div class="number" style="color:{C['info']};">{n_pos}</div><div class="slabel">Sentimen Positif</div></div>
  <div class="stat-card"><div class="number" style="color:{C['kontra']};">{n_neg}</div><div class="slabel">Sentimen Negatif</div></div>
  <div class="stat-card"><div class="number">{avg_sent:.2f}</div><div class="slabel">Rata-rata Skor Sentimen</div></div>
</div>

<!-- ── Stance + Sentiment donuts ── -->
<div class="section">
  <h2>Distribusi Sikap &amp; Sentimen</h2>
  <div class="chart-row">
    <div><canvas id="chartStance"></canvas></div>
    <div><canvas id="chartSentiment"></canvas></div>
  </div>
</div>

<!-- ── Monthly trend ── -->
<div class="section">
  <h2>Tren Sikap per Bulan</h2>
  <canvas id="chartMonthly" style="max-height:280px;"></canvas>
</div>

<!-- ── Variable distribution ── -->
<div class="section">
  <h2>Distribusi Variabel Diskursus</h2>
  <canvas id="chartVar" style="max-height:300px;"></canvas>
</div>

<!-- ── Top accounts ── -->
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
    <tbody>{actor_rows_html}</tbody>
  </table>
</div>

<!-- ── Top hashtags ── -->
<div class="section">
  <h2>Top 25 Hashtag</h2>
  <canvas id="chartHashtag" style="max-height:400px;"></canvas>
</div>

<!-- ── Mention network + Buzzer side by side ── -->
<div class="chart-row">
  <div class="section" style="margin-bottom:0;">
    <h2>Top Mention Network (berdasarkan frekuensi)</h2>
    <table class="tbl">
      <thead><tr>
        <th>Dari Akun</th><th></th><th>Ke Akun</th><th>Frekuensi</th>
      </tr></thead>
      <tbody>{edge_rows_html}</tbody>
    </table>
  </div>
  <div class="section" style="margin-bottom:0;">
    <h2>Akun dengan Indikator Buzzer Tertinggi</h2>
    <table class="tbl">
      <thead><tr>
        <th>Akun</th><th>Followers</th><th>Following</th><th>Posts</th><th>Skor</th><th>Flags</th>
      </tr></thead>
      <tbody>{buzzer_rows_html}</tbody>
    </table>
  </div>
</div>

</div><!-- /container -->

<script>
const STANCE = {stance_json};
const SENT   = {sent_json};
const MONTHLY = {monthly_json};
const VAR    = {var_json};
const HTAG   = {htag_json};

const PRO_C    = "{C['pro']}";
const KON_C    = "{C['kontra']}";
const NET_C    = "{C['netral']}";
const POS_C    = "{C['info']}";
const NEG_C    = "{C['kontra']}";
const NEU_C    = "{C['netral']}";
const TXT1     = "{C['txt1']}";
const TXT2     = "{C['txt2']}";
const BORDER   = "{C['border']}";

const TICK  = {{ color: TXT2, font: {{ size: 11 }} }};
const GRID  = {{ color: BORDER }};
const LEG   = {{ labels: {{ color: TXT1 }}, position: 'bottom' }};

new Chart(document.getElementById('chartStance'), {{
  type: 'doughnut',
  data: {{
    labels: ['PRO', 'KONTRA', 'NETRAL'],
    datasets: [{{ data: [STANCE.pro, STANCE.kontra, STANCE.netral],
      backgroundColor: [PRO_C, KON_C, NET_C], borderWidth: 0 }}],
  }},
  options: {{
    plugins: {{
      legend: LEG,
      title: {{ display: true, text: 'Sikap terhadap Nuklir/PLTN', color: TXT1, font: {{ size: 14 }} }},
    }},
    cutout: '62%',
  }},
}});

new Chart(document.getElementById('chartSentiment'), {{
  type: 'doughnut',
  data: {{
    labels: ['POSITIVE', 'NEGATIVE', 'NEUTRAL'],
    datasets: [{{ data: [SENT.pos, SENT.neg, SENT.neu],
      backgroundColor: [POS_C, NEG_C, NEU_C], borderWidth: 0 }}],
  }},
  options: {{
    plugins: {{
      legend: LEG,
      title: {{ display: true, text: 'Distribusi Sentimen Caption', color: TXT1, font: {{ size: 14 }} }},
    }},
    cutout: '62%',
  }},
}});

new Chart(document.getElementById('chartMonthly'), {{
  type: 'bar',
  data: {{
    labels: MONTHLY.labels,
    datasets: [
      {{ label: 'PRO',    data: MONTHLY.pro,    backgroundColor: PRO_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'KONTRA', data: MONTHLY.kontra, backgroundColor: KON_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'NETRAL', data: MONTHLY.netral, backgroundColor: NET_C, stack: 'a', borderRadius: 2 }},
    ],
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: LEG }},
    scales: {{
      x: {{ stacked: true, ticks: TICK, grid: {{ color: BORDER }} }},
      y: {{ stacked: true, ticks: TICK, grid: GRID }},
    }},
  }},
}});

new Chart(document.getElementById('chartVar'), {{
  type: 'bar',
  data: {{
    labels: VAR.labels,
    datasets: [
      {{ label: 'PRO',    data: VAR.pro,    backgroundColor: PRO_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'KONTRA', data: VAR.kontra, backgroundColor: KON_C, stack: 'a', borderRadius: 2 }},
      {{ label: 'NETRAL', data: VAR.netral, backgroundColor: NET_C, stack: 'a', borderRadius: 2 }},
    ],
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    plugins: {{ legend: LEG }},
    scales: {{
      x: {{ stacked: true, ticks: TICK, grid: GRID }},
      y: {{ stacked: true, ticks: {{ color: TXT2, font: {{ size: 11 }} }} }},
    }},
  }},
}});

new Chart(document.getElementById('chartHashtag'), {{
  type: 'bar',
  data: {{
    labels: HTAG.labels,
    datasets: [{{ label: 'Post', data: HTAG.counts, backgroundColor: "{C['accent']}", borderRadius: 4 }}],
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: TICK, grid: GRID }},
      y: {{ ticks: {{ color: TXT2, font: {{ size: 11 }} }} }},
    }},
  }},
}});
</script>
</body>
</html>"""

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(HTML, encoding="utf-8")
print(f"[DONE] {OUTPUT}")
print(f"  Posts: {total_posts}, Actors: {total_actors}")
print(f"  PRO: {n_pro}, KONTRA: {n_kontra}, NETRAL: {n_netral}")
print(f"  Sentiment avg: {avg_sent:.3f}")
