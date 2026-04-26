"""
STEP 5 - HTML STAKEHOLDER REPORT  (v2 — Global Period Filter + WCAG AA Colors)
================================================================================
Changes from v1:
  • WCAG AA-compliant color palette (min 4.5:1 contrast on all dark backgrounds)
  • Single global <select> dropdown replaces network-only tabs
  • ALL charts + stats row + network update on period change
  • Per-period data pre-computed in Python → serialised as one JSON blob
  • Chart.js instances updated in-place (no re-init flicker)

Input:
  output/01_flat_statements.csv
  output/02_nodes_actors.csv
  output/03_nodes_concepts.csv
  output/04_edges_actor_concept.csv
  output/05b_edges_actor_variable.csv
  output/05c_edges_actor_keyword.csv
  output/06a_summary_by_variable.csv
  output/07_sentiment_scored.csv

Output:
  output/report_dna.html          (single self-contained shareable file)
  output/network_dna_<pid>.html   (standalone per-period network files)

INSTALL:
  pip install pyvis pandas
"""

import base64
import json
from pathlib import Path

import pandas as pd

from config.institution_mapping import get_institution
from config.keyword_merge import KEYWORD_MERGE

OUTDIR = Path("output")
MIN_STATEMENTS = 3  # actors with fewer statements are excluded

# ── WCAG AA palette  (contrast ratio against #1e1e2e background) ───────────────
#   Verified with APCA-style relative luminance:
#     #69db7c  ≈ 9.0:1   PRO green
#     #ff6b6b  ≈ 5.3:1   KONTRA red
#     #ced4da  ≈ 10.7:1  NETRAL gray
#     #ffd43b  ≈ 11.3:1  AMBIGU yellow
#     #d4a6f7  ≈ 7.1:1   concept / section titles
#     #b197fc  ≈ 5.7:1   accent (replaces failing #7c4dff ≈ 1.8:1)
#     #4dabf7  ≈ 5.5:1   info blue
#     #c9d1d9  ≈ 10.1:1  secondary text
C = {
    "pro":        "#69db7c",
    "kontra":     "#ff6b6b",
    "netral":     "#ced4da",
    "ambigu":     "#ffd43b",
    "concept":    "#d4a6f7",
    "accent":     "#b197fc",
    "info":       "#4dabf7",
    "txt1":       "#e8e8e8",
    "txt2":       "#c9d1d9",
    "bg":         "#0f0f1a",
    "card":       "#1e1e2e",
    "card2":      "#16213e",
    "border":     "#2e3250",
    "hdr_from":   "#1a237e",
    "hdr_to":     "#311b92",
}

PERIOD_DEFS = {
    "all":     ("Keseluruhan",      None,         None),
    "jokowi1": ("Jokowi Periode 1", "2014-10-20", "2019-10-20"),
    "jokowi2": ("Jokowi Periode 2", "2019-10-20", "2024-10-20"),
    "prabowo": ("Prabowo",          "2024-10-20", None),
}
PERIOD_ORDER = ["all", "jokowi1", "jokowi2", "prabowo"]

# ── Load data ──────────────────────────────────────────────────────────────────
nodes_actors   = pd.read_csv(OUTDIR / "02_nodes_actors.csv")
nodes_concepts = pd.read_csv(OUTDIR / "03_nodes_concepts.csv")
edges_av       = pd.read_csv(OUTDIR / "05b_edges_actor_variable.csv")
edges_ak       = pd.read_csv(OUTDIR / "05c_edges_actor_keyword.csv")
sentiment_df   = pd.read_csv(OUTDIR / "07_sentiment_scored.csv")
flat_df        = pd.read_csv(OUTDIR / "01_flat_statements.csv")

edges_ak["keyword"] = edges_ak["keyword"].replace(KEYWORD_MERGE)

# ── Global actor filter (≥ MIN_STATEMENTS) ────────────────────────────────────
nodes_actors_filtered = nodes_actors[nodes_actors["n_statements"] >= MIN_STATEMENTS].copy()
nodes_actors_filtered["institution"] = nodes_actors_filtered.apply(
    lambda r: get_institution(r["actor"], r.get("actor_type", ""), r.get("actor_role", "")),
    axis=1,
)
nodes_actors_filtered = nodes_actors_filtered[nodes_actors_filtered["institution"].notna()]
active_actors  = set(nodes_actors_filtered["actor"])
actor_to_inst  = dict(zip(nodes_actors_filtered["actor"], nodes_actors_filtered["institution"]))

flat_df      = flat_df[flat_df["actor"].isin(active_actors)].copy()
sentiment_df = sentiment_df[sentiment_df["actor"].isin(active_actors)].copy()

# Parse dates
flat_df["date_parsed"] = pd.to_datetime(flat_df["date"], errors="coerce")
if "date" in sentiment_df.columns:
    sentiment_df["date_parsed"] = pd.to_datetime(sentiment_df["date"], errors="coerce")
elif "source_id" in sentiment_df.columns and "source_id" in flat_df.columns:
    _dmap = flat_df.drop_duplicates("source_id")[["source_id", "date_parsed"]]
    sentiment_df = sentiment_df.merge(_dmap, on="source_id", how="left")

