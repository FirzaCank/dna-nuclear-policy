"""
Merge all Instagram CSVs from input/Socmed/ into one clean file.
- Collapses hashtags/0..N and mentions/0..N into single columns
- Adds variable_number, category, variable_name, keyword from filename mapping
- Deduplicates by post_url (keeps first keyword match)
- Keeps only analysis-relevant columns
Output: output/socmed_merged.csv
"""

import os
import glob
import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).parent.parent
INPUT_DIR   = str(ROOT / "input" / "Socmed")
OUTPUT_PATH = str(ROOT / "output" / "socmed_merged.csv")

# filename stem → (variable_number, category, variable_name, keyword)
FILE_MAP = {
    "1. RUU EBET":                  (1, "Politik & Legislasi",   "Dinamika Pembahasan DIM",              "RUU EBET"),
    "2. PLTN":                      (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan",        "PLTN"),
    "2. IAEA":                      (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan",        "nuklir IAEA"),
    "2. BAPETEN":                   (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan",        "BAPETEN regulasi reaktor"),
    "3. LCOE":                      (3, "Teknokrasi",            "Ideologi & Integritas Data",            "LCOE nuklir"),
    "3. SMR Indonesia":             (3, "Teknokrasi",            "Ideologi & Integritas Data",            "SMR Indonesia"),
    "3. BRIN Nuklir":               (3, "Teknokrasi",            "Ideologi & Integritas Data",            "BRIN nuklir"),
    "3. Nuklir DPR":                (3, "Teknokrasi",            "Ideologi & Integritas Data",            "nuklir DPR"),
    "4. PLTU pensiun":              (4, "Ekonomi & Fiskal",      "Intervensi & Pembiayaan",               "PLTU pensiun"),
    "4. Biaya nuklir":              (4, "Ekonomi & Fiskal",      "Intervensi & Pembiayaan",               "Biaya nuklir"),
    "5. BRIN ESDM":                 (5, "Jaringan Kebijakan",    "Interaksi Pemangku Kepentingan",        "BRIN ESDM"),
    "6. penolakan PLTN":            (6, "Sosial & Lingkungan",   "Periferalisasi & Hak Masyarakat",       "penolakan PLTN"),
    "6. limbah nuklir":             (6, "Sosial & Lingkungan",   "Periferalisasi & Hak Masyarakat",       "limbah nuklir"),
    "7. NZE Indonesia":             (7, "Iklim & Masa Depan",    "Transisi Energi & NZE",                 "NZE Indonesia"),
    "7. Transisi Energy":           (7, "Iklim & Masa Depan",    "Transisi Energi & NZE",                 "transisi energi"),
    "7. Dekarbonisasi":             (7, "Iklim & Masa Depan",    "Transisi Energi & NZE",                 "dekarbonisasi"),
    "7. Just indonesia transition": (7, "Iklim & Masa Depan",    "Transisi Energi & NZE",                 "just transition indonesia"),
    "7. nuklir energi hijau":       (7, "Iklim & Masa Depan",    "Transisi Energi & NZE",                 "nuklir energi hijau"),
}

KEEP_COLS = [
    "post_url",
    "pub_date",
    "username",
    "full_name",
    "caption",
    "like_count",
    "comment_count",
    "hashtags",
    "mentions",
    "variable_number",
    "category",
    "variable_name",
    "keyword",
]


def collapse_array_cols(df, prefix):
    """Collapse prefix/0, prefix/1, ... into a single comma-separated column."""
    arr_cols = sorted(
        [c for c in df.columns if c.startswith(f"{prefix}/") and c[len(prefix)+1:].isdigit()],
        key=lambda c: int(c[len(prefix)+1:])
    )
    if not arr_cols:
        df[prefix] = ""
    else:
        df[prefix] = (
            df[arr_cols]
            .apply(lambda row: ",".join(str(v) for v in row if pd.notna(v) and str(v).strip()), axis=1)
        )
        df.drop(columns=arr_cols, inplace=True)
    return df


frames = []
files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.csv")))

for path in files:
    stem = os.path.splitext(os.path.basename(path))[0]
    if stem not in FILE_MAP:
        print(f"SKIP (no mapping): {stem}")
        continue

    var_num, category, var_name, keyword = FILE_MAP[stem]

    df = pd.read_csv(path, low_memory=False)
    original_rows = len(df)

    df = collapse_array_cols(df, "hashtags")
    df = collapse_array_cols(df, "mentions")

    df["variable_number"] = var_num
    df["category"]        = category
    df["variable_name"]   = var_name
    df["keyword"]         = keyword

    # keep only relevant columns that exist
    cols = [c for c in KEEP_COLS if c in df.columns]
    df = df[cols]

    frames.append(df)
    print(f"  {stem}: {original_rows} rows")

merged = pd.concat(frames, ignore_index=True)
total_before = len(merged)

# deduplicate by post_url, keep first (= first keyword alphabetically by file order)
merged.drop_duplicates(subset="post_url", keep="first", inplace=True)
total_after = len(merged)

merged.sort_values(["variable_number", "pub_date"], inplace=True)
merged.reset_index(drop=True, inplace=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
merged.to_csv(OUTPUT_PATH, index=False)

print(f"\nDone.")
print(f"  Files processed : {len(frames)}")
print(f"  Rows before dedup: {total_before:,}")
print(f"  Rows after dedup : {total_after:,}")
print(f"  Duplicates removed: {total_before - total_after:,}")
print(f"  Output: {OUTPUT_PATH}")
print(f"\nColumns: {list(merged.columns)}")
