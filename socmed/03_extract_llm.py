"""
STEP 3 - LLM EXTRACTION (Stance per Instagram Post)
=====================================================
Extracts stance (PRO/KONTRA/NETRAL) and concept keywords from each caption.
Resumable: skips already-processed post_urls.

Input : output/socmed_cleaned.csv
Output: output/socmed_extracted_raw.jsonl  (one JSON per line)
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT    = Path(__file__).parent.parent
IG_DIR  = ROOT / "output" / "socmed" / "instagram"
INPUT   = IG_DIR / "socmed_cleaned.csv"
OUTPUT  = IG_DIR / "socmed_extracted_raw.jsonl"

API_KEY      = os.getenv("API_KEY")
MODEL        = "gemini-2.5-flash"
SLEEP_SEC    = 1.2
MAX_RETRIES  = 3
TEST_MODE    = False


PROMPT_SYSTEM = """Anda adalah analis wacana kebijakan energi nuklir Indonesia untuk Discourse Network Analysis (DNA) dari media sosial Instagram.

Tugas: Analisis caption Instagram dan tentukan:
1. SIKAP akun terhadap energi nuklir/PLTN/kebijakan energi Indonesia
2. KONSEP utama yang dibahas (max 3 frasa pendek)

SIKAP:
- PRO: mendukung nuklir, PLTN, RUU EBET, SMR, teknologi nuklir
- KONTRA: menolak, mengkritik nuklir, PLTN, limbah radioaktif, risiko keselamatan
- NETRAL: informatif/edukasi tanpa posisi jelas, pertanyaan retoris, fakta saja

ATURAN:
- Satu caption = satu sikap dominan
- Jika caption sangat pendek atau ambigu → NETRAL
- Abaikan hashtag spam, fokus pada teks substantif
- Konsep: frasa spesifik dari isi caption (bukan hashtag)

Kembalikan JSON persis:
{
  "position": "PRO" | "KONTRA" | "NETRAL",
  "concepts": ["konsep1", "konsep2"],
  "reasoning": "satu kalimat singkat alasan sikap"
}"""


def call_gemini(caption: str) -> dict | None:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
        resp = client.models.generate_content(
            model=MODEL,
            contents=caption,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SYSTEM,
                temperature=0.1,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = resp.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text.strip())
        return parsed if isinstance(parsed, dict) else None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    df = pd.read_csv(INPUT)
    if TEST_MODE:
        df = df.head(5)
        print(f"[TEST MODE] Processing 5 rows only")

    # load already-processed
    done = set()
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["post_url"])
                except:
                    pass

    pending = df[~df["post_url"].isin(done)]
    print(f"[INPUT] {len(df)} posts | Done: {len(done)} | Pending: {len(pending)}")

    if len(pending) == 0:
        print("[DONE] All posts already processed.")
        return

    with open(OUTPUT, "a") as out:
        for i, (_, row) in enumerate(pending.iterrows()):
            caption = str(row.get("caption", "")).strip()
            if not caption:
                continue

            result = None
            for attempt in range(MAX_RETRIES):
                result = call_gemini(caption)
                if result:
                    break
                time.sleep(2 ** attempt)

            record = {
                "post_url":       row["post_url"],
                "username":       row["username"],
                "pub_date":       str(row.get("pub_date", "")),
                "variable_number": int(row.get("variable_number", 0)),
                "variable_name":  row.get("variable_name", ""),
                "keyword":        row.get("keyword", ""),
                "position":       result.get("position", "NETRAL") if result else "NETRAL",
                "concepts":       result.get("concepts", []) if result else [],
                "reasoning":      result.get("reasoning", "") if result else "",
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(pending)}] processed")

            time.sleep(SLEEP_SEC)

    print(f"\n[DONE] Output: {OUTPUT}")


if __name__ == "__main__":
    main()