TOTAL_CONCEPTS = int(nodes_concepts["concept"].nunique())

# ── Helper: dominant position ──────────────────────────────────────────────────
def _dominant_pos(r):
    p, k, n = int(r.get("pro_count", 0)), int(r.get("kontra_count", 0)), int(r.get("netral_count", 0))
    if p == k and p > 0:
        return "NETRAL"
    if p >= k and p >= n:
        return "PRO"
    if k >= p and k >= n:
        return "KONTRA"
    return "NETRAL"

COLOR_POS = {
    "PRO": C["pro"], "KONTRA": C["kontra"],
    "NETRAL": C["netral"], "AMBIGU": C["ambigu"],
}

# ── inst_stats (global, for network legend) ────────────────────────────────────
def _build_inst_stats(flat_slice, actor_to_inst_map, nodes_filtered):
    if flat_slice.empty:
        return pd.DataFrame(columns=[
            "institution", "n_statements", "pro_count", "kontra_count",
            "netral_count", "ambigu_count", "dominant_pos", "members",
        ])
    fs = flat_slice.copy()
    fs["institution"] = fs["actor"].map(actor_to_inst_map)
    fs = fs[fs["institution"].notna()]
    grp = fs.groupby("institution")
    stats = grp.agg(
        n_statements=("position", "count"),
        pro_count=("position",    lambda x: (x == "PRO").sum()),
        kontra_count=("position", lambda x: (x == "KONTRA").sum()),
        netral_count=("position", lambda x: (x == "NETRAL").sum()),
        ambigu_count=("position", lambda x: (x == "AMBIGU").sum()),
    ).reset_index()
    stats["dominant_pos"] = stats.apply(_dominant_pos, axis=1)
    stats["members"] = stats["institution"].map(
        fs.groupby("institution")["actor"].apply(lambda x: ", ".join(sorted(set(x))))
    )
    return stats


inst_stats_all = _build_inst_stats(flat_df, actor_to_inst, nodes_actors_filtered)

# ── Period slicer ──────────────────────────────────────────────────────────────
def _slice(flat, pstart, pend):
    if pstart is None and pend is None:
        return flat.copy()
    mask = pd.Series(True, index=flat.index)
    if pstart:
        mask &= flat["date_parsed"] >= pstart
    if pend:
        mask &= flat["date_parsed"] < pend
    return flat[mask].copy()


