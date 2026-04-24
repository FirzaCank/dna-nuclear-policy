"""
STEP 4 - SENTIMENT ANALYSIS
=============================
Sentiment analysis per statement using two approaches:
  A) IndoBERT (HuggingFace) — high accuracy, requires decent CPU/GPU
  B) Lexicon-based (InSet) — lightweight, no GPU required, suitable for exploration

Input : output/01_flat_statements.csv
Output: output/07_sentiment_scored.csv

INSTALL:
  # For IndoBERT:
  pip install transformers torch sentencepiece

  # For lexicon-based (already included in script):
  pip install pandas
"""

import os
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

INPUT  = "output/01_flat_statements.csv"
OUTPUT = "output/07_sentiment_scored.csv"

# Choose method: "gemini", "indobert", or "lexicon"
METHOD = "gemini"
GEMINI_MODEL = "gemini-2.5-flash"

PROMPT_SENTIMENT = """You are an Indonesian-language sentiment analyst. Your task is to evaluate the emotional valence of a statement (not its stance/position on an issue).

Return a JSON object in this exact format:
{
  "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
  "score": <float 0.0–1.0, where 1.0 = very positive, 0.0 = very negative, 0.5 = neutral>,
  "reasoning": "<one short sentence explaining the rating>"
}

Rules:
- POSITIVE: optimistic, supportive, praising, hopeful, achievement-oriented tone
- NEGATIVE: critical, pessimistic, rejecting, worried, threatening tone
- NEUTRAL: descriptive/factual with no emotional charge
- The score must be consistent with the label
- Output JSON only, no other text
"""


# ════════════════════════════════════════════════════════════════
# METHOD A: Gemini (high accuracy, reuses existing API)
# ════════════════════════════════════════════════════════════════
def score_gemini_single(statement: str) -> dict:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=API_KEY)
    prompt = f"Statement:\n{statement}"
    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SENTIMENT,
                temperature=0.1,
                max_output_tokens=256,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = resp.text.strip().strip("```json").strip("```").strip()
        data = json.loads(raw)
        return {
            "sentiment_label" : data.get("sentiment", "NEUTRAL"),
            "sentiment_score" : float(data.get("score", 0.5)),
            "sentiment_reason": data.get("reasoning", ""),
            "sentiment_method": "gemini",
        }
    except Exception as e:
        return {"sentiment_label": "NEUTRAL", "sentiment_score": 0.5, "sentiment_reason": f"error: {e}", "sentiment_method": "gemini"}


def score_gemini(statements: list) -> list:
    results = []
    for i, stmt in enumerate(statements):
        results.append(score_gemini_single(stmt))
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(statements)} processed...")
        time.sleep(0.1)  # rate limit safety
    return results


# ════════════════════════════════════════════════════════════════
# METHOD B: IndoBERT (high accuracy, requires strong CPU/GPU)
# ════════════════════════════════════════════════════════════════
def score_indobert(statements: list[str]) -> list[dict]:
    """
    Model: indobenchmark/indobert-base-p2 fine-tuned for sentiment
    or: w11wo/indonesian-roberta-base-sentiment-classifier
    """
    from transformers import pipeline

    print("[IndoBERT] Loading model (first run requires ~500MB download)...")
    clf = pipeline(
        "text-classification",
        model="w11wo/indonesian-roberta-base-sentiment-classifier",
        tokenizer="w11wo/indonesian-roberta-base-sentiment-classifier",
        truncation=True,
        max_length=512,
    )

    results = []
    batch_size = 16
    for i in range(0, len(statements), batch_size):
        batch = statements[i:i+batch_size]
        preds = clf(batch)
        for pred in preds:
            label = pred['label'].upper()
            score = pred['score']
            results.append({
                "sentiment_label": label,          # POSITIVE / NEGATIVE / NEUTRAL
                "sentiment_score": round(score, 4),
                "sentiment_method": "indobert",
            })
        if i % 100 == 0:
            print(f"  {i}/{len(statements)} processed...")
    return results


