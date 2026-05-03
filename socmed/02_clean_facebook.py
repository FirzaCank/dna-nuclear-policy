"""
STEP 2 - Clean Facebook Raw Data
==================================
Input : output/socmed/facebook/facebook_raw.csv
Output: output/socmed/facebook/facebook_cleaned.csv
        output/socmed/facebook/facebook_removed.csv
"""

import re
import pandas as pd
from pathlib import Path

ROOT    = Path(__file__).parent.parent
FB_DIR  = ROOT / "output" / "socmed" / "facebook"
INPUT   = FB_DIR / "facebook_raw.csv"
OUTPUT  = FB_DIR / "facebook_cleaned.csv"
REMOVED = FB_DIR / "facebook_removed.csv"

RELEVANCE_TERMS = [
    r"nuklir", r"nuclear", r"pltn", r"reaktor", r"reactor",
    r"radioaktif", r"radioactive", r"uranium", r"thorium",
    r"smr", r"small modular reactor", r"bapeten", r"iaea",
    r"ruu ebet", r"uu ebet", r"ebet",
    r"energi baru", r"energi terbarukan", r"new energy",
    r"transisi energi", r"energy transition",
    r"dekarbonisasi", r"decarbonisation", r"decarbonization",
    r"net zero", r"nze", r"karbon netral", r"carbon neutral",
    r"just transition", r"transisi berkeadilan",
    r"emisi karbon", r"carbon emission",
    r"pltu", r"pensiun batu bara", r"coal retirement", r"coal phase",
    r"lcoe", r"levelized cost",
    r"brin", r"esdm",
    r"energi hijau", r"green energy", r"clean energy", r"energi bersih",
    r"limbah radioaktif", r"nuclear waste", r"limbah nuklir",
    r"keamanan nuklir", r"nuclear safety",
    r"pembangkit listrik",
]

RELEVANCE_PATTERN = re.compile("|".join(RELEVANCE_TERMS), re.IGNORECASE)
URL_PATTERN       = re.compile(r"https?://\S+|www\.\S+")


def clean_caption(text):
    if not isinstance(text, str):
        return ""
    text = URL_PATTERN.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        tokens = line.split()
        if not tokens:
            cleaned.append(line)
            continue
        htag_ratio = sum(1 for t in tokens if t.startswith("#")) / len(tokens)
        if htag_ratio < 0.85:
            cleaned.append(line)
    return "\n".join(cleaned).strip()


df = pd.read_csv(INPUT, low_memory=False)
total = len(df)
removed = []

# 1. drop null/empty caption
mask_null = df["caption"].isna() | (df["caption"].fillna("").str.strip() == "")
removed.append(df[mask_null].assign(drop_reason="null_caption"))
df = df[~mask_null].copy()
print(f"Drop null caption  : {mask_null.sum()}")

# 2. relevance filter
mask_irrel = ~df["caption"].str.contains(RELEVANCE_PATTERN, na=False)
removed.append(df[mask_irrel].assign(drop_reason="off_topic"))
df = df[~mask_irrel].copy()
print(f"Drop off-topic     : {mask_irrel.sum()}")

# 3. clean caption
df["caption"] = df["caption"].apply(clean_caption)
mask_empty = df["caption"].str.strip() == ""
removed.append(df[mask_empty].assign(drop_reason="empty_after_clean"))
df = df[~mask_empty].copy()
print(f"Drop empty after   : {mask_empty.sum()}")

# 4. dedup by post_id
before_dedup = len(df)
df.drop_duplicates(subset="post_id", keep="first", inplace=True)
print(f"Drop duplicate id  : {before_dedup - len(df)}")

df.reset_index(drop=True, inplace=True)
df.to_csv(OUTPUT, index=False)
pd.concat(removed, ignore_index=True).to_csv(REMOVED, index=False)

print(f"\nInput  : {total:,}")
print(f"Output : {len(df):,}")
print(f"Removed: {total - len(df):,} ({(total - len(df))/total*100:.1f}%)")
print(f"\nPer variable:")
print(df.groupby(["variable_number","variable_name"])["post_id"].count().to_string())
print(f"\n→ {OUTPUT}")
