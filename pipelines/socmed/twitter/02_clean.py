"""
STEP 2 - Clean Twitter Raw Data
=================================
Input : data/processed/twitter/twitter_raw.csv
Output: data/processed/twitter/twitter_cleaned.csv
        data/processed/twitter/twitter_removed.csv
"""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(__file__).parent.parent.parent.parent
TW_DIR  = ROOT / "data" / "processed" / "twitter"
INPUT   = TW_DIR / "twitter_raw.csv"
OUTPUT  = TW_DIR / "twitter_cleaned.csv"
REMOVED = TW_DIR / "twitter_removed.csv"

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
URL_PATTERN       = re.compile(r"https?://\S+|www\.\S+|t\.co/\S+")
WIB               = timezone(timedelta(hours=7))


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = URL_PATTERN.sub("", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def parse_pub_date(created_at: str) -> str:
    """Convert Twitter created_at (UTC) to WIB date string."""
    try:
        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y")
        dt = dt.replace(tzinfo=timezone.utc).astimezone(WIB)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


df = pd.read_csv(INPUT, low_memory=False, dtype=str)
total = len(df)
removed = []

# 1. parse pub_date from created_at
df["pub_date"] = df["created_at"].apply(parse_pub_date)

# 2. drop null/empty text
mask_null = df["text"].isna() | (df["text"].fillna("").str.strip() == "")
removed.append(df[mask_null].assign(drop_reason="null_text"))
df = df[~mask_null].copy()
print(f"Drop null text     : {mask_null.sum()}")

# 3. relevance filter
mask_irrel = ~df["text"].str.contains(RELEVANCE_PATTERN, na=False)
removed.append(df[mask_irrel].assign(drop_reason="off_topic"))
df = df[~mask_irrel].copy()
print(f"Drop off-topic     : {mask_irrel.sum()}")

# 4. clean text
df["text"] = df["text"].apply(clean_text)
mask_empty = df["text"].str.strip() == ""
removed.append(df[mask_empty].assign(drop_reason="empty_after_clean"))
df = df[~mask_empty].copy()
print(f"Drop empty after   : {mask_empty.sum()}")

# 5. dedup by tweet_id
before_dedup = len(df)
df.drop_duplicates(subset="tweet_id", keep="first", inplace=True)
print(f"Drop duplicate id  : {before_dedup - len(df)}")

df.reset_index(drop=True, inplace=True)
df.to_csv(OUTPUT, index=False)

if removed:
    pd.concat(removed, ignore_index=True).to_csv(REMOVED, index=False)

print(f"\nInput  : {total:,}")
print(f"Output : {len(df):,}")
print(f"Removed: {total - len(df):,} ({(total - len(df))/total*100:.1f}%)")
print(f"\nPer variable:")
print(df.groupby(["variable_number","variable_name"])["tweet_id"].count().to_string())
print(f"\n→ {OUTPUT}")
