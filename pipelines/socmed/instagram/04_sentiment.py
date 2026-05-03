"""
STEP 4 - SENTIMENT PER POST
============================
Scores sentiment of each Instagram caption (POSITIVE/NEGATIVE/NEUTRAL).
Resumable: skips already-processed post_urls.

Input : output/socmed_cleaned.csv
Output: output/socmed_sentiment.csv
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT    = Path(__file__).parent.parent.parent.parent
IG_DIR  = ROOT / "data" / "processed" / "instagram"
INPUT   = IG_DIR / "socmed_cleaned.csv"
OUTPUT  = IG_DIR / "socmed_sentiment.csv"

API_KEY   = os.getenv("API_KEY")
MODEL     = "gemini-2.5-flash"
SLEEP_SEC = 1.2
MAX_RETRIES = 3
TEST_MODE = False


PROMPT_SYSTEM = """You are an Indonesian-language sentiment analyst for social media posts about nuclear energy policy.

Evaluate the emotional tone of the Instagram caption below.

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
- Score must be consistent with the label (POSITIVE > 0.6, NEGATIVE < 0.4, NEUTRAL 0.4-0.6)"""


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
        text = resp.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    df = pd.read_csv(INPUT)
    if TEST_MODE:
        df = df.head(5)
        print("[TEST MODE] Processing 5 rows only")

    # load already done
    done = {}
    if OUTPUT.exists():
        prev = pd.read_csv(OUTPUT)
        done = prev.set_index("post_url")[["sentiment", "sentiment_score", "sentiment_reasoning"]].to_dict("index")

    pending = df[~df["post_url"].isin(done)]
    print(f"[INPUT] {len(df)} posts | Done: {len(done)} | Pending: {len(pending)}")

    results = list(done.values()) if done else []
    post_urls_done = list(done.keys())

    for i, (_, row) in enumerate(pending.iterrows()):
        caption = str(row.get("caption", "")).strip()
        if not caption:
            res = {"sentiment": "NEUTRAL", "score": 0.5, "reasoning": "empty caption"}
        else:
            res = None
            for attempt in range(MAX_RETRIES):
                res = call_gemini(caption)
                if res:
                    break
                time.sleep(2 ** attempt)
            if not res:
                res = {"sentiment": "NEUTRAL", "score": 0.5, "reasoning": "extraction failed"}

        record = row.to_dict()
        record["sentiment"]           = res.get("sentiment", "NEUTRAL")
        record["sentiment_score"]     = res.get("score", 0.5)
        record["sentiment_reasoning"] = res.get("reasoning", "")
        results.append(record)
        post_urls_done.append(row["post_url"])

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(pending)}] processed")
            pd.DataFrame(results).to_csv(OUTPUT, index=False)

        time.sleep(SLEEP_SEC)

    # merge pending results with already-done rows from original df
    out_df = df.copy()
    res_df = pd.DataFrame(results)
    if "post_url" in res_df.columns:
        sentiment_cols = res_df[["post_url","sentiment","sentiment_score","sentiment_reasoning"]]
        out_df = out_df.merge(sentiment_cols, on="post_url", how="left")

    out_df.to_csv(OUTPUT, index=False)
    print(f"\n[DONE] {len(out_df)} rows → {OUTPUT}")


if __name__ == "__main__":
    main()
