# Discourse Network Analysis (DNA) Pipeline
## Case Study: Indonesia Nuclear Energy Policy — RUU EBET

A 6-step pipeline that extracts actor-stance-concept networks from Indonesian news articles using LLM-based extraction, then generates an interactive HTML report.

---

## Pipeline Overview

```
input/9_ready_to_parse.csv
        │
        ▼
01_preprocess.py      → output/cleaned.csv
        │
        ▼
02_extract_llm.py     → output/extracted_raw.jsonl   (resumable)
        │
        ▼
03_build_edgelist.py  → output/01_flat_statements.csv
                        output/02_nodes_actors.csv
                        output/03_nodes_concepts.csv
                        output/04_edges_actor_concept.csv
                        output/05b_edges_actor_variable.csv
                        output/05c_edges_actor_keyword.csv
                        output/06a_summary_by_variable.csv
        │
        ▼
04_sentiment.py       → output/07_sentiment_scored.csv
        │
        ▼
05_visualize_html.py  → output/report_dna.html        (self-contained, shareable)
        │
        ▼
06_export_gephi.py    → output/gephi/                 (Gephi-ready CSVs)
```

---

## Folder Structure

```
Claude_1/
├── input/
│   └── 9_ready_to_parse.csv     ← raw scraped articles (not committed)
├── output/                       ← all generated files (not committed)
├── log/                          ← run logs (not committed)
├── venv/                         ← Python virtual environment
├── 01_preprocess.py
├── 02_extract_llm.py
├── 03_build_edgelist.py
├── 04_sentiment.py
├── 05_visualize_html.py
├── 06_export_gephi.py
├── .env                          ← API keys (not committed)
└── README_pipeline.md
```

---

## Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# Install dependencies
pip install pandas tqdm python-dotenv pyvis google-generativeai
```

Create a `.env` file with your API key:
```
API_KEY=your_gemini_api_key_here
```

Get a free Gemini API key at: https://aistudio.google.com

---

## Running the Pipeline

Run steps in order:

```bash
# Step 1: Clean scraped articles
python 01_preprocess.py

# Step 2: LLM extraction (actor / statement / position / concept)
# Resumable — safe to stop and restart, picks up from last processed article
python 02_extract_llm.py

# Step 3: Build node and edge lists for DNA/SNA
python 03_build_edgelist.py

# Step 4: Sentiment analysis per statement
python 04_sentiment.py

# Step 5: Generate interactive HTML report (single self-contained file)
python 05_visualize_html.py

# Step 6: (Optional) Export Gephi-ready CSV files
python 06_export_gephi.py
```

---

## Output: HTML Report

`output/report_dna.html` is a **single self-contained file** that includes:

| Section | Description |
|---|---|
| Summary stats | Total statements, unique actors, concepts, % PRO/KONTRA |
| DNA Network | Interactive bipartite graph: Institution → Keyword/Topic |
| Position by variable | Stacked bar: PRO / KONTRA / NETRAL per analysis dimension |
| Top 15 actors | Horizontal bar by statement count, colored by dominant position |
| Sentiment donut | Overall sentiment distribution |
| Sentiment × Position | Cross-tabulation chart |
| Article trend | Stacked bar: articles per month by position |
| Actor type breakdown | Donut: INDIVIDU / INSTITUSI / PAKAR / FRAKSI / MEDIA |
| Top 10 KONTRA actors | With institution affiliation in parentheses |
| Statements per variable | Horizontal bar per analysis dimension |

The network nodes are colored:
- 🟢 **Green** = PRO nuclear institution
- 🔴 **Red** = KONTRA nuclear institution
- ⚪ **Grey** = NETRAL institution
- 🟠 **Orange box** = Keyword/Topic node

**Sharing:** The HTML file is fully self-contained. Share the single file — no server or dependencies needed. Works in any modern browser.

---

## Network Configuration

Key settings in `05_visualize_html.py`:

```python
NETWORK_MODE   = "keyword"   # "keyword" (recommended) or "variable"
MIN_STATEMENTS = 3           # minimum statements to include an actor
```

Institution mapping uses `INST_KEYWORDS` (case-insensitive keyword → institution name) and `INST_SHORT` (full name → abbreviation). Actors that cannot be mapped to an institution are excluded from the graph.

---

## LLM Configuration

Edit `02_extract_llm.py`:

```python
LLM_PROVIDER = "gemini"
API_KEY       = os.getenv("API_KEY")   # from .env
MODELS = {
    "gemini": "gemini-2.5-flash",      # recommended
}
TEST_MODE = False   # set True to process only 5 articles for testing
SLEEP_SEC = 1.2     # delay between requests (adjust for rate limits)
```

### Processing Time Estimate (735 articles)

| Provider | Estimated Time | Notes |
|---|---|---|
| Gemini Flash | ~30–45 min | 1.2s/req, free tier |
| Groq (llama-3.1-70b) | ~25–35 min | 6K req/day free |
| Ollama (7B local) | ~2–4 hrs | depends on hardware |

---

## Gephi Import (Step 6)

After running `06_export_gephi.py`:

1. Open Gephi → **File > Import Spreadsheet**
2. Import `output/gephi/edges_actor_concept_gephi.csv` as **Edge Table**
3. Gephi auto-creates nodes from Source/Target
4. *(Optional)* Import `output/gephi/all_nodes_gephi.csv` as **Node Table** for attributes
5. **Layout:** ForceAtlas2 or Fruchterman-Reingold
6. **Appearance:** Color by `dominant_pos`, size by `n_statements`
