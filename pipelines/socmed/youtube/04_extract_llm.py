"""
STEP 2 — LLM Extraction YouTube (Stance per Video)
===================================================
Extracts stance (PRO/KONTRA/NETRAL) and concept keywords from each video
title + description.
Resumable: skips already-processed video_ids.

Input : output/socmed/youtube/youtube_metadata.csv
Output: output/socmed/youtube/youtube_extracted_raw.jsonl

Run: source venv/bin/activate && python socmed/02_extract_llm_youtube.py
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

ROOT   = Path(__file__).parent.parent.parent.parent
YT_DIR = ROOT / "data" / "processed" / "youtube"
INPUT  = YT_DIR / "youtube_metadata.csv"
OUTPUT = YT_DIR / "youtube_extracted_raw.jsonl"

API_KEY     = os.getenv("API_KEY")
MODEL       = "gemini-2.5-flash"
SLEEP_SEC   = 1.2
MAX_RETRIES = 3
TEST_MODE   = False

PROMPT_SYSTEM = """Anda adalah analis wacana kebijakan energi nuklir Indonesia untuk Discourse Network Analysis (DNA) dari konten YouTube.

Tugas: Analisis judul dan deskripsi video YouTube dan tentukan:
1. SIKAP channel/pembuat konten terhadap energi nuklir/PLTN/kebijakan energi Indonesia
2. KONSEP utama yang dibahas (max 3 frasa pendek)

SIKAP:
- PRO: mendukung nuklir, PLTN, RUU EBET, SMR, teknologi nuklir sebagai solusi energi
- KONTRA: menolak, mengkritik nuklir, PLTN, limbah radioaktif, risiko keselamatan, biaya tinggi
- NETRAL: informatif/berita faktual tanpa posisi jelas, liputan objektif, pertanyaan tanpa jawaban

ATURAN:
- Satu video = satu sikap dominan
- Berita/liputan TV yang hanya meliput fakta tanpa opini → NETRAL
- Jika judul/deskripsi sangat pendek atau tidak relevan nuklir → NETRAL
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
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SYSTEM,
                temperature=0.1,
                max_output_tokens=512,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text_out = resp.text.strip()
        if text_out.startswith("```"):
            text_out = text_out.split("```")[1]
            if text_out.startswith("json"):
                text_out = text_out[4:]
        parsed = json.loads(text_out.strip())
        return parsed if isinstance(parsed, dict) else None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    df = pd.read_csv(INPUT)
    if TEST_MODE:
        df = df.head(5)
        print("[TEST MODE] 5 rows only")

    # load already-processed
    done = set()
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["video_id"])
                except Exception:
                    pass

    pending = df[~df["video_id"].isin(done)]
    print(f"[INPUT] {len(df)} videos | Done: {len(done)} | Pending: {len(pending)}")

    if len(pending) == 0:
        print("[DONE] All videos already processed.")
        return

    with open(OUTPUT, "a") as out:
        for i, (_, row) in enumerate(pending.iterrows()):
            title = str(row.get("video_title", "")).strip()
            desc  = str(row.get("description", "")).strip()
            if desc == "nan":
                desc = ""
            text_input = f"Judul: {title}\n\nDeskripsi: {desc}" if desc else f"Judul: {title}"

            result = None
            for attempt in range(MAX_RETRIES):
                result = call_gemini(text_input)
                if result:
                    break
                time.sleep(2 ** attempt)

            record = {
                "video_id":        row["video_id"],
                "video_url":       row["video_url"],
                "channel_title":   row.get("channel_title", ""),
                "channel_id":      row.get("channel_id", ""),
                "published_at":    str(row.get("published_at", "")),
                "variable_number": int(row.get("variable_number", 0)),
                "variable_name":   row.get("variable_name", ""),
                "keyword":         row.get("keyword", ""),
                "view_count":      row.get("view_count", 0),
                "like_count":      row.get("like_count", 0),
                "comment_count":   row.get("comment_count", 0),
                "subscriber_count": row.get("subscriber_count", 0),
                "position":        result.get("position", "NETRAL") if result else "NETRAL",
                "concepts":        result.get("concepts", []) if result else [],
                "reasoning":       result.get("reasoning", "") if result else "",
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(pending)}] processed")

            time.sleep(SLEEP_SEC)

    print(f"\n[DONE] Output: {OUTPUT}")


if __name__ == "__main__":
    main()
