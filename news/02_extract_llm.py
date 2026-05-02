"""
STEP 2 - LLM EXTRACTION (Actor-Statement-Position)
"""

import os
import json
import time
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
LLM_PROVIDER = "gemini"
API_KEY       = os.getenv("API_KEY")
# Model per provider
MODELS = {  
    "gemini" : "gemini-2.5-flash",           # Tier 2 — 2K RPM, 100K RPD
    # "ollama" : "qwen2.5:7b",                 # atau llama3.1:8b
}

BATCH_SIZE  = 1       # Proses 1 artikel per request (untuk rate limit aman)
SLEEP_SEC   = 1.2     # Jeda antar request (sesuaikan kalau kena rate limit)
MAX_RETRIES = 3
TEST_MODE   = False    # True = hanya proses 5 artikel pertama untuk testing

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "output" / "cleaned.csv"
OUTPUT = ROOT / "output" / "extracted_raw.jsonl"  # Simpan per-baris JSONL (resumable)
# ══════════════════════════════════════════════════════════════════════════════


PROMPT_SYSTEM = """Anda adalah analis wacana kebijakan nuklir Indonesia yang sangat ahli untuk Discourse Network Analysis (DNA).
Tugas Anda: ekstrak aktor dan pernyataan dari teks berita bahasa Indonesia agar bisa digunakan sebagai input untuk analisis jaringan wacana untuk pemetaan yang akan divisualisasikan.

═══ SYARAT VALID UNIT ANALISIS DNA ═══
Sebuah kalimat/pernyataan HANYA valid untuk DNA jika mengandung KETIGA elemen berikut secara bersamaan:
  1. AKTOR (Siapa): Orang atau organisasi yang membuat pernyataan — disebut eksplisit di teks.
  2. KONSEP/WACANA (Apa): Argumen, pandangan, atau gagasan aktor mengenai isu nuklir/energi.
  3. SIKAP (Bagaimana): Dukungan (PRO) atau penolakan (KONTRA) yang dapat disimpulkan dari kalimat.

JENIS KALIMAT YANG VALID (keduanya boleh):
  ✓ Kutipan langsung: "...teknologi nuklir adalah kunci kedaulatan energi..." — aktor jelas, ada argumen, ada sikap.
  ✓ Narasi/kutipan tidak langsung jurnalis: "Ekonom X meyakini omnibus law tidak akan memicu PHK meluas." — bukan kutipan langsung, tapi valid karena aktor, konsep, dan sikap jelas.
  ✓ Kalimat biasa: "WALHI menolak rencana PLTN karena mengancam lingkungan." — valid karena ada aktor, konsep, dan sikap kontra.
  ✓ Ada wacana argumentasi maupun sikap pro/kontra.

KALIMAT YANG TIDAK VALID — JANGAN EKSTRAK:
  ✗ Fakta/peristiwa tanpa sikap: "Presiden mengunjungi lokasi PLTN." — hanya fakta, tidak ada argumen/sikap.
  ✗ Tindakan diplomatik netral: "Menteri X bertemu Menteri Y di Moskow." — hanya fakta pertemuan, bukan pernyataan.
  ✗ Kehadiran/perjalanan: "Prabowo berangkat ke Moskow." — fakta perjalanan, bukan sikap terhadap isu.
  ✗ Atribusi tanpa argumen: "Rosatom hadir dalam pertemuan tersebut." — tidak ada konsep/sikap.
  ✗ Ada wacana argumentasi maupun sikap pro/kontra.

ATURAN PENTING:
  - Position PRO/KONTRA hanya jika kalimat SECARA EKSPLISIT menunjukkan dukungan atau penolakan terhadap isu nuklir/PLTN.
  - Jangan inferensi sikap dari tindakan (mengunjungi, bertemu, hadir ≠ PRO).
  - NETRAL hanya untuk pernyataan yang mengandung argumen/konsep tapi tidak jelas pro/kontra.
  - AMBIGU untuk pernyataan yang bisa ditafsirkan dua arah.
  - Jika suatu aktor hanya disebutkan melakukan tindakan tanpa argumen → JANGAN ekstrak sama sekali.
  - Jika tidak ada aktor eksplisit → kembalikan array kosong [].
  - Hanya ekstrak pernyataan dengan confidence >= 0.85 (aktor jelas, konsep jelas, sikap jelas).
  - Maksimal 3 pernyataan per artikel — pilih yang PALING JELAS aktor, wacana, dan sikapnya.
  - Urutkan dari yang paling tinggi confidence-nya.
  - Jawab HANYA JSON valid, tanpa penjelasan tambahan.

FORMAT JSON OUTPUT:
[
  {
    "actor": "nama aktor",
    "actor_type": "INDIVIDU|INSTITUSI|FRAKSI|PAKAR|MEDIA",
    "actor_role": "jabatan/peran",
    "statement": "kalimat/pernyataan/kutipan yang mengandung aktor+konsep+sikap (1-3 kalimat)",
    "concept": "konsep/wacana utama (max 5 kata)",
    "position": "PRO|KONTRA|NETRAL|AMBIGU",
    "confidence": 0.0
  }
]

actor_role apabila terdapat singkatan, maka gunakan singkatan saja. Lebih pendek lebih baik. Contoh "Ketua Umum Partai Golkar" → "Ketum Golkar", "Menteri Energi dan Sumber Daya Mineral" → "Menteri ESDM", "Juru Bicara Kementerian Luar Negeri" → "Jubir Kemlu", dll.

"""


