"""
STEP 3 - LLM Extraction Twitter (Stance per Tweet)
====================================================
Extracts stance (PRO/KONTRA/NETRAL) and concept keywords from each tweet.
Resumable: skips already-processed tweet_ids.

Input : data/processed/twitter/twitter_cleaned.csv
Output: data/processed/twitter/twitter_extracted_raw.jsonl

Run: source venv/bin/activate && python pipelines/socmed/twitter/03_extract_llm.py
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")

ROOT    = Path(__file__).parent.parent.parent.parent
TW_DIR  = ROOT / "data" / "processed" / "twitter"
INPUT   = TW_DIR / "twitter_cleaned.csv"
OUTPUT  = TW_DIR / "twitter_extracted_raw.jsonl"

API_KEY     = os.getenv("API_KEY")
MODEL       = "gemini-2.5-flash"
SLEEP_SEC   = 1.2
MAX_RETRIES = 3
TEST_MODE   = False

PROMPT_SYSTEM = """Anda adalah analis wacana kebijakan energi nuklir Indonesia untuk Discourse Network Analysis (DNA) dari media sosial Twitter/X.

Tugas: Analisis tweet dan tentukan:
1. SIKAP akun terhadap energi nuklir/PLTN/kebijakan energi Indonesia
2. KONSEP utama yang dibahas (max 3 frasa pendek)

SIKAP:
- PRO: mendukung nuklir, PLTN, RUU EBET, SMR, teknologi nuklir sebagai solusi energi
- KONTRA: menolak, mengkritik nuklir, PLTN, limbah radioaktif, risiko keselamatan, biaya tinggi
- NETRAL: informatif/berita faktual tanpa posisi jelas, edukasi, pertanyaan tanpa jawaban

ATURAN:
- Satu tweet = satu sikap dominan
- Jika teks sangat pendek atau ambigu → NETRAL
- Fokus pada teks substantif, abaikan tautan dan hashtag
- Konsep: frasa spesifik dari isi konten (bukan hashtag generik)

Kembalikan JSON persis:
{
  "position": "PRO" | "KONTRA" | "NETRAL",
  "concepts": ["konsep1", "konsep2"],
  "reasoning": "satu kalimat singkat alasan sikap"
}"""


def call_gemini(text: str) -> dict | None:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
        resp = client.models.generate_content(
            model=MODEL,
            contents=text[:2000],
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SYSTEM,
                temperature=0.1,
                max_output_tokens=512,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = resp.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        return parsed if isinstance(parsed, dict) else None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    df = pd.read_csv(INPUT)
    if TEST_MODE:
        df = df.head(5)
        print("[TEST MODE] 5 rows only")

    done = set()
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["tweet_id"])
                except Exception:
                    pass

    pending = df[~df["tweet_id"].isin(done)]
    print(f"[INPUT] {len(df)} tweets | Done: {len(done)} | Pending: {len(pending)}")

    if len(pending) == 0:
        print("[DONE] All tweets already processed.")
        return

    with open(OUTPUT, "a") as out:
        for i, (_, row) in enumerate(pending.iterrows()):
            text = str(row.get("text", "")).strip()
            if not text:
                continue

            result = None
            for attempt in range(MAX_RETRIES):
                result = call_gemini(text)
                if result:
                    break
                time.sleep(2 ** attempt)

            record = {
                "tweet_id"       : row["tweet_id"],
                "tweet_url"      : row.get("tweet_url", ""),
                "username"       : row.get("username", ""),
                "user_name"      : row.get("user_name", ""),
                "pub_date"       : str(row.get("pub_date", "")),
                "variable_number": int(float(str(row.get("variable_number", 0)))),
                "variable_name"  : row.get("variable_name", ""),
                "keyword"        : row.get("keyword", ""),
                "favorite_count" : row.get("favorite_count", 0),
                "retweet_count"  : row.get("retweet_count", 0),
                "position"       : result.get("position", "NETRAL") if result else "NETRAL",
                "concepts"       : result.get("concepts", []) if result else [],
                "reasoning"      : result.get("reasoning", "") if result else "",
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(pending)}] processed")

            time.sleep(SLEEP_SEC)

    print(f"\n[DONE] Output: {OUTPUT}")


if __name__ == "__main__":
    main()