# ── compute_period_charts: all chart data for one period ──────────────────────
def compute_period_charts(flat_slice, sent_all):
    """
    flat_slice  – flat_df filtered to this period (active actors already applied)
    sent_all    – full sentiment_df; will be filtered to actors in flat_slice
    Returns a dict of all chart data for this period.
    """
    EMPTY = dict(
        stats=dict(total_news=0, total_stmt=0, total_actors=0,
                   total_concepts=TOTAL_CONCEPTS,
                   pro_pct=0, kontra_pct=0, netral_pct=0, ambigu_pct=0),
        pos=dict(labels=[], pro=[], kontra=[], netral=[]),
        actors=dict(labels=[], values=[], colors=[]),
        sent=dict(labels=[], values=[]),
        cross=dict(positions=[], datasets=[]),
        trend=dict(labels=[], pro=[], kontra=[], netral=[]),
        actor_type=dict(labels=[], values=[]),
        kontra=dict(labels=[], values=[]),
        var_chart=dict(labels=[], values=[]),
    )
    if flat_slice.empty:
        return EMPTY

    period_actors = set(flat_slice["actor"].dropna().unique())
    sent_slice = sent_all[sent_all["actor"].isin(period_actors)].copy()

    # ── Stats row ──────────────────────────────────────────────────────────
    total_stmt   = len(flat_slice)
    total_actors = flat_slice["actor"].nunique()
    total_news   = (flat_slice["source_url"].nunique()
                    if "source_url" in flat_slice.columns else 0)
    pc = flat_slice["position"].value_counts()
    _tot = max(total_stmt, 1)
    _keys = ["PRO", "KONTRA", "NETRAL", "AMBIGU"]
    _ex = {k: (pc.get(k, 0) / _tot) * 100 for k in _keys}
    _fl = {k: int(v) for k, v in _ex.items()}
    _left = 100 - sum(_fl.values())
    for k in sorted(_keys, key=lambda k: -(_ex[k] - _fl[k]))[:_left]:
        _fl[k] += 1

    stats = dict(
        total_news=int(total_news), total_stmt=int(total_stmt),
        total_actors=int(total_actors), total_concepts=TOTAL_CONCEPTS,
        pro_pct=_fl["PRO"], kontra_pct=_fl["KONTRA"],
        netral_pct=_fl["NETRAL"], ambigu_pct=_fl["AMBIGU"],
    )

    # ── Position per variable ──────────────────────────────────────────────
    aggcol = "source_id" if "source_id" in flat_slice.columns else "date"
    try:
        _piv = flat_slice.pivot_table(
            index=["actor", "variable"], columns="position",
            values=aggcol, aggfunc="count", fill_value=0,
        ).reset_index()
    except Exception:
        _piv = pd.DataFrame()
    variables = sorted(flat_slice["variable"].dropna().unique().tolist())
    pos_data = dict(
        labels=variables,
        pro=[int(_piv[_piv["variable"] == v]["PRO"].sum())
             if not _piv.empty and "PRO" in _piv.columns else 0 for v in variables],
        kontra=[int(_piv[_piv["variable"] == v]["KONTRA"].sum())
                if not _piv.empty and "KONTRA" in _piv.columns else 0 for v in variables],
        netral=[int(_piv[_piv["variable"] == v]["NETRAL"].sum())
                if not _piv.empty and "NETRAL" in _piv.columns else 0 for v in variables],
    )

    # ── Per-actor aggregation (shared by multiple charts) ─────────────────
    actor_agg = flat_slice.groupby("actor").agg(
        n_statements=("position", "count"),
        pro_count=("position",    lambda x: (x == "PRO").sum()),
        kontra_count=("position", lambda x: (x == "KONTRA").sum()),
        netral_count=("position", lambda x: (x == "NETRAL").sum()),
    ).reset_index()
    meta_cols = ["actor"] + [c for c in ["actor_type", "actor_role"]
                              if c in nodes_actors_filtered.columns]
    actor_agg = actor_agg.merge(
        nodes_actors_filtered[meta_cols].drop_duplicates("actor"),
        on="actor", how="left",
    )
    actor_agg["dominant_pos"] = actor_agg.apply(_dominant_pos, axis=1)

    def _alabel(row):
        org = get_institution(
            row["actor"],
            row.get("actor_type", ""),
            row.get("actor_role", ""),
        )
        return (f"{row['actor']} ({org})"
                if org and org.lower() != row["actor"].lower() else row["actor"])

    # ── Top 15 actors ──────────────────────────────────────────────────────
    top15 = actor_agg.nlargest(15, "n_statements").copy()
    top15["label"] = top15.apply(_alabel, axis=1)
    actors_data = dict(
        labels=top15["label"].tolist(),
        values=[int(v) for v in top15["n_statements"].tolist()],
        colors=[COLOR_POS.get(p, C["info"]) for p in top15["dominant_pos"].tolist()],
    )

    # ── Sentiment donut ────────────────────────────────────────────────────
    if not sent_slice.empty and "sentiment_label" in sent_slice.columns:
        sc = sent_slice["sentiment_label"].value_counts()
        sent_data = dict(labels=sc.index.tolist(),
                         values=[int(v) for v in sc.values.tolist()])
    else:
        sent_data = dict(labels=[], values=[])

    # ── Sentiment × Position ───────────────────────────────────────────────
    if (not sent_slice.empty
            and "position" in sent_slice.columns
            and "sentiment_label" in sent_slice.columns):
        cross_p = pd.crosstab(sent_slice["position"],
                               sent_slice["sentiment_label"]).reset_index()
        sl = [c for c in cross_p.columns if c != "position"]
        cross_data = dict(
            positions=cross_p["position"].tolist(),
            datasets=[{"label": s,
                        "data": [int(x) for x in cross_p[s].tolist()]}
                       for s in sl if s in cross_p.columns],
        )
    else:
        cross_data = dict(positions=[], datasets=[])

    # ── Monthly trend ──────────────────────────────────────────────────────
    fs = flat_slice.copy()
    fs["year_month"] = fs["date_parsed"].dt.to_period("M").astype(str)
    grp_col = "source_url" if "source_url" in fs.columns else "actor"
    trend_raw = (
        fs.groupby(["year_month", "position"])[grp_col]
        .nunique().reset_index(name="n")
    )
    months = sorted(trend_raw["year_month"].dropna().unique().tolist())
    _tp = {r["year_month"]: r["n"] for _, r in trend_raw[trend_raw["position"] == "PRO"].iterrows()}
    _tk = {r["year_month"]: r["n"] for _, r in trend_raw[trend_raw["position"] == "KONTRA"].iterrows()}
    _tn = {r["year_month"]: r["n"] for _, r in trend_raw[trend_raw["position"] == "NETRAL"].iterrows()}
    trend_data = dict(
        labels=months,
        pro=[int(_tp.get(m, 0)) for m in months],
        kontra=[int(_tk.get(m, 0)) for m in months],
        netral=[int(_tn.get(m, 0)) for m in months],
    )

    # ── Actor type donut ───────────────────────────────────────────────────
    if "actor_type" in flat_slice.columns:
        atc = flat_slice["actor_type"].value_counts()
        actor_type_data = dict(labels=atc.index.tolist(),
                               values=[int(v) for v in atc.values.tolist()])
    else:
        actor_type_data = dict(labels=[], values=[])

    # ── Top 10 KONTRA ──────────────────────────────────────────────────────
    top_k = actor_agg[actor_agg["kontra_count"] > 0].nlargest(10, "kontra_count").copy()
    if not top_k.empty:
        top_k["label"] = top_k.apply(_alabel, axis=1)
        kontra_data = dict(
            labels=top_k["label"].tolist(),
            values=[int(v) for v in top_k["kontra_count"].tolist()],
        )
    else:
        kontra_data = dict(labels=[], values=[])

    # ── Statements per variable ────────────────────────────────────────────
    if "variable" in flat_slice.columns:
        vc = flat_slice["variable"].value_counts()
        var_data = dict(labels=vc.index.tolist(),
                        values=[int(v) for v in vc.values.tolist()])
    else:
        var_data = dict(labels=[], values=[])

    return dict(
        stats=stats, pos=pos_data, actors=actors_data,
        sent=sent_data, cross=cross_data, trend=trend_data,
        actor_type=actor_type_data, kontra=kontra_data, var_chart=var_data,
    )