def build_prompt(row: pd.Series) -> str:
    return f"""Sub-tema artikel: {row['variable']}
Keyword: {row.get('keyword', '')}
Tanggal: {row['date']}
Sumber: {row['source']}

TEKS ARTIKEL:
{row['content_clean'][:4000]}

Ekstrak semua aktor dan pernyataan dari artikel ini."""


# ── LLM Clients ──────────────────────────────────────────────────────────────

def call_groq(prompt: str, model: str) -> str:
    from groq import Groq
    client = Groq(api_key=API_KEY)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.1,
        max_tokens=2000,
    )
    return resp.choices[0].message.content


def call_gemini(prompt: str, model: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=API_KEY)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=PROMPT_SYSTEM,
            temperature=0.1,
            max_output_tokens=8192,
            thinking_config=types.ThinkingConfig(thinking_budget=0),  # nonaktifkan thinking
        ),
    )
    return resp.text


def call_ollama(prompt: str, model: str) -> str:
    import ollama
    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        options={"temperature": 0.1},
    )
    return resp['message']['content']


CALLERS = {
    # "groq"  : call_groq,
    "gemini": call_gemini,
    # "ollama": call_ollama,
}


def call_llm(prompt: str) -> str:
    model  = MODELS[LLM_PROVIDER]
    caller = CALLERS[LLM_PROVIDER]
    for attempt in range(MAX_RETRIES):
        try:
            return caller(prompt, model)
        except Exception as e:
            print(f"  [retry {attempt+1}] Error: {e}")
            time.sleep(SLEEP_SEC * (attempt + 1))
    return "[]"


def parse_llm_response(raw: str) -> list:
    """Parse JSON dari response LLM, toleran terhadap format tidak sempurna."""
    import re
    raw = raw.strip()
    # Hapus markdown code fences (```json ... ``` atau ``` ... ```)
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        # Coba ekstrak blok JSON array dari dalam teks
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return []


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    df = pd.read_csv(INPUT)
    print(f"[INPUT] {len(df)} artikel")

    # Cek progress (resume jika sudah ada output) — tracking per source_id
    done_ids = set()
    out_path = Path(OUTPUT)
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done_ids.add(rec['source_id'])
                except:
                    pass
        print(f"[RESUME] {len(done_ids)} artikel sudah diproses sebelumnya")

    todo = df[~df['ID'].isin(done_ids)]
    if TEST_MODE:
        n=5
        todo = todo.head(n)
        print(f"[TEST MODE] Hanya memproses {n} artikel pertama\n")
    print(f"[TODO]  {len(todo)} artikel tersisa\n")

    total_statements = 0
    with open(out_path, 'a', encoding='utf-8') as outf:
        for _, row in tqdm(todo.iterrows(), total=len(todo), desc="Extracting"):
            prompt = build_prompt(row)
            raw    = call_llm(prompt)
            actors = parse_llm_response(raw)

            # Filter: confidence >= 0.85, max 3 per artikel
            actors = [a for a in actors if float(a.get('confidence', 0)) >= 0.85]
            actors = sorted(actors, key=lambda a: float(a.get('confidence', 0)), reverse=True)[:3]

            # 1 row per statement (bukan 1 row per artikel)
            if actors:
                for actor_data in actors:
                    record = {
                        "source_id"   : int(row['ID']),
                        "variable"    : row['variable'],
                        "keyword"     : row.get('keyword', ''),
                        "source"      : row['source'],
                        "date"        : str(row['date']),
                        **actor_data,   # actor, actor_type, actor_role, statement, concept, position, confidence
                    }
                    outf.write(json.dumps(record, ensure_ascii=False) + '\n')
                    total_statements += 1
            else:
                # Tulis 1 baris kosong agar source_id tetap tercatat untuk resume
                record = {
                    "source_id" : int(row['ID']),
                    "variable"  : row['variable'],
                    "keyword"   : row.get('keyword', ''),
                    "source"    : row['source'],
                    "date"      : str(row['date']),
                    "actor"     : None,
                }
                outf.write(json.dumps(record, ensure_ascii=False) + '\n')

            time.sleep(SLEEP_SEC)

    print(f"\n[DONE] {total_statements} statements diekstrak → {OUTPUT}")


if __name__ == "__main__":
    main()
