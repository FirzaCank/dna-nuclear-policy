"""
Clean socmed_merged.csv:
  1. Drop posts with empty/null caption
  2. Filter relevance: caption must contain >=1 nuclear/energy-policy term
  3. Clean caption text: normalize whitespace, strip URLs, strip trailing hashtag blocks
Output: output/socmed_cleaned.csv
       output/socmed_removed.csv  (rejected rows, for audit)
"""

import os
import re
import pandas as pd
from pathlib import Path

ROOT    = Path(__file__).parent.parent
INPUT   = ROOT / "output" / "socmed_merged.csv"
OUTPUT  = ROOT / "output" / "socmed_cleaned.csv"
REMOVED = ROOT / "output" / "socmed_removed.csv"

# Must match >=1 term (case-insensitive, word-boundary aware)
# Covers nuclear + energy policy in Indonesian + English
RELEVANCE_TERMS = [
    # Nuclear core
    r"nuklir", r"nuclear", r"pltn", r"reaktor", r"reactor",
    r"radioaktif", r"radioactive", r"uranium", r"thorium",
    r"fisi", r"fusi", r"fission", r"fusion",
    r"chernobyl", r"fukushima", r"three mile",
    r"smr", r"small modular reactor",
    r"bapeten", r"iaea",
    # Energy policy (nuclear context)
    r"ruu ebet", r"uu ebet", r"ebet",
    r"energi baru", r"new energy", r"energi terbarukan",
    r"transisi energi", r"energy transition",
    r"dekarbonisasi", r"decarbonisation", r"decarbonization",
    r"net zero", r"nze", r"karbon netral", r"carbon neutral",
    r"just transition", r"transisi berkeadilan",
    r"emisi karbon", r"carbon emission", r"emisi co2",
    r"pltu", r"pensiun batu bara", r"coal retirement", r"coal phase",
    r"lcoe", r"levelized cost",
    r"brin", r"esdm",
    r"energi hijau", r"green energy", r"clean energy", r"energi bersih",
    r"pembangkit listrik",
    r"limbah radioaktif", r"nuclear waste", r"limbah nuklir",
    r"keamanan nuklir", r"nuclear safety", r"nuclear security",
]

RELEVANCE_PATTERN = re.compile(
    "|".join(RELEVANCE_TERMS),
    re.IGNORECASE
)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")

def clean_caption(text):
    if not isinstance(text, str):
        return ""
    # strip Unicode line/paragraph separators (U+2028, U+2029) from Instagram
    text = text.replace(" ", "\n").replace(" ", "\n")
    # strip URLs
    text = URL_PATTERN.sub("", text)
    # normalize whitespace: collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # strip trailing hashtag-only lines (lines where >80% tokens are hashtags)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        tokens = line.split()
        if not tokens:
            cleaned_lines.append(line)
            continue
        hashtag_ratio = sum(1 for t in tokens if t.startswith("#")) / len(tokens)
        # keep if not a pure hashtag dump (allow mixed lines)
        if hashtag_ratio < 0.85:
            cleaned_lines.append(line)
    text = "\n".join(cleaned_lines).strip()
    return text


df = pd.read_csv(INPUT, low_memory=False)
total_input = len(df)
removed_rows = []

# Step 1: drop null/empty caption
mask_null = df["caption"].isna() | (df["caption"].fillna("").str.strip() == "")
removed_rows.append(df[mask_null].assign(drop_reason="null_caption"))
df = df[~mask_null].copy()
print(f"Drop null caption: {mask_null.sum()} rows")

# Step 2: relevance filter
mask_irrelevant = ~df["caption"].str.contains(RELEVANCE_PATTERN, na=False)
removed_rows.append(df[mask_irrelevant].assign(drop_reason="off_topic"))
df = df[~mask_irrelevant].copy()
print(f"Drop off-topic   : {mask_irrelevant.sum()} rows")

# Step 3: clean caption text
df["caption"] = df["caption"].apply(clean_caption)

# drop any that became empty after cleaning
mask_empty_after = df["caption"].str.strip() == ""
removed_rows.append(df[mask_empty_after].assign(drop_reason="empty_after_clean"))
df = df[~mask_empty_after].copy()
print(f"Drop empty after clean: {mask_empty_after.sum()} rows")

# save
df.reset_index(drop=True, inplace=True)
df.to_csv(OUTPUT, index=False)

removed_df = pd.concat(removed_rows, ignore_index=True)
removed_df.to_csv(REMOVED, index=False)

print(f"\nInput : {total_input:,}")
print(f"Output: {len(df):,}")
print(f"Removed: {total_input - len(df):,} ({(total_input - len(df))/total_input*100:.1f}%)")
print(f"\nRemaining per variable:")
print(df.groupby(["variable_number","variable_name"])["post_url"].count().to_string())
print(f"\nOutput : {OUTPUT}")
print(f"Removed: {REMOVED}")