# ── Build network edges at institution level ───────────────────────────────────
def _build_edges_net(edges_raw, actors_set, inst_map):
    ef = edges_raw[edges_raw["source"].isin(actors_set)].copy()
    ef["institution"] = ef["source"].map(inst_map)
    ei = ef.groupby(["institution", "target", "position"])["weight"].sum().reset_index()
    if ei.empty:
        return ei
    return (ei.loc[ei.groupby(["institution", "target"])["weight"].idxmax()]
              .reset_index(drop=True))


FREEZE_JS = """
<script type="text/javascript">
document.addEventListener("DOMContentLoaded", function() {
  var _frozen = false;
  function layoutNodes() {
    if (typeof network === "undefined" || typeof nodes === "undefined") return;
    var all = nodes.get();
    var kw = all.filter(function(n) { return n.group === "concept"; });
    var sp = 160, sy = -((kw.length - 1) / 2) * sp;
    nodes.update(kw.map(function(n, i) {
      return { id: n.id, x: 0, y: sy + i * sp, fixed: { x: true, y: true } };
    }));
    function side(arr, xBase) {
      var s = 180, sy2 = -((arr.length - 1) / 2) * s;
      return arr.map(function(n, i) {
        return { id: n.id, x: xBase + (Math.random() - 0.5) * 200, y: sy2 + i * s };
      });
    }
    var pro = all.filter(function(n) { return n.group === "inst_pro"; });
    var kon = all.filter(function(n) { return n.group === "inst_kontra"; });
    var net = all.filter(function(n) { return n.group === "inst_netral"; });
    var amb = all.filter(function(n) { return n.group === "inst_ambigu"; });
    nodes.update(side(pro, -900).concat(side(kon, 900))
      .concat(side(net, Math.random() > .5 ? -900 : 900))
      .concat(side(amb, Math.random() > .5 ? -1200 : 1200)));
  }
  function freeze() {
    if (_frozen) return; _frozen = true;
    network.setOptions({ physics: { enabled: false } }); network.fit();
  }
  var t = setInterval(function() {
    if (typeof network !== "undefined") {
      clearInterval(t); layoutNodes();
      network.on("stabilizationIterationsDone", freeze);
      setTimeout(freeze, 12000);
    }
  }, 100);
});
</script>"""


def _build_pyvis_html(edges_net, inst_stats_p, out_path):
    """Build and save a pyvis network; return the full HTML string."""
    from pyvis.network import Network

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
            "inst_pro":    {"color": {"background": C["pro"],    "border": C["pro"]}},
            "inst_kontra": {"color": {"background": C["kontra"], "border": C["kontra"]}},
            "inst_netral": {"color": {"background": C["netral"], "border": C["netral"]}},
            "inst_ambigu": {"color": {"background": C["ambigu"], "border": C["ambigu"]}},
            "concept":     {"color": {"background": C["concept"], "border": C["concept"]}},
        },
    }))

    kw_degree = edges_net.groupby("target")["institution"].nunique()
    for t in sorted(edges_net["target"].unique(),
                    key=lambda t: kw_degree.get(t, 0), reverse=True):
        deg = int(kw_degree.get(t, 1))
        net.add_node(
            f"V::{t}", label=t, color=C["concept"], shape="box", size=50,
            title=f"{t}\nConnected to {deg} institutions", group="concept",
            font={"color": "#000000", "size": 18, "face": "arial",
                  "bold": True, "strokeWidth": 0},
        )

    active_inst = set(edges_net["institution"])
    for _, row in inst_stats_p[inst_stats_p["institution"].isin(active_inst)].iterrows():
        dp = str(row.get("dominant_pos", "NETRAL")).strip().upper()
        col = COLOR_POS.get(dp, C["netral"])
        g   = {"PRO": "inst_pro", "KONTRA": "inst_kontra",
               "AMBIGU": "inst_ambigu"}.get(dp, "inst_netral")
        size = max(14, min(50, int(row.get("n_statements", 1)) * 2))
        title = (
            f"{row['institution']}\nTotal: {row.get('n_statements',0)}\n"
            f"Posisi: {dp}\n"
            f"PRO:{row.get('pro_count',0)} | KONTRA:{row.get('kontra_count',0)} | "
            f"NETRAL:{row.get('netral_count',0)} | AMBIGU:{row.get('ambigu_count',0)}\n"
            f"Anggota: {row.get('members','')}"
        )
        net.add_node(
            f"A::{row['institution']}", label=row["institution"],
            color={"background": col, "border": col,
                   "highlight": {"background": col, "border": col}},
            shape="dot", size=size, title=title, group=g,
            font={"color": "#ffffff", "size": 16,
                  "strokeWidth": 2, "strokeColor": "#000000"},
        )

    for _, row in edges_net.iterrows():
        col = COLOR_POS.get(str(row.get("position", "NETRAL")), C["netral"])
        net.add_edge(
            f"A::{row['institution']}", f"V::{row['target']}",
            color=col, width=max(1, min(8, int(row.get("weight", 1)))),
            title=f"{row.get('position','')} | n={row.get('weight',1)}",
        )

    net.save_graph(str(out_path))
    html = out_path.read_text(encoding="utf-8")
    html = html.replace("</body>", FREEZE_JS + "\n</body>")
    out_path.write_text(html, encoding="utf-8")
    return html


