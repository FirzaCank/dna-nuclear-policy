# DNA Pipeline — Technical Reference

Multi-platform Discourse Network Analysis pipeline for Indonesia's nuclear energy policy discourse.

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env   # fill in API keys
```

`.env` required keys:
```
API_KEY=your_gemini_api_key        # https://aistudio.google.com
YT_API_KEY=your_youtube_data_api   # https://console.cloud.google.com
SCRAPE_BADGER=your_scrapebadger_key  # https://scrapebadger.com/dashboard/api-keys
```

---

## Pipelines

### News Articles (`pipelines/news/`)

```
data/raw/news/9_ready_to_parse.csv
        │
        ▼
01_preprocess.py       → data/processed/news/cleaned.csv
        │
        ▼
02_extract_llm.py      → data/processed/news/extracted_raw.jsonl      [resumable]
        │
        ▼
03_build_edgelist.py   → data/processed/news/01_flat_statements.csv
                          data/processed/news/02_nodes_actors.csv
                          data/processed/news/03_nodes_concepts.csv
                          data/processed/news/04_edges_actor_concept.csv
                          data/processed/news/05b_edges_actor_variable.csv
                          data/processed/news/06a_summary_by_variable.csv
        │
        ▼
04_sentiment.py        → data/processed/news/07_sentiment_scored.csv
        │
        ▼
05_visualize_html.py   → data/processed/news/report_dna.html
        │
        ▼
06_export_gephi.py     → data/processed/news/gephi/                   [optional]
07_export_analysis_csvs.py
08_build_report_docx.py
```

Run:
```bash
python pipelines/news/01_preprocess.py
python pipelines/news/02_extract_llm.py      # resumable
python pipelines/news/03_build_edgelist.py
python pipelines/news/04_sentiment.py
python pipelines/news/05_visualize_html.py
```

---

### Instagram (`pipelines/socmed/instagram/`)

```
data/raw/instagram/*.csv
        │
        ▼
01_merge.py            → data/processed/instagram/socmed_merged.csv
        │
        ▼
02_clean.py            → data/processed/instagram/socmed_cleaned.csv
        │
        ▼
03_extract_llm.py      → data/processed/instagram/socmed_extracted_raw.jsonl   [resumable]
        │
        ▼
04_sentiment.py        → data/processed/instagram/socmed_sentiment.csv
        │
        ▼
05_sna_network.py      → data/processed/instagram/socmed_edges_mention.csv
06_cohashtag.py        → data/processed/instagram/socmed_edges_hashtag.csv
07_buzzer.py           → data/processed/instagram/socmed_buzzer_scores.csv
        │
        ▼
08_visualize.py        → data/processed/instagram/socmed_report.html
```

---

### YouTube (`pipelines/socmed/youtube/`)

```
data/raw/youtube/*.csv
        │
        ▼
01_merge.py            → data/processed/youtube/youtube_merged.csv
02_get_channels.py     → data/processed/youtube/youtube_channel_urls.csv
03_fetch_metadata.py   → data/processed/youtube/youtube_metadata.csv       [YouTube Data API v3]
        │
        ▼
04_extract_llm.py      → data/processed/youtube/youtube_extracted_raw.jsonl  [resumable]
        │
        ▼
05_sentiment.py        → data/processed/youtube/youtube_sentiment.csv
        │
        ▼
06_build_edgelist.py   → data/processed/youtube/yt_*.csv
        │
        ▼
07_visualize.py        → data/processed/youtube/youtube_report.html
```

---

### Facebook (`pipelines/socmed/facebook/`)

Requires: `data/raw/facebook/www.facebook.com_cookies.txt` (Netscape format, exported from browser)

```
data/raw/variable_keywords.csv      [18 keywords]
        │
        ▼
01_scrape.py           → data/processed/facebook/facebook_raw.csv          [Playwright + cookies]
        │
        ▼
02_clean.py            → data/processed/facebook/facebook_cleaned.csv
        │
        ▼
03_extract_llm.py      → data/processed/facebook/facebook_extracted_raw.jsonl  [resumable]
        │
        ▼
04_sentiment.py        → data/processed/facebook/facebook_sentiment.csv
        │
        ▼
05_visualize.py        → data/processed/facebook/facebook_report.html
```

### Twitter/X (`pipelines/socmed/twitter/`)

Requires: `SCRAPE_BADGER` key in `.env` (ScrapeBadger API)

```
data/raw/variable_keywords.csv      [18 keywords]
        │
        ▼
01_scrape.py           → data/processed/twitter/twitter_raw.csv          [ScrapeBadger API, resumable]
        │
        ▼
02_clean.py            → data/processed/twitter/twitter_cleaned.csv
        │
        ▼
03_extract_llm.py      → data/processed/twitter/twitter_extracted_raw.jsonl  [resumable]
        │
        ▼
04_sentiment.py        → data/processed/twitter/twitter_sentiment.csv
        │
        ▼
05_visualize.py        → data/processed/twitter/twitter_report.html + twitter_network_tw_{period}.html
```

Run:
```bash
source venv/bin/activate
python pipelines/socmed/twitter/01_scrape.py
python pipelines/socmed/twitter/02_clean.py
python pipelines/socmed/twitter/03_extract_llm.py   # resumable
python pipelines/socmed/twitter/04_sentiment.py     # resumable
python pipelines/socmed/twitter/05_visualize.py
```

---

## Publishing to GitHub Pages

After running any visualize script, copy outputs to `docs/`:

```bash
cp data/processed/news/report_dna.html data/processed/news/network_dna_*.html docs/
cp data/processed/instagram/socmed_report.html data/processed/instagram/socmed_network_*.html docs/
cp data/processed/youtube/youtube_report.html data/processed/youtube/youtube_network_*.html docs/
cp data/processed/facebook/facebook_report.html data/processed/facebook/facebook_network_*.html docs/
cp data/processed/twitter/twitter_report.html data/processed/twitter/twitter_network_tw_*.html docs/
git add docs/ && git commit -m "update dashboards" && git push
```

Live dashboards: **https://firzacank.github.io/dna-nuclear-policy**

---

## LLM Configuration

All LLM scripts use Gemini 2.5 Flash with `thinking_budget=0` for speed.

```python
MODEL       = "gemini-2.5-flash"
SLEEP_SEC   = 1.2     # between requests
MAX_RETRIES = 3
TEST_MODE   = False   # set True to process 5 rows only
```

All LLM scripts are **resumable** — checkpointed to JSONL/CSV every 50 records. Safe to stop and restart.

---

## Political Era Definitions

| Period | Date Range |
|---|---|
| Jokowi I | 2014-10-20 → 2019-10-20 |
| Jokowi II | 2019-10-20 → 2024-10-20 |
| Prabowo | 2024-10-20 → present |

---

## Gephi Export (News)

After `pipelines/news/06_export_gephi.py`:

1. Gephi → **File > Import Spreadsheet**
2. Import `edges_actor_concept_gephi.csv` as **Edge Table**
3. *(Optional)* import `all_nodes_gephi.csv` as **Node Table**
4. Layout: ForceAtlas2 or Fruchterman-Reingold
5. Appearance: color by `dominant_pos`, size by `n_statements`
