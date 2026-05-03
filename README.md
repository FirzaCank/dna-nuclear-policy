# DNA Nuclear Policy — Discourse Network Analysis

**Multi-platform Discourse Network Analysis (DNA) of Indonesian public discourse on nuclear energy policy (RUU EBET / PLTN)**

Extracts actor–stance–concept networks from news articles and social media (Instagram, YouTube, Facebook) using LLM-based parsing, then generates interactive dashboards filterable by political era.

---

## Live Dashboards

> **[https://firzacank.github.io/dna-nuclear-policy](https://firzacank.github.io/dna-nuclear-policy)**

| Dashboard | Data | Volume |
|---|---|---|
| [Berita Nasional](https://firzacank.github.io/dna-nuclear-policy/report_dna.html) | News articles | 500+ articles |
| [Instagram](https://firzacank.github.io/dna-nuclear-policy/socmed_report.html) | IG captions | 1,769 posts |
| [YouTube](https://firzacank.github.io/dna-nuclear-policy/youtube_report.html) | Video titles + descriptions | 559 videos |
| [Facebook](https://firzacank.github.io/dna-nuclear-policy/facebook_report.html) | FB post captions | 931 posts |

All dashboards include:
- Period filter: **All / Jokowi I / Jokowi II / Prabowo**
- Stance distribution (PRO / KONTRA / NETRAL)
- Sentiment distribution (POSITIVE / NEGATIVE / NEUTRAL)
- Top concepts, top actors, variable distribution
- Interactive force-directed SNA network (pyvis)

---

## Repository Structure

```
DNA/
├── pipelines/
│   ├── news/                          # News article pipeline
│   │   ├── 01_preprocess.py           # Clean raw scraped articles
│   │   ├── 02_extract_llm.py          # LLM: actor / stance / concept extraction
│   │   ├── 03_build_edgelist.py       # Build DNA bipartite + SNA edgelists
│   │   ├── 04_sentiment.py            # Sentiment scoring per statement
│   │   ├── 05_visualize_html.py       # Generate interactive HTML dashboard
│   │   ├── 06_export_gephi.py         # Export Gephi-ready CSVs
│   │   ├── 07_export_analysis_csvs.py
│   │   └── 08_build_report_docx.py    # Generate Word report
│   └── socmed/
│       ├── instagram/                 # Instagram pipeline
│       │   ├── 01_merge.py
│       │   ├── 02_clean.py
│       │   ├── 03_extract_llm.py
│       │   ├── 04_sentiment.py
│       │   ├── 05_sna_network.py
│       │   ├── 06_cohashtag.py
│       │   ├── 07_buzzer.py
│       │   └── 08_visualize.py
│       ├── youtube/                   # YouTube pipeline
│       │   ├── 01_merge.py
│       │   ├── 02_get_channels.py
│       │   ├── 03_fetch_metadata.py   # YouTube Data API v3
│       │   ├── 04_extract_llm.py
│       │   ├── 05_sentiment.py
│       │   ├── 06_build_edgelist.py
│       │   └── 07_visualize.py
│       └── facebook/                  # Facebook pipeline
│           ├── 01_scrape.py           # Playwright + cookie auth
│           ├── 02_clean.py
│           ├── 03_extract_llm.py
│           ├── 04_sentiment.py
│           └── 05_visualize.py
│
├── data/
│   ├── raw/                           # Raw inputs (gitignored)
│   │   ├── news/
│   │   ├── instagram/
│   │   ├── youtube/
│   │   ├── facebook/
│   │   └── variable_keywords.csv
│   └── processed/                     # Pipeline outputs (gitignored)
│       ├── news/
│       ├── instagram/
│       ├── youtube/
│       └── facebook/
│
├── config/                            # Shared actor/keyword mappings
├── assets/                            # JS libs (vis.js, tom-select)
├── docs/                              # GitHub Pages (HTML dashboards)
└── .env                               # API_KEY, YT_API_KEY, FB_COOKIES_FILE
```

---

## Pipelines

### News Articles

```
pipelines/news/01_preprocess.py          Clean raw articles
        ↓
pipelines/news/02_extract_llm.py         LLM: actor / stance / concept  [Gemini 2.5 Flash]
        ↓
pipelines/news/03_build_edgelist.py      Build DNA bipartite + SNA edgelists
        ↓
pipelines/news/04_sentiment.py           Sentiment per statement
        ↓
pipelines/news/05_visualize_html.py   →  data/processed/news/report_dna.html
```

### Instagram

```
pipelines/socmed/instagram/01_merge.py       Merge keyword-scraped CSVs
        ↓
pipelines/socmed/instagram/02_clean.py       Relevance filter + dedup
        ↓
pipelines/socmed/instagram/03_extract_llm.py LLM: stance + concepts  [resumable]
        ↓
pipelines/socmed/instagram/04_sentiment.py   Sentiment per post
        ↓
pipelines/socmed/instagram/08_visualize.py → data/processed/instagram/socmed_report.html
```

### YouTube

```
pipelines/socmed/youtube/01–03_*.py           Merge + fetch metadata via YouTube Data API v3
        ↓
pipelines/socmed/youtube/04_extract_llm.py   LLM: stance + concepts  [resumable]
        ↓
pipelines/socmed/youtube/05_sentiment.py     Sentiment per video
        ↓
pipelines/socmed/youtube/06_build_edgelist.py
        ↓
pipelines/socmed/youtube/07_visualize.py  →  data/processed/youtube/youtube_report.html
```

### Facebook

```
pipelines/socmed/facebook/01_scrape.py       Playwright + cookie auth → keyword search
        ↓
pipelines/socmed/facebook/02_clean.py        Relevance filter + dedup
        ↓
pipelines/socmed/facebook/03_extract_llm.py  LLM: stance + concepts  [resumable]
        ↓
pipelines/socmed/facebook/04_sentiment.py    Sentiment per post
        ↓
pipelines/socmed/facebook/05_visualize.py  → data/processed/facebook/facebook_report.html
```

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install pandas pyvis python-dotenv google-genai playwright
playwright install chromium

# Configure API keys
echo 'API_KEY=your_gemini_api_key' > .env
echo 'YT_API_KEY=your_youtube_data_api_key' >> .env

# Run news pipeline
python pipelines/news/01_preprocess.py
python pipelines/news/02_extract_llm.py    # resumable — safe to stop/restart
python pipelines/news/03_build_edgelist.py
python pipelines/news/04_sentiment.py
python pipelines/news/05_visualize_html.py
# → data/processed/news/report_dna.html
```

All LLM scripts are **resumable** — progress checkpointed to JSONL/CSV every 50 records.

---

## Political Era Definitions

| Period | Date Range |
|---|---|
| Jokowi I | 2014-10-20 → 2019-10-20 |
| Jokowi II | 2019-10-20 → 2024-10-20 |
| Prabowo | 2024-10-20 → present |

---

## Network Node Colors

| Color | Meaning |
|---|---|
| Green | PRO nuclear actor |
| Red | KONTRA nuclear actor |
| Grey | NETRAL actor |
| Orange box | Policy concept / keyword |

---

## Tech Stack

| Component | Tool |
|---|---|
| LLM extraction | Gemini 2.5 Flash (`google-genai`) |
| Network visualization | pyvis (vis.js) |
| Charts | Chart.js 4.4.0 |
| Facebook scraping | Playwright (headless Chromium + cookie auth) |
| Data processing | pandas |
| Deployment | GitHub Pages (`docs/` folder) |
