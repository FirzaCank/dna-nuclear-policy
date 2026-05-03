# Discourse Network Analysis: Indonesia's Nuclear Energy Policy
## Strategic Intelligence Report — Multi-Platform Analysis
**Prepared by:** Data Analytics Team
**Date:** May 4, 2026
**Status:** Phase 1 Complete (News Media) | Phase 2 Complete (Instagram, YouTube, Facebook)
**Live Dashboards:**
- [Berita Nasional](https://firzacank.github.io/dna-nuclear-policy/report_dna.html)
- [Instagram](https://firzacank.github.io/dna-nuclear-policy/socmed_report.html) — 1,769 posts
- [YouTube](https://firzacank.github.io/dna-nuclear-policy/youtube_report.html) — 559 videos
- [Facebook](https://firzacank.github.io/dna-nuclear-policy/facebook_report.html) — 931 posts

---

# TABLE OF CONTENTS

1. [Overview](#1-overview)
2. [Definitions](#2-definitions)
3. [Data Used](#3-data-used)
4. [Methodology](#4-methodology)
5. [Analysis](#5-analysis)
6. [Recommendations](#6-recommendations)
7. [Conclusion](#7-conclusion)
8. [Assumptions & Limitations](#8-assumptions--limitations)

---

# 1. OVERVIEW

## 1.1 Project Background

Indonesia stands at a critical crossroads in its energy policy trajectory. After decades of deliberation, the government's commitment to achieving Net Zero Emissions (NZE) by 2060 — combined with explosive electricity demand growth — has reignited serious debate around nuclear energy as a potential component of the national energy mix. The inclusion of nuclear power in the Revised Government Energy Regulation (PP 79/2014) and its explicit mention in the New and Renewable Energy Bill (*RUU EBET*) marks a historic shift in the political legitimacy of nuclear discourse in Indonesia.

This project applies **Discourse Network Analysis (DNA)** — a hybrid methodology merging Social Network Analysis (SNA) with Discourse/Content Analysis — to systematically map who is saying what about nuclear energy policy in Indonesia, how actors are positioned relative to each other, and what narratives dominate or are suppressed across the public policy debate.

## 1.2 Strategic Purpose

This report serves as a **stakeholder intelligence tool** to:

- Identify and profile key actors driving the nuclear policy narrative
- Map the distribution and intensity of PRO vs. KONTRA positions across different policy dimensions
- Detect emerging coalitions, fault lines, and discourse shifts over time
- Surface marginalized or peripheralized voices in the debate
- Provide a data-driven foundation for communication strategy, stakeholder engagement, and policy advocacy

## 1.3 Scope of This Report

This is a two-phase multi-platform analysis:

| Phase | Data Source | Volume | Status |
|-------|------------|--------|--------|
| Phase 1 | Online news media (national + specialized) | 719 articles | ✅ Complete |
| Phase 2a | Instagram | 1,769 posts | ✅ Complete |
| Phase 2b | YouTube | 559 videos | ✅ Complete |
| Phase 2c | Facebook | 931 posts | ✅ Complete |

Phase 1 covers **719 online news articles** spanning **December 2010 to April 2026**. Phase 2 covers social media posts collected via keyword search across 18 policy variables, analyzed with LLM-based stance extraction (PRO/KONTRA/NETRAL) and sentiment scoring.

---

# 2. DEFINITIONS

## 2.1 Core Concepts

### Discourse Network Analysis (DNA)
DNA is an analytical framework developed by Philip Leifeld (2013, 2017) that combines:
- **Social Network Analysis (SNA)**: mapping relationships between actors
- **Qualitative Content Analysis**: extracting and coding substantive positions

DNA produces bipartite graphs where **actors** are connected to **concepts/discourses** through **statements of position** (PRO/KONTRA/NETRAL). It reveals not only *who* speaks but *what* they argue and *how* they align with or oppose other actors.

### Actor
Any individual, institution, coalition, political faction, or organization that makes an explicit, attributable statement about nuclear energy policy in a news source. Anonymous quotes and general references (e.g., "the public said...") are excluded.

**Actor Types used in this analysis:**
| Type | Description | Example |
|------|-------------|---------|
| INDIVIDU | Named individual | Bahlil Lahadalia, Fabby Tumiwa |
| INSTITUSI | Organization/government body | BRIN, Greenpeace, Kementerian ESDM |
| PAKAR | Expert/academic without explicit org affiliation | Akademisi, Pengamat Energi |
| FRAKSI | Parliamentary caucus | Fraksi PKS DPR |
| MEDIA | Media organization as actor | Antara News |

### Statement
A sentence or short passage — either direct quotation or attributed paraphrase by the journalist — that clearly identifies: (1) a named actor, (2) a substantive concept about nuclear/energy policy, and (3) an inferrable position (PRO/KONTRA/NETRAL/AMBIGU). Minimum extraction confidence: **0.85**.

### Position
| Label | Definition |
|-------|-----------|
| PRO | Actor explicitly supports nuclear energy development, PLTN construction, or related policy |
| KONTRA | Actor explicitly opposes nuclear energy development, PLTN construction, or related policy |
| NETRAL | Actor makes a substantive observation/argument but without clear directional position |
| AMBIGU | Statement can be interpreted as either PRO or KONTRA depending on context |

### Concept / Discourse Variable
The thematic dimension of policy debate that a statement addresses. Nine analytical variables were defined *a priori* based on a preliminary reading of the nuclear policy discourse in Indonesia (see Section 3.3).

## 2.2 Key Terms

| Term | Definition |
|------|-----------|
| PLTN | Pembangkit Listrik Tenaga Nuklir — Nuclear Power Plant |
| SMR | Small Modular Reactor — compact, modular nuclear reactor technology |
| RUU EBET | Draft law on New and Renewable Energy (includes nuclear provision) |
| DIM | Daftar Inventarisasi Masalah — parliamentary clause-by-clause review document |
| NZE | Net Zero Emissions — Indonesia's 2060 climate target |
| BRIN | Badan Riset dan Inovasi Nasional — National Research & Innovation Agency |
| DNA | Discourse Network Analysis |
| Bipartite Network | Network with two distinct node types (actors and concepts) connected by edges |
| Institution Mapping | Grouping individual actors under their parent institution for network visualization |

---

# 3. DATA USED

## 3.1 Raw Data Collected

| Attribute | Value |
|-----------|-------|
| Total articles collected | 719 unique URLs |
| Total statements extracted | 2,084 |
| Unique actors identified | 762 |
| Analysis period | December 21, 2010 – April 17, 2026 |
| Primary language | Indonesian (Bahasa Indonesia) |

## 3.2 Media Sources

The corpus was built from **20+ online news sources** spanning government portals, national newspapers, specialized energy/business media, and environmental outlets. Top sources by statement volume:

| Source | Approx. Statements |
|--------|--------------------|
| kompas.id | 134 |
| brin.go.id | 117 |
| bloombergtechnoz.com | 77 |
| mongabay.co.id | 66 |
| antaranews.com | 57 |
| ruangenergi.com | 57 |
| katadata.co.id | 52 |
| listrikindonesia.com | 46 |
| cnbcindonesia.com | 42 |
| medcom.id | 40 |
| liputan6.com | 38 |
| detik.com (news + finance) | ~69 |
| fraksi.pks.id | 36 |
| dunia-energi.com | 36 |
| bisnis.com | ~58 |
| voaindonesia.com | 30 |
| esdm.go.id | 27 |
| industri.kontan.co.id | 30 |
| + others | remaining |

**Source diversity assessment:** The corpus includes government official portals (brin.go.id, esdm.go.id), mainstream national media (Kompas, CNBC, Detik, Bisnis), business/energy specialized outlets (Katadata, Ruang Energi, Dunia Energi, Bloomberg Technoz), and environmental/civil society aligned media (Mongabay), providing reasonable cross-spectrum coverage.

## 3.3 Analysis Variables (Thematic Dimensions)

Nine *a priori* discourse variables were defined to systematically capture different dimensions of the nuclear policy debate:

| Variable | Statements | % of Total | Description |
|----------|-----------|-----------|-------------|
| Keamanan Nasional & Kedaulatan | 497 | 23.8% | Nuclear as instrument of national security, energy sovereignty, and strategic independence |
| Ideologi & Integritas Data | 326 | 15.6% | Ideological framing, data credibility, expert authority claims |
| Intervensi & Pembiayaan | 304 | 14.6% | Foreign investment, financing models, geopolitical dependency risks |
| Transisi Energi & NZE | 294 | 14.1% | Nuclear's role in energy transition and Indonesia's NZE 2060 pathway |
| Periferalisasi & Hak Masyarakat | 268 | 12.9% | Community rights, displacement, marginalization of affected populations |
| Dinamika Pembahasan DIM | 232 | 11.1% | Legislative dynamics: parliamentary clause review, political maneuvering |
| Sinkronisasi Regulasi | 78 | 3.7% | Legal framework alignment, regulatory consistency |
| Interaksi Pemangku Kepentingan | 57 | 2.7% | Multi-stakeholder process, public consultation dynamics |
| Subordinasi Oposisi | 28 | 1.3% | Suppression or sidelining of opposing voices in the policy process |
| **TOTAL** | **2,084** | **100%** | |

## 3.4 Output Data Files

| File | Content | Rows |
|------|---------|------|
| `01_flat_statements.csv` | All extracted statements with full metadata | 2,084 |
| `02_nodes_actors.csv` | Actor node list with statement counts and positions | 762 |
| `03_nodes_concepts.csv` | Concept/keyword node list | Variable |
| `04_edges_actor_concept.csv` | Bipartite edges (actor → concept) | Variable |
| `05c_edges_actor_keyword.csv` | Actor-to-keyword edges (used in visualization) | Variable |
| `06a_summary_by_variable.csv` | Position distribution per actor per variable | Variable |
| `07_sentiment_scored.csv` | Sentiment scores per statement | 2,084 |
| `excluded_actors.csv` | Actors filtered out of network with reasons | Variable |
| `actor_detail.csv` | All actors with institution mapping and notes | 762 |

---

# 4. METHODOLOGY

## 4.1 Pipeline Overview

The analysis was implemented as a fully automated, reproducible 7-step Python pipeline:

```
[Raw Scraped Articles]
        │
        ▼ Step 1: Preprocessing
[Cleaned Articles CSV]
        │
        ▼ Step 2: LLM Extraction (Gemini 2.5 Flash)
[extracted_raw.jsonl — Actor + Statement + Position per Article]
        │
        ▼ Step 3: Edge List Construction
[01_flat_statements.csv, 02_nodes_actors.csv, 03_nodes_concepts.csv,
 04_edges_actor_concept.csv, 05b/05c_edges.csv, 06a_summary.csv]
        │
        ▼ Step 4: Sentiment Analysis (Gemini 2.5 Flash)
[07_sentiment_scored.csv]
        │
        ▼ Step 5: Visualization & Dashboard
[report_dna.html — self-contained interactive report]
        │
        ▼ Step 6/7: Export
[excluded_actors.csv, actor_detail.csv, Gephi files]
```

## 4.2 Step 1 — Preprocessing

**Input:** `input/9_ready_to_parse.csv` (scraped raw articles)
**Output:** `output/cleaned.csv`

Preprocessing removed:
- Articles with fewer than 300 characters (failed scrapes)
- Boilerplate content: "Baca juga:", "Editor:", reporter codes
- Inline URLs, "ADVERTISEMENT" tags
- Excessive whitespace and duplicate lines

## 4.3 Step 2 — LLM-Powered Statement Extraction

**Model:** Google Gemini 2.5 Flash (`gemini-2.5-flash`)
**Temperature:** 0.1 (near-deterministic)
**Thinking mode:** Disabled (speed optimization)
**Max statements per article:** 3 (highest confidence selected)
**Minimum confidence threshold:** 0.85

Each article was processed individually with a structured system prompt that instructed the model to act as an expert Indonesian nuclear policy discourse analyst. The model extracted structured JSON per article containing:

```json
{
  "actor": "Bahlil Lahadalia",
  "actor_type": "INDIVIDU",
  "actor_role": "Menteri ESDM",
  "statement": "quoted or paraphrased text",
  "concept": "kedaulatan energi nuklir",
  "position": "PRO",
  "confidence": 0.95
}
```

**Extraction rules enforced via prompt:**
- Statement must contain ALL THREE: named actor + substantive concept + inferrable position
- Pure factual events excluded ("Presiden mengunjungi lokasi PLTN" = invalid)
- PRO/KONTRA only if explicitly supported by the text — no inference from actions
- NETRAL for substantive but non-directional observations
- AMBIGU for genuinely ambiguous statements

## 4.4 Step 3 — Edge List Construction

**Input:** `extracted_raw.jsonl`
**Outputs:** 7 CSV files

Edge construction flattened the JSONL into a relational format, computing:
- **Actor nodes**: aggregated statement counts, dominant position, per-variable breakdowns
- **Concept nodes**: keyword and variable-level concept nodes
- **Bipartite edges**: actor → concept links weighted by statement frequency and position

## 4.5 Step 4 — Sentiment Analysis

**Model:** Google Gemini 2.5 Flash (same model as extraction)
**Task:** Per-statement emotional valence scoring, independent of policy position

Sentiment classification:
| Label | Definition |
|-------|-----------|
| POSITIVE | Optimistic, supportive, praising, achievement-oriented tone |
| NEGATIVE | Critical, pessimistic, rejecting, worried, alarming tone |
| NEUTRAL | Descriptive/factual with no emotional charge |

**Important distinction:** Sentiment ≠ Position. A PRO actor can use NEGATIVE sentiment (e.g., "we *must* build nuclear or face an energy *crisis*"). A KONTRA actor can use POSITIVE sentiment (e.g., "renewables offer a *promising* and safe alternative").

## 4.6 Step 5 — Network Visualization & Dashboard

The final output is a **single self-contained HTML file** (`report_dna.html`) containing:

1. **Bipartite Network Graph** (pyvis/vis.js): Institution → Keyword edges, color-coded by dominant position (green=PRO, red=KONTRA, grey=NETRAL)
2. **7 interactive Chart.js charts** embedded inline:
   - Position distribution per analytical variable (stacked bar)
   - Top 15 actors by statement count (horizontal bar)
   - Sentiment distribution (donut)
   - Sentiment × Position cross-tabulation (bar)
   - Article trend per month by position (stacked bar)
   - Actor type distribution (donut)
   - Top 10 KONTRA actors (horizontal bar)

**Network filtering criteria:** Actors included in the network visualization must satisfy BOTH:
1. ≥ 3 statements (eliminates noise from one-off mentions)
2. Mappable to a recognized institution (eliminates generic entities like "masyarakat")

This reduced 762 actors to **197 actors** for network analysis.

## 4.7 Institution Mapping

Individual actors were mapped to their parent institutions to enable institutional-level analysis. For example:
- "Bahlil Lahadalia" → "Kementerian ESDM"
- "Fabby Tumiwa" → "IESR"
- "Mulyanto" → "Fraksi PKS"
- "Hashim Djojohadikusumo" → "Prabowo Cabinet"

Institution mapping used a rule-based keyword matcher applied to `actor_role` fields, with a manually maintained mapping dictionary (`config/institution_mapping.py`).

---

# 5. ANALYSIS

## 5.1 Overall Position Distribution

| Position | Count | Percentage |
|---------|-------|-----------|
| PRO | 1,504 | **72%** |
| KONTRA | 385 | **18%** |
| NETRAL | 166 | **8%** |
| AMBIGU | 29 | **1%** |
| **TOTAL** | **2,084** | **100%** |

**Key Finding:** The **dominant narrative in Indonesian news media is strongly PRO-nuclear**, with 72% of all extracted statements expressing support for nuclear energy development. This creates a significant **media representation asymmetry** — opposition voices, while present and substantive, receive proportionally less coverage than government and pro-nuclear actors.

This asymmetry does not necessarily reflect public opinion (Phase 2 social media analysis is needed) but is indicative of the **agenda-setting power of government communications and pro-nuclear advocacy** in shaping media coverage.

---

## 5.2 Temporal Trend Analysis

### Articles by Year (Unique Source URLs)

| Year | Articles | Key Events |
|------|----------|-----------|
| 2010–2019 | ~41 total | Early discourse, sporadic |
| 2020 | 34 | COVID era energy planning, post-omnibus law |
| 2021 | 36 | NZE 2060 target announced |
| 2022 | 58 | Russia-Ukraine war → energy security urgency |
| 2023 | 86 | RUU EBET tabled, Prabowo campaign |
| 2024 | 97 | Election year, Prabowo victory, nuclear pledge |
| 2025 | **259** | **Peak year**: RUU EBET DIM deliberation, SMR deals |
| 2026 | 108 | Ongoing (Jan–Apr only) |

**Key Finding:** Nuclear policy discourse **exploded in 2025**, with 3x more articles than the previous year. This surge coincides with:
1. The DIM (clause-by-clause) review of RUU EBET in parliament
2. Prabowo administration's explicit nuclear energy commitments
3. Multiple high-profile international nuclear cooperation agreements (US, Russia, South Korea, France)
4. BRIN's intensified communication about Small Modular Reactors (SMR)

The trajectory strongly suggests nuclear policy discourse will remain a **high-attention issue** through at least 2027 given the legislative timeline.

---

## 5.3 Actor Analysis

### 5.3.1 Most Active Actors (by statement volume)

| Rank | Actor | Institution | Statements | Position |
|------|-------|------------|-----------|---------|
| 1 | Bahlil Lahadalia | Kementerian ESDM | 59 | PRO |
| 2 | Pemerintah | Government (generic) | 48 | PRO |
| 3 | Dadan Kusdiana | Kementerian ESDM | 41 | PRO |
| 4 | Hashim Djojohadikusumo | Prabowo Cabinet | 41 | PRO |
| 5 | Syaiful Bakhri | Akademisi/FMIPA | 36 | PRO |
| 6 | Yuliot Tanjung | Kementerian ESDM | 32 | PRO |
| 7 | Arifin Tasrif | Kementerian ESDM | 30 | PRO |
| 8 | Pemerintah Indonesia | Government (formal) | 30 | PRO |
| 9 | Mulyanto | Fraksi PKS | 27 | KONTRA |
| 10 | Fabby Tumiwa | IESR | 26 | KONTRA |
| 11 | Eddy Soeparno | DPR/PAN | 23 | PRO |
| 12 | Bambang Patijaya | DPR | 21 | PRO |
| 13 | Yuliot | Kementerian ESDM | 19 | PRO |
| 14 | Airlangga Hartarto | Kemko Ekonomi | 18 | PRO |
| 15 | BRIN | BRIN | 18 | PRO |

**Key Finding:** **13 of the top 15 most vocal actors are PRO-nuclear**, dominated overwhelmingly by Kementerian ESDM officials (ranks 1, 3, 6, 7, 13). This reflects a pattern where government officials — with built-in media access via press conferences, official statements, and ministry portals — systematically outpace civil society voices in media coverage volume.

The two KONTRA actors in the top 15 — **Mulyanto** (PKS parliamentary faction) and **Fabby Tumiwa** (IESR) — represent institutionally distinct opposition voices: legislative (democratic opposition) and techno-expert (energy transition analysis), respectively.

### 5.3.2 Actor Coverage Distribution

| Threshold | Actors | % of Total |
|-----------|--------|-----------|
| ≥ 1 statement | 762 | 100% |
| ≥ 3 statements (network-eligible) | 197 | 26% |
| Excluded (< 3 OR no institution map) | 565 | 74% |

The **long tail of 565 excluded actors** is analytically significant: it represents a wide range of voices (local community members, smaller NGOs, international observers, one-time commentators) that collectively contribute to the discourse but are individually insufficient for network centrality analysis. These will be revisited in a qualitative supplementary analysis.

### 5.3.3 Actor Type Distribution

| Type | Statements | % |
|------|-----------|--|
| INDIVIDU | 1,610 | 77.3% |
| INSTITUSI | 395 | 19.0% |
| PAKAR | 64 | 3.1% |
| FRAKSI | 7 | 0.3% |
| MEDIA | 7 | 0.3% |

**Key Finding:** Individual actors dominate the discourse (77%), which is expected — journalists quote people, not organizations. However, institutional statements (19%) are notable as they represent official organizational positions (BRIN research positions, Greenpeace Indonesia statements, etc.) with higher credibility weight.

---

## 5.4 Position Analysis by Variable

| Variable | PRO | KONTRA | NETRAL | AMBIGU | PRO Dominance |
|----------|-----|--------|--------|--------|---------------|
| Keamanan Nasional & Kedaulatan | ~420 | ~40 | ~37 | — | **Very High** |
| Ideologi & Integritas Data | ~270 | ~30 | ~26 | — | **Very High** |
| Intervensi & Pembiayaan | ~155 | ~125 | ~24 | — | **Moderate** |
| Transisi Energi & NZE | ~235 | ~25 | ~34 | — | **High** |
| Periferalisasi & Hak Masyarakat | ~65 | ~170 | ~33 | — | **KONTRA dominant** |
| Dinamika Pembahasan DIM | ~110 | ~70 | ~52 | — | **Moderate** |
| Sinkronisasi Regulasi | ~55 | ~15 | ~8 | — | **High** |
| Interaksi Pemangku Kepentingan | ~45 | ~8 | ~4 | — | **High** |
| Subordinasi Oposisi | ~12 | ~12 | ~4 | — | **Contested** |

*Note: Exact per-variable PRO/KONTRA/NETRAL breakdowns by actor are in `06a_summary_by_variable.csv`*

**Key Findings:**

**1. National Security is the dominant framing (23.8% of all statements):** The most heavily deployed narrative positions nuclear energy as essential to Indonesia's strategic autonomy, energy sovereignty, and national security. This framing effectively co-opts nationalist sentiment in support of nuclear adoption.

**2. Community Rights is the only variable where KONTRA dominates:** "Periferalisasi & Hak Masyarakat" has the clearest KONTRA majority, indicating that opposition to nuclear is most effectively articulated through a rights-based, social justice lens rather than purely technical or environmental arguments. Civil society organizations (Greenpeace, WALHI, Koalisi Masyarakat Sipil) concentrate their opposition here.

**3. Intervention & Financing is the most contested financial variable:** With nearly balanced PRO/KONTRA distribution, debates about foreign financing (Russia's Rosatom, US companies, South Korea) and financial risk are genuinely contested even among PRO actors who disagree on acceptable financing terms.

**4. Parliamentary Dynamics (DIM) is a real battleground:** With 232 statements and mixed distribution, the DIM review process represents the current legislative front line where positions harden and deal-making occurs.

---

## 5.5 Top Discourse Keywords (Network Centrality)

The most frequently invoked keyword clusters (by combined edge weight in the actor-keyword network):

| Rank | Keyword Cluster | Weight | Variable Alignment |
|------|----------------|--------|-------------------|
| 1 | limbah radioaktif nuklir Indonesia | 177 | Periferalisasi / Keamanan |
| 2 | PLTN ketahanan energi nasional | 162 | Keamanan Nasional |
| 3 | kedaulatan energi nuklir | 157 | Keamanan Nasional |
| 4 | SMR Indonesia reaktor | 135 | Transisi Energi |
| 5 | tarif listrik PLN nuklir | 132 | Intervensi & Pembiayaan |
| 6 | RUU EBET DIM | 113 | Dinamika Pembahasan DIM |
| 7 | BRIN nuklir SDM | 110 | Ideologi & Integritas Data |
| 8 | nuklir IAEA keselamatan Indonesia | 108 | Keamanan Nasional |
| 9 | fraksi DPR nuklir | 98 | Dinamika Pembahasan DIM |
| 10 | nuklir NZE 2060 Indonesia | 95 | Transisi Energi |
| 11 | nuklir energi hijau target iklim | 83 | Transisi Energi |
| 12 | PLTU pensiun dini nuklir | 80 | Transisi Energi |
| 13 | penolakan PLTN masyarakat lokal | 79 | Periferalisasi |
| 14 | PLTU batubara nuklir transisi | 64 | Transisi Energi |
| 15 | UU Cipta Kerja nuklir regulasi | 48 | Sinkronisasi Regulasi |

**Key Finding:** The **"limbah radioaktif" (nuclear waste)** keyword cluster has the highest overall weight, indicating it is the most universally referenced concept — used by both PRO actors (to argue Indonesia has the technical capability to manage it) and KONTRA actors (to argue it represents unacceptable risk). Nuclear waste management is the single most contested empirical battleground in the discourse.

The **SMR keyword cluster** (rank 4) is notable for its relatively high weight given SMRs are a newer technology, suggesting BRIN and government sources have been highly effective at inserting this narrative into mainstream media coverage as a "safe, modern alternative" framing.

---

## 5.6 Sentiment Analysis

### Overall Sentiment Distribution

| Sentiment | Count | Percentage |
|-----------|-------|-----------|
| POSITIVE | 1,039 | **49.9%** |
| NEUTRAL | 627 | **30.1%** |
| NEGATIVE | 418 | **20.1%** |

### Sentiment × Position Cross-Tabulation

| Position | POSITIVE | NEUTRAL | NEGATIVE |
|---------|---------|---------|---------|
| PRO (n=1,504) | 1,007 (67%) | 445 (30%) | 52 (3%) |
| KONTRA (n=385) | 14 (4%) | 37 (10%) | 334 (87%) |
| NETRAL (n=166) | 18 (11%) | 124 (75%) | 24 (14%) |
| AMBIGU (n=29) | 0 (0%) | 21 (72%) | 8 (28%) |

**Key Findings:**

**1. PRO actors speak with optimism (67% POSITIVE):** Government and pro-nuclear advocates overwhelmingly use positive, achievement-oriented language — framing nuclear as opportunity, progress, and national pride. This is a deliberate rhetorical strategy that makes opposition harder by contrast.

**2. KONTRA actors speak with urgency and alarm (87% NEGATIVE):** Opposition voices use overwhelmingly negative emotional framing — risk, danger, rejection, warning. While this is authentic to genuine concern, it creates a **perception contrast** where PRO actors sound constructive and visionary while KONTRA actors sound purely restrictive.

**3. NETRAL statements are accurately calibrated (75% NEUTRAL sentiment):** Academic and analytical statements, which make up most NETRAL-position content, correctly score as emotionally neutral — confirming sentiment model validity.

**4. AMBIGU statements carry negative undertones (28% NEGATIVE, 72% NEUTRAL, 0% POSITIVE):** The complete absence of positive sentiment in AMBIGU statements suggests these are not genuinely balanced — they lean toward concern framed in diplomatic or hedged language.

---

## 5.7 Key Actor Coalitions

### PRO Coalition — Core Members

**Government / Executive:**
- Kementerian ESDM (Bahlil Lahadalia, Dadan Kusdiana, Arifin Tasrif, Yuliot Tanjung)
- Kemko Perekonomian (Airlangga Hartarto)
- Kantor Presiden / Prabowo inner circle (Hashim Djojohadikusumo)

**Legislative:**
- Multiple DPR factions (PKB, Golkar, PAN, Gerindra)

**Research / Technical:**
- BRIN (institutional voice)
- Individual academics from UI, ITB, UGM supporting nuclear feasibility

**International Partners:**
- Rosatom (Russia), NuScale (US), KHNP (South Korea) — implicit PRO through cooperation agreements

### KONTRA Coalition — Core Members

**Civil Society / Environmental:**
- Greenpeace Indonesia
- WALHI (Wahana Lingkungan Hidup Indonesia)
- JATAM (Jaringan Advokasi Tambang)
- ICEL (Indonesian Center for Environmental Law)
- CELIOS (Center of Economic and Law Studies)
- Koalisi Masyarakat Sipil untuk Transisi Energi

**Legislative Opposition:**
- Fraksi PKS (Mulyanto as primary spokesperson — 27 statements, dominant KONTRA)

**Technical / Energy Transition:**
- IESR (Fabby Tumiwa — 26 statements, 18 KONTRA) — provides economic and technical arguments against nuclear viability in Indonesia's specific context
- Arcandra Tahar — former Deputy Minister ESDM, now KONTRA on financing model concerns

**Academic:**
- Yudi Utomo Imardjoko — nuclear physicist with safety concerns
- Ahmad Subhan Hafiz — community rights advocate

---

# 6. RECOMMENDATIONS

## 6.1 For Policy Communication (Pro-Nuclear Stakeholders)

### R1: Directly Address Nuclear Waste — The #1 Contested Keyword
The "limbah radioaktif" cluster has the highest network centrality and is the most common entry point for KONTRA arguments. **Current PRO messaging is insufficient here.** Recommendation: commission and publish a technically credible, independently reviewed white paper specifically on Indonesia's nuclear waste management plan, hosted at a neutral domain (e.g., BRIN or a university).

### R2: Engage the Community Rights Narrative — The Only KONTRA-dominant Variable
"Periferalisasi & Hak Masyarakat" is where KONTRA voices win. No amount of energy security messaging neutralizes genuine community displacement concerns. Recommendation: proactively develop a **Social Impact & Benefit-Sharing Framework** for any proposed PLTN site, announced *before* site selection finalizes, to preempt this narrative.

### R3: Counter the Rhetorical Asymmetry on Financing
The Intervensi & Pembiayaan variable is genuinely contested — even PRO actors disagree on financing terms. Recommendation: develop transparent public criteria for acceptable foreign financing models to prevent KONTRA actors from exploiting ambiguity.

### R4: Leverage SMR Narrative — It Is Working
The SMR keyword cluster (rank 4, weight 135) has achieved significant penetration despite being newer. BRIN's communications strategy on SMR is effective. Recommendation: **sustain and intensify** SMR-specific communication, particularly linking SMR to local industrial zones (Kawasan Industri) and energy-hungry sectors (data centers, aluminum smelters) where cost arguments are most compelling.

## 6.2 For Opposition & Civil Society (KONTRA Stakeholders)

### R5: Reframe from "Danger" to "Alternatives" — Fix the Sentiment Asymmetry
87% NEGATIVE sentiment among KONTRA actors creates a perception problem: opposition sounds obstructionist. Recommendation: shift communication toward **POSITIVE framing of alternatives** (e.g., "Indonesia can achieve NZE with geothermal + storage — here is the evidence") rather than primarily warning-based messaging.

### R6: Build Economic Arguments — Not Just Safety/Rights
The two most effective KONTRA voices (Fabby Tumiwa/IESR and Arcandra Tahar) use economic and financing arguments. Pure safety or environmental arguments have lower traction in the current political climate. Recommendation: invest in producing **cost-comparison studies** showing nuclear LCOE vs. renewables in Indonesia's specific grid context.

### R7: Activate Parliamentary Allies in DIM Review
The DIM review variable (232 statements) is an active legislative front. Fraksi PKS (Mulyanto) is currently the primary legislative opposition voice. Recommendation: coordinate a multi-faction civil society briefing to expand the number of legislators making substantive KONTRA arguments during DIM proceedings.

## 6.3 For Research / Analytics (This Project)

### R8: Prioritize Social Media Phase — The Missing Voice
The news media corpus is dominated by government-affiliated actors with high media access. Social media data will likely reveal a very different distribution: more individual citizen voices, more KONTRA sentiment, and different keyword clusters. Phase 2 is essential for a complete picture.

### R9: Conduct Qualitative Deep-Dive on 565 Excluded Actors
The 74% of actors below the 3-statement threshold represent the "long tail" of discourse — local community members, regional officials, small NGOs. A qualitative analysis of this cohort may reveal important peripheral voices systematically underrepresented in the network.

### R10: Track Discourse Shifts Pre/Post Key Legislative Events
The DIM review is ongoing. Recommendation: re-run the pipeline after each major parliamentary session (or at minimum, quarterly) to detect real-time narrative shifts and coalition realignment.

---

# 7. CONCLUSION

## 7.1 Summary of Core Findings

Indonesia's nuclear energy policy discourse — as represented in online news media from 2010 to April 2026 — is characterized by **three structural features**:

**1. Pro-nuclear hegemony in media representation:** 72% of all statements are PRO-nuclear, driven primarily by government officials with built-in media access. This does not necessarily represent broader public opinion but creates an important **information environment** that shapes elite and mass perceptions.

**2. A highly contested but losing opposition:** KONTRA voices are substantive, technically credible, and institutionally diverse (civil society, environmental NGOs, selective academic experts, PKS parliamentary faction), but they represent only 18% of media statements. Their most effective arguments concentrate in two areas: community rights/displacement and economic viability of financing models.

**3. A discourse at an inflection point:** The 2025 spike (259 articles vs. 97 in 2024) and the ongoing DIM legislative process mark the most consequential moment in Indonesia's nuclear policy debate since the 1997 PLTN Muria controversy. The next 12–24 months will be decisive: if RUU EBET passes with nuclear provisions intact and site selection begins, the policy window for meaningful opposition narrows dramatically.

## 7.2 Strategic Implications

For **any stakeholder** engaging in this policy space:

- **Narrative battles are won on specific frames, not general positions.** Nuclear waste management, community rights, and financing model legitimacy are the three specific terrains where this debate will be decided.
- **Sentiment strategy matters.** The optimistic tone of PRO actors and the alarming tone of KONTRA actors are not neutral — they actively shape how each side is perceived by undecided stakeholders (regional governments, international investors, the middle-class public).
- **Phase 2 social media data is essential** before drawing conclusions about public opinion. News media systematically overrepresents institutionally powerful actors. Social media will test whether the 72% PRO media dominance reflects or contradicts grassroots sentiment.

## 7.3 Next Steps

| Priority | Action | Timeline |
|----------|--------|----------|
| High | Complete social media data collection (Twitter/X, YouTube) | Q2 2026 |
| High | Re-run pipeline after next major DIM session | Within 30 days of session |
| Medium | Qualitative review of excluded actors for stakeholder blind spots | Q2 2026 |
| Medium | Share `excluded_actors.csv` and `actor_detail.csv` with subject matter experts for validation | Immediate |
| Low | Gephi-based advanced network centrality analysis | Q3 2026 |

---

# 8. ASSUMPTIONS & LIMITATIONS

## 8.1 Data Collection Assumptions

| Assumption | Implication |
|-----------|-------------|
| The 719 articles collected are representative of the broader nuclear policy news coverage | If major sources were missed or blocked during scraping, the corpus may systematically underrepresent certain perspectives |
| Article date reflects publication date of original content | Some republished or undated articles may have incorrect temporal attribution |
| All 20+ sources were available and scrapable without paywalls | Kompas.id (partial paywall) and some business sources may have yielded fewer articles than their actual nuclear coverage volume |

## 8.2 LLM Extraction Assumptions

| Assumption | Implication |
|-----------|-------------|
| Gemini 2.5 Flash correctly identifies actor-concept-position triples with ≥0.85 confidence | LLM extraction is not 100% accurate; estimated error rate ~5-15% based on spot-checks |
| Maximum 3 statements per article is sufficient | Some long analytical articles may contain more than 3 substantive statements; the highest-confidence ones are selected but others are lost |
| Actor names are extracted consistently | Name variants (e.g., "Agus Puji Prasetiyono" vs "Agus Puji Prasetyono") create duplicate actors; partially resolved via institution mapping but some duplication remains |
| PRO/KONTRA labels accurately reflect the actor's actual policy position | Journalists sometimes misquote or oversimplify. The model operates on the text as given, not the actor's actual views |

## 8.3 Methodology Limitations

**1. Media coverage bias, not public opinion:**
This analysis measures what actors say in the news, not what the public believes. The dominance of government voices reflects access to media, not necessarily prevalence of that view in society.

**2. Statement-level, not actor-level consistency:**
An actor who makes 10 PRO statements and 2 KONTRA statements is counted as PRO (dominant position logic). Nuanced, evolving, or context-specific positions are simplified.

**3. Network filtering removes 74% of actors:**
The MIN_STATEMENTS=3 threshold is necessary to maintain network readability but excludes the "long tail" of discourse participants. This may systematically exclude local/community voices who may each speak once.

**4. Institution mapping is rule-based, not infallible:**
Actors without identifiable institution (mapped as None) are excluded from the network visualization. Some valid actors with unclear roles are dropped. The current mapping dictionary covers the most active actors but may miss newer or more obscure institutional affiliations.

**5. Keyword clustering is manually curated:**
The `KEYWORD_MERGE` dictionary (merging near-duplicate keyword strings) is manually maintained. New keyword clusters that emerge post-pipeline-run are not automatically captured.

**6. Sentiment model validated for Indonesian:**
Gemini 2.5 Flash has strong Indonesian language capability but was not specifically fine-tuned for Indonesian political discourse sentiment. Politically coded language (sarcasm, Indonesian rhetorical conventions) may score differently than intended.

**7. Social media is absent (Phase 1 only):**
The absence of social media data means this analysis captures elite/institutional discourse only. Mass public discourse — which may be substantially more oppositional — is not represented.

## 8.4 Temporal Limitations

- Data collected through April 17, 2026. Events after this date are not captured.
- The 2010–2019 period is substantially underrepresented (41 articles vs. 719 total), reflecting both the lower intensity of nuclear discourse in that period AND potentially lower scraping coverage of older articles.
- Year 2026 data (108 articles) covers only January–April and should not be annualized.

---

*End of Report*

---
**Document metadata:**
- Analysis engine: Google Gemini 2.5 Flash
- Pipeline language: Python 3.13
- Live dashboard: https://FirzaCank.github.io/dna-nuclear-policy
- Report generated: April 23, 2026
- Phase: 1 of 2 (News Media only)
- Data coverage: December 2010 – April 17, 2026
