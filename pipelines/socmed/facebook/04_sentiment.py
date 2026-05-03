"""
STEP 4 - Sentiment per Facebook Post
======================================
Scores sentiment of each caption (POSITIVE/NEGATIVE/NEUTRAL).
Resumable: skips already-processed post_ids.

Input : output/socmed/facebook/facebook_cleaned.csv
Output: output/socmed/facebook/facebook_sentiment.csv

Run: source venv/bin/activate && python socmed/04_sentiment_facebook.py
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

ROOT    = Path(__file__).parent.parent.parent.parent
FB_DIR  = ROOT / "data" / "processed" / "facebook"
INPUT   = FB_DIR / "facebook_cleaned.csv"
OUTPUT  = FB_DIR / "facebook_sentiment.csv"

API_KEY     = os.getenv("API_KEY")
MODEL       = "gemini-2.5-flash"
SLEEP_SEC   = 1.2
MAX_RETRIES = 3
TEST_MODE   = False

PROMPT_SYSTEM = """You are an Indonesian-language sentiment analyst for social media posts about nuclear energy policy.

Evaluate the emotional tone of the Facebook post below.

Return JSON exactly:
{
  "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
  "score": <float 0.0-1.0, where 1.0=very positive, 0.0=very negative, 0.5=neutral>,
  "reasoning": "<one short sentence>"
}

Rules:
- POSITIVE: optimistic, supportive, hopeful, proud, achievement-oriented
- NEGATIVE: critical, worried, rejecting, angry, fearful
- NEUTRAL: factual/informational, no clear emotional charge
- Score must be consistent with label (POSITIVE > 0.6, NEGATIVE < 0.4, NEUTRAL 0.4-0.6)"""


def call_gemini(caption: str) -> dict | None:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
        resp = client.models.generate_content(
            model=MODEL,
            contents=caption[:2000],
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SYSTEM,
                temperature=0.1,
                max_output_tokens=256,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = resp.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    df = pd.read_csv(INPUT)
    if TEST_MODE:
        df = df.head(5)
        print("[TEST MODE] 5 rows only")

    done = {}
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT)
        prev = prev.dropna(subset=["sentiment"])
        done = prev.set_index("post_id")[["sentiment","sentiment_score","sentiment_reasoning"]].to_dict("index")

    pending = df[~df["post_id"].isin(done)]
    print(f"[INPUT] {len(df)} posts | Done: {len(done)} | Pending: {len(pending)}")

    results = list(done.values()) if done else []
    ids_done = list(done.keys())

    for i, (_, row) in enumerate(pending.iterrows()):
        caption = str(row.get("caption", "")).strip()
        if not caption:
            res = {"sentiment": "NEUTRAL", "score": 0.5, "reasoning": "empty"}
        else:
            res = None
            for attempt in range(MAX_RETRIES):
                res = call_gemini(caption)
                if res:
                    break
                time.sleep(2 ** attempt)
            if not res:
                res = {"sentiment": "NEUTRAL", "score": 0.5, "reasoning": "failed"}

        record = row.to_dict()
        record["sentiment"]           = res.get("sentiment", "NEUTRAL")
        record["sentiment_score"]     = res.get("score", 0.5)
        record["sentiment_reasoning"] = res.get("reasoning", "")
        results.append(record)
        ids_done.append(row["post_id"])

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(pending)}] processed")
            pd.DataFrame(results).to_csv(OUTPUT, index=False)

        time.sleep(SLEEP_SEC)

    out_df = df.copy()
    res_df = pd.DataFrame(results)
    if "post_id" in res_df.columns:
        sent_cols = res_df[["post_id","sentiment","sentiment_score","sentiment_reasoning"]]
        out_df = out_df.merge(sent_cols, on="post_id", how="left")

    out_df.to_csv(OUTPUT, index=False)
    print(f"\n[DONE] {len(out_df)} rows → {OUTPUT}")


if __name__ == "__main__":
    main()
