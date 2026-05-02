"""
STEP 1 - PREPROCESSING
=======================
Cleans noise from scraped news articles.
Input : input/9_ready_to_parse.csv
Output: output/cleaned.csv

Noise removed:
- Failed scraping footers (< 300 chars / office address content)
- "Baca juga:", "Editor:", reporter codes
- Inline URLs, ADVERTISEMENT tags
- Excessive whitespace and duplicate lines
"""

import pandas as pd
import re
from pathlib import Path

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "input" / "9_ready_to_parse.csv"
OUTPUT = ROOT / "output" / "cleaned.csv"

# ── Load ─────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT)
print(f"[INPUT]  {len(df)} rows")

# ── Drop rows with null variable/content ─────────────────────────────────────
df = df.dropna(subset=['variable', 'content'])
print(f"[after dropna] {len(df)} rows")

# ── Filter articles that are too short (likely failed scrapes) ────────────────
df = df[df['content'].str.len() >= 300]
print(f"[after length filter] {len(df)} rows")

# ── Content cleaning function ─────────────────────────────────────────────────
def clean_content(text: str) -> str:
    # Remove "Baca juga: ..." (Indonesian "Read also:")
    text = re.sub(r'[Bb]aca [Jj]uga\s*:?[^\n]*\n?', '', text)
    # Remove "Editor : ..." to end of line
    text = re.sub(r'Editor\s*:.*', '', text, flags=re.IGNORECASE)
    # Remove short reporter codes at end of article e.g. (wah), (riz)
    text = re.sub(r'\s*\([a-z]{2,4}\)\s*$', '', text.strip())
    # Remove inline URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove ADVERTISEMENT labels
    text = re.sub(r'\bADVERTISEMENT\b', '', text, flags=re.IGNORECASE)
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove duplicate lines within an article (scraping artifacts)
    lines = text.split('\n')
    seen = []
    seen_set = set()
    for line in lines:
        key = line.strip()
        if key not in seen_set:
            seen.append(line)
            seen_set.add(key)
    text = '\n'.join(seen)
    return text.strip()

df['content_clean'] = df['content'].apply(clean_content)

# ── Deduplicate by content ───────────────────────────────────────────────────
before_dedup = len(df)
df = df.drop_duplicates(subset=['content_clean'], keep='first')
after_dedup = len(df)
print(f"[DEDUPLICATED] {before_dedup} → {after_dedup} rows ({before_dedup - after_dedup} duplicates removed)")

# ── Add helper columns ────────────────────────────────────────────────────────
df['content_len_clean'] = df['content_clean'].str.len()
df['year'] = pd.to_datetime(df['date'], errors='coerce').dt.year

# ── Select and reorder columns ───────────────────────────────────────────────
df = df[['ID', 'year', 'keyword', 'variable', 'source', 'date', 'content_clean', 'content_len_clean']]

# ── Save ─────────────────────────────────────────────────────────────────────
df.to_csv(OUTPUT, index=False)
print(f"\n[OUTPUT] {len(df)} rows → {OUTPUT}")
print("\n[VARIABLE DISTRIBUTION]")
print(df['variable'].value_counts().to_string())
print("\n[CONTENT LENGTH STATS]")
print(df['content_len_clean'].describe())
