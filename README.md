# DNA Nuclear Policy - Discourse Network Analysis

**Discourse Network Analysis (DNA) of Indonesian news coverage on nuclear energy policy (RUU EBET)**

> Extracts actor–stance–concept networks from news articles using LLM-based parsing, then generates an interactive stakeholder report.

---

## Live Report

**[https://FirzaCank.github.io/dna-nuclear-policy](https://FirzaCank.github.io/dna-nuclear-policy)**

The report is a single self-contained HTML file with:
- Interactive bipartite network: Institution → Policy Concept
- 8 Chart.js charts (positions, actor rankings, sentiment trends, etc.)
- Summary stats: total statements, unique actors, concepts, % PRO / KONTRA

---

## Pipeline

```
01_preprocess.py       Clean raw scraped articles
        ↓
02_extract_llm.py      LLM extraction: actor / stance / concept  (Gemini 2.5 Flash)
        ↓
03_build_edgelist.py   Build node & edge lists for DNA/SNA
        ↓
04_sentiment.py        Sentiment scoring per statement
        ↓
05_visualize_html.py   Generate self-contained HTML report
        ↓
06_export_gephi.py     (Optional) Export Gephi-ready CSVs
```

Full setup and run guide: [README_pipeline.md](README_pipeline.md)

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install pandas tqdm python-dotenv pyvis google-generativeai
echo "API_KEY=your_gemini_api_key" > .env

python 01_preprocess.py
python 02_extract_llm.py   # resumable — safe to stop/restart
python 03_build_edgelist.py
python 04_sentiment.py
python 05_visualize_html.py
# → output/report_dna.html
```


---

## Network Node Colors

| Color | Meaning |
|---|---|
| Green | PRO nuclear institution |
| Red | KONTRA nuclear institution |
| Grey | NETRAL institution |
| Orange box | Keyword / Policy concept |

---

## Tech Stack

- **LLM**: Gemini 2.5 Flash via `google-generativeai`
- **Network**: [pyvis](https://pyvis.readthedocs.io) (vis.js)
- **Charts**: Chart.js 4.4.0
- **Data**: pandas
- **Deployment**: GitHub Pages (single self-contained HTML)