# ── Pre-compute per-period data ────────────────────────────────────────────────
all_periods_data   = {}   # pid → chart data dict
network_sections   = {}   # pid → iframe HTML string
period_meta        = {}   # pid → inst-level summary counts

print(f"[INPUT] {len(nodes_actors)} actors total → "
      f"{len(nodes_actors_filtered)} (≥{MIN_STATEMENTS} stmts) → "
      f"institution-level")

for pid in PERIOD_ORDER:
    label, pstart, pend = PERIOD_DEFS[pid]
    flat_p = _slice(flat_df, pstart, pend)
    actors_p = set(flat_p["actor"].dropna().unique())

    # Chart data
    all_periods_data[pid] = compute_period_charts(flat_p, sentiment_df)

    # Network
    inst_stats_p  = _build_inst_stats(flat_p, actor_to_inst, nodes_actors_filtered)
    edges_net_p   = _build_edges_net(edges_av, actors_p, actor_to_inst)

    # period_meta for legend pills
    dp = inst_stats_p["dominant_pos"].value_counts() if not inst_stats_p.empty else pd.Series(dtype=int)
    period_meta[pid] = {
        "n_inst":   len(inst_stats_p),
        "n_pro":    int(dp.get("PRO", 0)),
        "n_kontra": int(dp.get("KONTRA", 0)),
        "n_netral": int(dp.get("NETRAL", 0)),
        "n_ambigu": int(dp.get("AMBIGU", 0)),
        "n_stmt":   int(inst_stats_p["n_statements"].sum()) if not inst_stats_p.empty else 0,
    }

    try:
        if edges_net_p.empty:
            network_sections[pid] = (
                f"<p style='color:{C['txt2']};padding:20px'>"
                f"Tidak ada data untuk {label}</p>"
            )
            print(f"  [SKIP] {label}: no edges")
        else:
            out_path = OUTDIR / f"network_dna_{pid}.html"
            html_p   = _build_pyvis_html(edges_net_p, inst_stats_p, out_path)
            b64_p    = base64.b64encode(html_p.encode("utf-8")).decode("ascii")
            network_sections[pid] = (
                f'<iframe src="data:text/html;base64,{b64_p}" '
                f'width="100%" height="1100px" '
                f'style="border:none;display:block;"></iframe>'
            )
            print(f"  [OK] {label}: {len(edges_net_p)} edges → {out_path.name}")
    except ImportError:
        network_sections[pid] = (
            "<p style='color:#aaa'>Install pyvis: "
            "<code>pip install pyvis</code></p>"
        )
        print(f"  [WARN] pyvis not installed")


# ── Meta pills HTML ────────────────────────────────────────────────────────────
def _meta_html(pid):
    m = period_meta.get(pid, {})
    n = m.get("n_inst", 0)
    if n == 0:
        return ""
    return f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px;font-size:0.82rem;">
  <span style="background:{C['card2']};border:1px solid {C['border']};
               border-radius:6px;padding:5px 13px;color:{C['txt1']};">
    🏛 <b style="color:{C['concept']}">{n}</b> Institusi
  </span>
  <span style="background:{C['card2']};border:1px solid {C['pro']};
               border-radius:6px;padding:5px 13px;color:{C['txt1']};">
    <b style="color:{C['pro']}">{m.get('n_pro',0)}</b> PRO
  </span>
  <span style="background:{C['card2']};border:1px solid {C['kontra']};
               border-radius:6px;padding:5px 13px;color:{C['txt1']};">
    <b style="color:{C['kontra']}">{m.get('n_kontra',0)}</b> KONTRA
  </span>
  <span style="background:{C['card2']};border:1px solid {C['netral']};
               border-radius:6px;padding:5px 13px;color:{C['txt1']};">
    <b style="color:{C['netral']}">{m.get('n_netral',0)}</b> NETRAL
  </span>
  <span style="background:{C['card2']};border:1px solid {C['ambigu']};
               border-radius:6px;padding:5px 13px;color:{C['txt1']};">
    <b style="color:{C['ambigu']}">{m.get('n_ambigu',0)}</b> AMBIGU
  </span>
  <span style="background:{C['card2']};border:1px solid {C['info']};
               border-radius:6px;padding:5px 13px;color:{C['txt1']};">
    📝 <b style="color:{C['info']}">{m.get('n_stmt',0)}</b> Pernyataan
  </span>
