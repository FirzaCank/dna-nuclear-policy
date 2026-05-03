# DNA Nuclear Policy — Discourse Network Analysis

**Multi-platform Discourse Network Analysis (DNA) of Indonesian public discourse on nuclear energy policy (RUU EBET / PLTN)**

Extracts actor–stance–concept networks from news articles and social media (Instagram, YouTube, Facebook) using LLM-based parsing, then generates interactive dashboards filterable by political era.

---

## Live Dashboards

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
├── news/                          # News article pipeline
│   ├── 01_preprocess.py           # Clean raw scraped articles
│   ├── 02_extract_llm.py          # LLM: actor / stance / concept extraction
│   ├── 03_build_edgelist.py       # Build DNA bipartite + SNA edgelists
│   ├── 04_sentiment.py            # Sentiment scoring per statement
│   ├── 05_visualize_html.py       # Generate interactive HTML dashboard
│   ├── 06_export_gephi.py         # Export Gephi-ready CSVs
│   ├── 07_export_analysis_csvs.py
│   └── 08_build_report_docx.py    # Generate Word report
│
├── socmed/                        # Social media pipeline
│   ├── 01_merge.py                # Merge Instagram raw CSVs
│   ├── 01b_merge_youtube.py       # Merge YouTube raw CSVs
│   ├── 01c_get_youtube_channels.py
│   ├── 01d_fetch_youtube_metadata.py   # Fetch via YouTube Data API v3
│   ├── 01e_scrape_facebook.py     # Playwright + cookie auth keyword scraper
│   ├── 02_clean.py                # Clean Instagram data
│   ├── 02_clean_facebook.py       # Clean Facebook data
│   ├── 02_extract_llm_youtube.py  # LLM extraction for YouTube
│   ├── 03_extract_llm.py          # LLM stance extraction for Instagram
│   ├── 03_extract_llm_facebook.py
│   ├── 03_sentiment_youtube.py
│   ├── 04_build_edgelist_youtube.py
│   ├── 04_sentiment.py            # Sentiment scoring for Instagram
│   ├── 04_sentiment_facebook.py
│   ├── 05_sna_network.py          # Instagram mention network
│   ├── 05_visualize_socmed.py     # Instagram HTML dashboard
│   ├── 05_visualize_youtube.py    # YouTube HTML dashboard
│   ├── 05_visualize_facebook.py   # Facebook HTML dashboard
│   ├── 06_cohashtag.py            # Hashtag co-occurrence network
│   └── 07_buzzer.py               # Bot/buzzer detection scoring
│
├── input/                         # Raw data inputs
├── output/                        # Generated outputs (gitignored)
├── docs/                          # GitHub Pages (18 HTML files)
└── .env                           # API_KEY, YT_API_KEY, FB_COOKIES_FILE
```

---

## Pipelines

### News Articles

```
news/01_preprocess.py          Clean raw articles
        ↓
news/02_extract_llm.py         LLM: actor / stance / concept  [Gemini 2.5 Flash]
        ↓
news/03_build_edgelist.py      Build DNA bipartite + SNA edgelists
        ↓
news/04_sentiment.py           Sentiment per statement
        ↓
news/05_visualize_html.py   →  output/report_dna.html
```

### Instagram

```
socmed/01_merge.py             Merge keyword-scraped CSVs
        ↓
socmed/02_clean.py             Relevance filter + dedup
        ↓
socmed/03_extract_llm.py       LLM: stance + concepts  [resumable]
        ↓
socmed/04_sentiment.py         Sentiment per post
        ↓
socmed/05_visualize_socmed.py  → output/socmed_report.html
```

### YouTube

```
socmed/01b–01d_*.py            Merge + fetch metadata via YouTube Data API v3
        ↓
socmed/02_extract_llm_youtube.py   LLM: stance + concepts  [resumable]
        ↓
socmed/03_sentiment_youtube.py     Sentiment per video
        ↓
socmed/04_build_edgelist_youtube.py
        ↓
socmed/05_visualize_youtube.py  →  output/youtube_report.html
```

### Facebook

```
socmed/01e_scrape_facebook.py      Playwright + cookie auth → keyword search
        ↓
socmed/02_clean_facebook.py        Relevance filter + dedup
        ↓
socmed/03_extract_llm_facebook.py  LLM: stance + concepts  [resumable]
        ↓
socmed/04_sentiment_facebook.py    Sentiment per post
        ↓
socmed/05_visualize_facebook.py  → output/facebook_report.html
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
python news/01_preprocess.py
python news/02_extract_llm.py    # resumable — safe to stop/restart
python news/03_build_edgelist.py
python news/04_sentiment.py
python news/05_visualize_html.py
# → output/report_dna.html
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
