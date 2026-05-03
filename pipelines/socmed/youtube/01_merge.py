"""
Merge all YouTube CSVs from input/socmed/youtube/ into one clean file.
- Each CSV has 3 columns: channel_name, keyword, video_url
- Maps keyword → variable_number, category, variable_name
- Handles double-quoted CSV format (4-7 multi-variable file)
- Deduplicates by video_url
- Adds profile_search_url (YouTube search — direct channel URL not derivable from name)

Output: output/socmed/youtube/youtube_merged.csv
"""

import csv
import glob
import os
import pandas as pd
from pathlib import Path
from urllib.parse import quote

ROOT      = Path(__file__).parent.parent.parent.parent
INPUT_DIR = ROOT / "data" / "raw" / "youtube"
OUTPUT    = ROOT / "data" / "processed" / "youtube" / "youtube_merged.csv"

# keyword (lowercase) → (variable_number, category, variable_name)
KEYWORD_MAP = {
    "ruu ebet":                    (1, "Politik & Legislasi",   "Dinamika Pembahasan DIM"),
    "pltn":                        (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan"),
    "nuklir iaea":                 (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan"),
    "iaea":                        (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan"),
    "bapeten":                     (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan"),
    "bapeten regulasi reaktor":    (2, "Strategi & Keamanan",   "Keamanan Nasional & Kedaulatan"),
    "lcoe nuklir":                 (3, "Teknokrasi",            "Ideologi & Integritas Data"),
    "smr indonesia":               (3, "Teknokrasi",            "Ideologi & Integritas Data"),
    "brin nuklir":                 (3, "Teknokrasi",            "Ideologi & Integritas Data"),
    "nuklir dpr":                  (3, "Teknokrasi",            "Ideologi & Integritas Data"),
    "pensiun pltu":                (4, "Ekonomi & Fiskal",      "Intervensi & Pembiayaan"),
    "biaya nuklir":                (4, "Ekonomi & Fiskal",      "Intervensi & Pembiayaan"),
    "brin esdm":                   (5, "Jaringan Kebijakan",    "Interaksi Pemangku Kepentingan"),
    "penolakan pltn":              (6, "Sosial & Lingkungan",   "Periferalisasi & Hak Masyarakat"),
    "limbah nuklir":               (6, "Sosial & Lingkungan",   "Periferalisasi & Hak Masyarakat"),
    "nze indonesia":               (7, "Iklim & Masa Depan",    "Transisi Energi & NZE"),
    "net zero emission indonesia": (7, "Iklim & Masa Depan",    "Transisi Energi & NZE"),
    "transisi energi":             (7, "Iklim & Masa Depan",    "Transisi Energi & NZE"),
    "dekarbonisasi":               (7, "Iklim & Masa Depan",    "Transisi Energi & NZE"),
    "just transition indonesia":   (7, "Iklim & Masa Depan",    "Transisi Energi & NZE"),
    "nuklir energi hijau":         (7, "Iklim & Masa Depan",    "Transisi Energi & NZE"),
}


def read_csv_safe(path: Path) -> pd.DataFrame:
    """Read CSV, handling double-quoted format used in some files."""
    try:
        df = pd.read_csv(path)
        if len(df.columns) == 1:
            raise ValueError("single column — likely double-quoted format")
        return df
    except Exception:
        # parse double-wrapped format: each line is "col1,""col2"",""col3"""
        with open(path) as f:
            lines = f.readlines()
        rows = []
        for line in lines:
            line = line.strip()
            if line.startswith('"') and line.endswith('"'):
                inner = line[1:-1].replace('""', '"')
                rows.append(next(csv.reader([inner])))
            else:
                rows.append(next(csv.reader([line])))
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows[1:], columns=rows[0])


def map_keyword(kw: str):
    kw_lower = kw.strip().lower()
    if kw_lower in KEYWORD_MAP:
        return KEYWORD_MAP[kw_lower]
    # partial match
    for key, val in KEYWORD_MAP.items():
        if key in kw_lower or kw_lower in key:
            return val
    return (0, "Tidak Diketahui", "Tidak Diketahui")


frames = []
files = sorted(INPUT_DIR.glob("*.csv"))

for path in files:
    df = read_csv_safe(path)
    if df.empty:
        print(f"  SKIP (empty): {path.name}")
        continue

    # normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    if "video_url" not in df.columns or "channel_name" not in df.columns:
        print(f"  SKIP (missing cols): {path.name} — {list(df.columns)}")
        continue

    # map keyword → variable
    df["variable_number"] = df["keyword"].apply(lambda k: map_keyword(k)[0])
    df["category"]        = df["keyword"].apply(lambda k: map_keyword(k)[1])
    df["variable_name"]   = df["keyword"].apply(lambda k: map_keyword(k)[2])

    # profile search URL (best available without channel ID)
    df["profile_search_url"] = df["channel_name"].apply(
        lambda n: f"https://www.youtube.com/results?search_query={quote(str(n))}" if pd.notna(n) else ""
    )

    frames.append(df)
    print(f"  {path.name}: {len(df)} rows")

merged = pd.concat(frames, ignore_index=True)
total_before = len(merged)

merged.drop_duplicates(subset="video_url", keep="first", inplace=True)
merged.sort_values(["variable_number", "channel_name"], inplace=True)
merged.reset_index(drop=True, inplace=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
merged.to_csv(OUTPUT, index=False)

print(f"\nDone.")
print(f"  Files    : {len(frames)}")
print(f"  Before dedup: {total_before}")
print(f"  After dedup : {len(merged)}")
print(f"  Columns  : {list(merged.columns)}")
print(f"  Output   : {OUTPUT}")