# ════════════════════════════════════════════════════════════════
# METHOD C: Lexicon-based (InSet Lexicon — lightweight)
# ════════════════════════════════════════════════════════════════
# Word subset from InSet Lexicon (Indonesian Sentiment Dictionary)
# Source: github.com/masdevid/ID-OpinionWords
# This is a mini version for exploration — download the full file for production use
POSITIVE_WORDS = {
    "mendukung","dukung","dukungan","setuju","menyetujui","sepakat",
    "mendorong","optimalkan","optimal","prioritas","manfaat","bermanfaat",
    "aman","keamanan","selamat","keselamatan","bersih","berkelanjutan",
    "maju","kemajuan","strategis","penting","kunci","peluang","kesempatan",
    "percepat","akselerasi","inovasi","modern","canggih","andal","murah",
    "efisien","efisiensi","hemat","stabil","stabilitas","kuat","ketahanan",
    "transisi","hijau","ramah","lingkungan","sejahtera","kesejahteraan",
    "transparan","akuntabel","partisipatif","aspirasi","masyarakat","rakyat",
}

NEGATIVE_WORDS = {
    "tolak","menolak","penolakan","keberatan","menentang","tentang","lawan",
    "bahaya","berbahaya","risiko","berisiko","ancaman","mengancam",
    "khawatir","kekhawatiran","takut","ketakutan","was-was",
    "mahal","memberatkan","membebani","beban","hutang","utang",
    "limbah","radioaktif","radiasi","bocor","kebocoran","bencana",
    "monopoli","dominasi","intervensi","asing","ketergantungan",
    "rugikan","merugikan","kerugian","melanggar","pelanggaran",
    "ditolak","gagal","kegagalan","lambat","terhambat","hambatan",
    "tidak aman","tidak transparan","tidak adil","tidak demokratis",
}

def score_lexicon(text: str) -> dict:
    """Score sentiment using a simple lexicon lookup."""
    if not isinstance(text, str):
        return {"sentiment_label": "NEUTRAL", "sentiment_score": 0.5, "sentiment_method": "lexicon"}

    words = text.lower().split()
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)

    total = pos + neg
    if total == 0:
        return {"sentiment_label": "NEUTRAL", "sentiment_score": 0.5, "sentiment_method": "lexicon"}

    ratio = pos / total
    if ratio >= 0.6:
        label = "POSITIVE"
    elif ratio <= 0.4:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return {
        "sentiment_label" : label,
        "sentiment_score" : round(ratio, 4),
        "pos_count"       : pos,
        "neg_count"       : neg,
        "sentiment_method": "lexicon",
    }


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    df = pd.read_csv(INPUT)
    print(f"[INPUT] {len(df)} statements")

    if METHOD == "gemini":
        print(f"[Gemini] Scoring sentiment for {len(df)} statements...")
        results = score_gemini(df['statement'].fillna('').tolist())
        sentiment_df = pd.DataFrame(results)
    elif METHOD == "indobert":
        results = score_indobert(df['statement'].fillna('').tolist())
        sentiment_df = pd.DataFrame(results)
    else:
        print("[Lexicon] Scoring sentiment...")
        results = df['statement'].fillna('').apply(score_lexicon)
        sentiment_df = pd.DataFrame(results.tolist())

    # Merge with original data
    out = pd.concat([df.reset_index(drop=True), sentiment_df], axis=1)

    # Add combined column: position (from LLM) + sentiment (from lexicon/bert)
    # position = thematic stance (PRO/KONTRA toward nuclear)
    # sentiment = emotional valence of the statement text
    out['position_sentiment'] = out['position'] + '_' + out['sentiment_label']

    out.to_csv(OUTPUT, index=False)
    print(f"\n[OUTPUT] → {OUTPUT}")

    print("\n=== SENTIMENT DISTRIBUTION ===")
    print(out['sentiment_label'].value_counts().to_string())
    print("\n=== CROSS: POSITION × SENTIMENT ===")
    print(pd.crosstab(out['position'], out['sentiment_label']).to_string())
    print("\n=== SENTIMENT PER VARIABLE ===")
    print(out.groupby('variable')['sentiment_label'].value_counts().to_string())


if __name__ == "__main__":
    main()