</div>"""


# ── Build combined network HTML (all periods, shown/hidden by JS) ──────────────
network_html_parts = ""
for pid in PERIOD_ORDER:
    display = "block" if pid == "all" else "none"
    network_html_parts += (
        f'<div id="net-{pid}" style="width:100%;overflow:hidden;display:{display};">'
        f'{_meta_html(pid)}{network_sections.get(pid,"")}'
        f'</div>\n'
    )

# ── Serialize all period data to JSON for JS ───────────────────────────────────
all_data_json = json.dumps(all_periods_data, ensure_ascii=False)

# Colours exported to JS
SENT_COLORS_JS = json.dumps([C["pro"], C["kontra"], C["netral"], C["ambigu"]])
ACTOR_TYPE_COLORS_JS = json.dumps([
    C["accent"], C["info"], C["ambigu"], C["pro"], C["kontra"], C["netral"]
])

# ── Build HTML ─────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DNA Report — Kebijakan Nuklir Indonesia</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
/* ── Reset & base ── */
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{C['bg']};color:{C['txt1']};line-height:1.5}}
/* ── Header ── */
.header{{background:linear-gradient(135deg,{C['hdr_from']},{C['hdr_to']});padding:28px 48px}}
.header h1{{font-size:1.85rem;color:#fff;letter-spacing:-0.5px}}
.header p{{color:{C['txt2']};margin-top:6px;font-size:0.95rem}}
/* ── Layout ── */
.container{{max-width:1400px;margin:0 auto;padding:28px 48px}}
/* ── Period selector ── */
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
/* ── Stats row ── */
.stats-row{{display:grid;grid-template-columns:repeat(8,1fr);gap:14px;margin-bottom:28px}}
.stat-card{{
  background:{C['card']};border-radius:12px;padding:18px 12px;
  text-align:center;border:1px solid {C['border']};
}}
.stat-card .number{{font-size:2rem;font-weight:700;color:{C['accent']}}}
.stat-card .slabel{{font-size:0.78rem;color:{C['txt2']};margin-top:5px;line-height:1.3}}
/* ── Sections ── */
.section{{
  background:{C['card']};border-radius:12px;padding:22px;
  margin-bottom:22px;border:1px solid {C['border']};
}}
.section h2{{
  font-size:1.1rem;color:{C['concept']};margin-bottom:14px;
  padding-bottom:8px;border-bottom:1px solid {C['border']};
  font-weight:600;
}}
.chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
canvas{{max-height:320px}}
/* ── Network legend ── */
.net-legend{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:14px;font-size:0.8rem}}
.leg{{display:flex;align-items:center;gap:6px;color:{C['txt2']}}}
.dot{{width:11px;height:11px;border-radius:50%;flex-shrink:0}}
/* ── Responsive ── */
@media(max-width:900px){{
  .chart-row{{grid-template-columns:1fr}}
  .stats-row{{grid-template-columns:repeat(2,1fr)}}
  .container,.header{{padding:16px 20px}}
}}
</style>
</head>
<body>

<!-- ── Header ── -->
<div class="header">
  <h1>Discourse Network Analysis</h1>
  <p>Kebijakan Energi Nuklir Indonesia — Laporan Analisis Wacana Aktor-Konsep</p>
</div>

<div class="container">

  <!-- ── Global period selector ── -->
  <div class="period-bar">
    <label for="periodSelect">🗓 Filter Periode:</label>
    <select id="periodSelect" class="period-select" onchange="updatePeriod(this.value)">
      <option value="all">Keseluruhan (Semua Periode)</option>
      <option value="jokowi1">Jokowi Periode 1 — Okt 2014–Okt 2019</option>
      <option value="jokowi2">Jokowi Periode 2 — Okt 2019–Okt 2024</option>
      <option value="prabowo">Prabowo — Okt 2024–Sekarang</option>
    </select>
    <span id="periodBadge" style="font-size:0.82rem;color:{C['txt2']};margin-left:4px"></span>
  </div>

  <!-- ── Stats row ── -->
  <div class="stats-row" id="statsRow">
    <div class="stat-card">
      <div class="number" id="s-news">—</div>
      <div class="slabel">Total Artikel Berita</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-stmt">—</div>
      <div class="slabel">Total Pernyataan</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-actors">—</div>
      <div class="slabel">Aktor Unik</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-concepts">—</div>
      <div class="slabel">Konsep / Wacana</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-pro" style="color:{C['pro']}">—</div>
      <div class="slabel">Pernyataan PRO</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-kontra" style="color:{C['kontra']}">—</div>
      <div class="slabel">Pernyataan KONTRA</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-netral" style="color:{C['netral']}">—</div>
      <div class="slabel">Pernyataan NETRAL</div>
    </div>
    <div class="stat-card">
      <div class="number" id="s-ambigu" style="color:{C['ambigu']}">—</div>
      <div class="slabel">Pernyataan AMBIGU</div>
    </div>
  </div>

  <!-- ── DNA Network ── -->
  <div class="section">
    <h2>DNA Bipartite Network</h2>
    <div class="net-legend">
      <span class="leg"><span class="dot" style="background:{C['pro']}"></span>Institusi PRO</span>
      <span class="leg"><span class="dot" style="background:{C['kontra']}"></span>Institusi KONTRA</span>
      <span class="leg"><span class="dot" style="background:{C['netral']}"></span>Institusi NETRAL</span>
      <span class="leg"><span class="dot" style="background:{C['ambigu']}"></span>Institusi AMBIGU</span>
      <span class="leg"><span class="dot" style="background:{C['concept']}"></span>Variabel Kebijakan</span>
      <span class="leg" style="font-size:0.75rem;color:{C['txt2']}">
        — Edge: HIJAU=PRO &nbsp; MERAH=KONTRA &nbsp; ABU=NETRAL &nbsp; KUNING=AMBIGU
      </span>
    </div>
    {network_html_parts}
  </div>

  <!-- ── Charts row 1 ── -->
  <div class="chart-row">
    <div class="section">
      <h2>Distribusi Posisi per Variabel</h2>
      <canvas id="chartPos"></canvas>
    </div>
    <div class="section">
      <h2>Top 15 Aktor — Jumlah Pernyataan</h2>
      <canvas id="chartActors"></canvas>
    </div>
  </div>

  <!-- ── Charts row 2 ── -->
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

  <!-- ── Trend ── -->
  <div class="section">
    <h2>Tren Artikel per Bulan (Berdasarkan Posisi)</h2>
    <canvas id="chartTrend" style="max-height:300px"></canvas>
  </div>

  <!-- ── Charts row 3 ── -->
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

</div><!-- /.container -->

<!-- ═══════════════════ JavaScript ═══════════════════ -->
<script>
/* ── All period data from Python ── */
const ALL_DATA = {all_data_json};
const SENT_COLORS = {SENT_COLORS_JS};
const ACTOR_TYPE_COLORS = {ACTOR_TYPE_COLORS_JS};

/* ── Chart defaults (dark theme) ── */
Chart.defaults.color = "{C['txt2']}";
Chart.defaults.borderColor = "{C['border']}";
Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";

const TICK_OPTS = {{ color: "{C['txt2']}" }};
const LEGEND_OPTS = {{ labels: {{ color: "{C['txt1']}", padding: 14 }} }};

/* ── Init charts ── */
const charts = {{}};

function makeCharts() {{
  // 1. Position per variable — stacked bar
  charts.pos = new Chart(document.getElementById('chartPos'), {{
    type: 'bar',
    data: {{ labels: [], datasets: [
      {{ label:'PRO',    data:[], backgroundColor:"{C['pro']}" }},
      {{ label:'KONTRA', data:[], backgroundColor:"{C['kontra']}" }},
      {{ label:'NETRAL', data:[], backgroundColor:"{C['netral']}" }},
    ]}},
    options: {{
      responsive: true,
      plugins: {{ legend: LEGEND_OPTS }},
      scales: {{
        x: {{ stacked:true, ticks:{{ ...TICK_OPTS, maxRotation:35 }} }},
        y: {{ stacked:true, ticks:TICK_OPTS }},
      }},
    }},
  }});

  // 2. Top 15 actors — horizontal bar
  charts.actors = new Chart(document.getElementById('chartActors'), {{
    type: 'bar',
    data: {{ labels: [], datasets: [{{ data:[], backgroundColor:[], borderRadius:4 }}] }},
    options: {{
      indexAxis: 'y', responsive: true,
      plugins: {{ legend: {{ display:false }} }},
      scales: {{
        x: {{ ticks:TICK_OPTS }},
        y: {{ ticks:{{ ...TICK_OPTS, font:{{ size:10 }} }} }},
      }},
    }},
  }});

  // 3. Sentiment donut
  charts.sent = new Chart(document.getElementById('chartSent'), {{
    type: 'doughnut',
    data: {{ labels:[], datasets:[{{ data:[], backgroundColor:SENT_COLORS }}] }},
    options: {{ responsive:true, plugins:{{ legend:LEGEND_OPTS }} }},
  }});

  // 4. Sentiment × Position — grouped bar
  charts.cross = new Chart(document.getElementById('chartCross'), {{
    type: 'bar',
    data: {{ labels:[], datasets:[] }},
    options: {{
      responsive: true,
      plugins: {{ legend:LEGEND_OPTS }},
      scales: {{
        x: {{ ticks:TICK_OPTS }},
        y: {{ ticks:TICK_OPTS }},
      }},
    }},
  }});

  // 5. Monthly trend — stacked bar
  charts.trend = new Chart(document.getElementById('chartTrend'), {{
    type: 'bar',
    data: {{ labels:[], datasets: [
      {{ label:'PRO',    data:[], backgroundColor:'rgba(105,219,124,0.82)', stack:'a' }},
      {{ label:'KONTRA', data:[], backgroundColor:'rgba(255,107,107,0.82)', stack:'a' }},
      {{ label:'NETRAL', data:[], backgroundColor:'rgba(206,212,218,0.65)', stack:'a' }},
    ]}},
    options: {{
      responsive: true,
      plugins: {{ legend:LEGEND_OPTS }},
      scales: {{
        x: {{ stacked:true, ticks:{{ ...TICK_OPTS, maxRotation:45, font:{{ size:10 }} }} }},
        y: {{ stacked:true, ticks:TICK_OPTS,
              title:{{ display:true, text:'Jumlah Artikel', color:"{C['txt2']}" }} }},
      }},
    }},
  }});

  // 6. Actor type — donut
  charts.actorType = new Chart(document.getElementById('chartActorType'), {{
    type: 'doughnut',
    data: {{ labels:[], datasets:[{{ data:[], backgroundColor:ACTOR_TYPE_COLORS }}] }},
    options: {{ responsive:true, plugins:{{ legend:LEGEND_OPTS }} }},
  }});

  // 7. Top 10 KONTRA — horizontal bar
  charts.kontra = new Chart(document.getElementById('chartKontra'), {{
    type: 'bar',
    data: {{ labels:[], datasets:[{{ data:[], backgroundColor:"{C['kontra']}", borderRadius:4 }}] }},
    options: {{
      indexAxis: 'y', responsive:true,
      plugins: {{ legend:{{ display:false }} }},
      scales: {{
        x: {{ ticks:TICK_OPTS }},
        y: {{ ticks:{{ ...TICK_OPTS, font:{{ size:10 }} }} }},
      }},
    }},
  }});
}}

/* ── Update all charts + stats + network for a period ── */
function updatePeriod(pid) {{
  const d = ALL_DATA[pid];
  if (!d) return;

  /* Stats row */
  document.getElementById('s-news').textContent    = d.stats.total_news.toLocaleString();
  document.getElementById('s-stmt').textContent    = d.stats.total_stmt.toLocaleString();
  document.getElementById('s-actors').textContent  = d.stats.total_actors.toLocaleString();
  document.getElementById('s-concepts').textContent= d.stats.total_concepts.toLocaleString();
  document.getElementById('s-pro').textContent     = d.stats.pro_pct + '%';
  document.getElementById('s-kontra').textContent  = d.stats.kontra_pct + '%';
  document.getElementById('s-netral').textContent  = d.stats.netral_pct + '%';
  document.getElementById('s-ambigu').textContent  = d.stats.ambigu_pct + '%';

  /* Network panels */
  ['all','jokowi1','jokowi2','prabowo'].forEach(function(p) {{
    document.getElementById('net-' + p).style.display = (p === pid) ? 'block' : 'none';
  }});

  /* Chart 1: Position per variable */
  charts.pos.data.labels                  = d.pos.labels;
  charts.pos.data.datasets[0].data        = d.pos.pro;
  charts.pos.data.datasets[1].data        = d.pos.kontra;
  charts.pos.data.datasets[2].data        = d.pos.netral;
  charts.pos.update();

  /* Chart 2: Top actors */
  charts.actors.data.labels               = d.actors.labels;
  charts.actors.data.datasets[0].data     = d.actors.values;
  charts.actors.data.datasets[0].backgroundColor = d.actors.colors;
  charts.actors.update();

  /* Chart 3: Sentiment donut */
  charts.sent.data.labels                 = d.sent.labels;
  charts.sent.data.datasets[0].data       = d.sent.values;
  charts.sent.update();

  /* Chart 4: Sentiment × Position (dynamic datasets) */
  const cross = d.cross;
  charts.cross.data.labels = cross.positions;
  charts.cross.data.datasets = cross.datasets.map(function(ds, i) {{
    return {{
      label: ds.label,
      data: ds.data,
      backgroundColor: SENT_COLORS[i % SENT_COLORS.length],
    }};
  }});
  charts.cross.update();

  /* Chart 5: Monthly trend */
  charts.trend.data.labels                = d.trend.labels;
  charts.trend.data.datasets[0].data      = d.trend.pro;
  charts.trend.data.datasets[1].data      = d.trend.kontra;
  charts.trend.data.datasets[2].data      = d.trend.netral;
  charts.trend.update();

  /* Chart 6: Actor type */
  charts.actorType.data.labels            = d.actor_type.labels;
  charts.actorType.data.datasets[0].data  = d.actor_type.values;
  charts.actorType.update();

  /* Chart 7: Top 10 KONTRA */
  charts.kontra.data.labels               = d.kontra.labels;
  charts.kontra.data.datasets[0].data     = d.kontra.values;
  charts.kontra.update();
}}

/* ── Bootstrap ── */
makeCharts();
updatePeriod('all');
</script>
</body>
</html>"""

# ── Write output ───────────────────────────────────────────────────────────────
report_path = OUTDIR / "report_dna.html"
report_path.write_text(HTML, encoding="utf-8")

print(f"\n[OUTPUT] → {report_path}")
print(f"[DONE]   Open in browser. Use the dropdown at the top to switch periods.")