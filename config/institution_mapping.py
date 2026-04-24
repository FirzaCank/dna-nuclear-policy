"""
config/institution_mapping.py
==============================
Canonical institution mapping for the DNA Nuclear Policy pipeline.

INST_KEYWORDS : ordered list of (substring, canonical_name) tuples.
                Matched case-insensitively against actor name and actor_role.
                Order matters — more specific patterns should come first.

INST_SHORT    : dict of full name → short label (case-insensitive key).
                Applied after INST_KEYWORDS matching.

Edit this file to:
  - Add new institutions
  - Fix wrong mappings
  - Rename canonical labels
"""

import pandas as pd

# ── Keyword → canonical institution ──────────────────────────────────────────
# Ordered: more specific patterns first to avoid early-exit mis-matches.
INST_KEYWORDS = [
    # NGO / Civil Society
    ("walhi kepulauan bangka belitung", "WALHI Babel"),
    ("walhi babel",                     "WALHI Babel"),
    ("walhi",                           "WALHI"),
    ("greenpeace",                      "Greenpeace"),
    ("jatam",                           "JATAM"),
    ("iesr",                            "IESR"),
    ("icel",                            "ICEL"),
    ("celios",                          "CELIOS"),
    ("trend asia",                      "Trend Asia"),
    ("indonesia cerah",                 "CERAH"),
    ("cerah",                           "CERAH"),
    ("iress",                           "IRESS"),
    ("pbhi",                            "PBHI"),
    ("pushep",                          "PUSHEP"),
    ("ekomarin",                        "Ekomarin"),
    ("reforminer",                      "ReforMiner"),
    ("koalisi masyarakat sipil untuk transisi energi berkeadilan", "KMSTEB"),
    ("koalisi masyarakat sipil indonesia untuk energi bersih",     "KMSEB"),
    ("koalisi masyarakat sipil",        "Koalisi MST"),
    ("yayasan srikandi lestari",        "Srikandi Lestari"),
    ("srikandi lestari",                "Srikandi Lestari"),
    ("himni",                           "HIMNI"),
    ("mebni",                           "MEBNI"),
    # Central Government (Ministry)
    ("kementerian esdm",                "ESDM"),
    ("esdm",                            "ESDM"),
    ("menko perekonomian",              "Kemenko Ekonomi"),
    ("kemenko perekonomian",            "Kemenko Ekonomi"),
    ("kemenko polkam",                  "Kemenko Polkam"),
    ("wamenhan",                        "Kemhan"),
    ("menristekdikti",                  "Kemendikti"),
    ("mendiktisaintek",                 "Kemendikti"),
    ("kementerian lingkungan hidup dan kehutanan", "KLHK"),
    ("klhk",                            "KLHK"),
    ("klh",                             "KLH"),
    ("bplh",                            "KLH"),
    ("kemenpanrb",                      "KemenPANRB"),
    ("panrb",                           "KemenPANRB"),
    ("kementerian panrb",               "KemenPANRB"),
    ("kementerian hukum",               "Kemenkumham"),
    ("kemenkumham",                     "Kemenkumham"),
    ("kementerian perindustrian",       "Kemenperin"),
    ("kemenperin",                      "Kemenperin"),
    ("kementerian keuangan",            "Kemenkeu"),
    ("kemenkeu",                        "Kemenkeu"),
    ("wantannas",                       "Wantannas"),
    ("utusan khusus",                   "Istana"),
    ("presiden",                        "Istana"),
    # State-Owned Enterprises / Government Bodies
    ("pt pln (persero)",                "PLN"),
    ("pln indonesia power",             "PLN Power"),
    ("pln",                             "PLN"),
    ("brin",                            "BRIN"),
    ("badan riset dan inovasi nasional","BRIN"),
    ("batan",                           "BATAN"),
    ("bapeten",                         "Bapeten"),
    ("badan pengawas tenaga nuklir",    "Bapeten"),
    ("bappenas",                        "Bappenas"),
    ("badan perencanaan pembangunan nasional", "Bappenas"),
    ("pt pal",                          "PT PAL"),
    ("pertamina",                       "Pertamina"),
    ("thorcon",                         "Thorcon"),
    ("rosatom",                         "Rosatom"),
    # Parliament
    ("komisi xii",                      "DPR"),
    ("komisi vii",                      "DPR"),
    ("komisi iv dprd",                  "DPRD"),
    ("anggota dpr",                     "DPR"),
    ("ketua dpr",                       "DPR"),
    ("wakil ketua dpr",                 "DPR"),
    ("wakil ketua komisi",              "DPR"),
    ("panja",                           "DPR"),
    ("fraksi",                          "DPR"),
    ("dpr",                             "DPR"),
    ("mpr",                             "MPR"),
    ("dpd",                             "DPD"),
    ("dprd",                            "DPRD"),
    ("dewan energi nasional",           "DEN"),
    ("anggota den",                     "DEN"),
    ("sekjen den",                      "DEN"),
    ("den",                             "DEN"),
    # Religion / Business
    ("mui",                             "MUI"),
    ("kadin",                           "KADIN"),
    ("apindo",                          "APINDO"),
    # Academia
    ("universitas gadjah mada",         "UGM"),
    ("ugm",                             "UGM"),
    ("pslh ugm",                        "UGM"),
    ("itpln",                           "ITPLN"),
    ("ipb",                             "IPB"),
    ("universitas indonesia",           "UI"),
    ("feb ui",                          "UI"),
    ("guru besar fe ui",                "UI"),
    ("unair",                           "UNAIR"),
    ("universitas airlangga",           "UNAIR"),
    ("its",                             "ITS"),
    ("unhas",                           "Unhas"),
    ("universitas hasanuddin",          "Unhas"),
    ("unpad",                           "Unpad"),
    ("itb",                             "ITB"),
    ("umy",                             "UMY"),
    ("untirta",                         "Untirta"),
    ("universitas tanjungpura",         "Untan"),
    ("tanjungpura",                     "Untan"),
    ("universitas bangka belitung",     "UBB"),
    ("unhan",                           "Unhan"),
    ("stt migas",                       "STT Migas"),
    ("poltek nuklir",                   "Poltek Nuklir"),
    ("oregon state",                    "Oregon State Univ"),
    ("uns",                             "UNS"),
    ("pakar",                           "Pakar/Akademisi"),
    ("peneliti",                        "Pakar/Akademisi"),
    ("profesor",                        "Pakar/Akademisi"),
    ("guru besar",                      "Pakar/Akademisi"),
    ("ekonom",                          "Ekonom"),
    # Media
    ("antara",                          "ANTARA"),
    ("kompas",                          "Kompas"),
    ("katadata",                        "Katadata"),
    # International
    ("iaea",                            "IAEA"),
    ("international atomic energy agency", "IAEA"),
    ("iea",                             "IEA"),
    ("nea oecd",                        "NEA-OECD"),
    ("world nuclear",                   "WNA"),
    ("fas",                             "FAS"),
    ("federasi ilmuwan amerika",        "FAS"),
    ("ipcc",                            "IPCC"),
    ("aocnmb",                          "AOCNMB"),
    ("kedubes jepang",                  "Pemerintah Jepang"),
    ("meti jepang",                     "Pemerintah Jepang"),
    ("jepang",                          "Pemerintah Jepang"),
    ("kedubes as",                      "Pemerintah AS"),
    ("rusia",                           "Pemerintah Rusia"),
    ("kanada",                          "Pemerintah Kanada"),
    ("korea selatan",                   "Pemerintah Korea Selatan"),
    ("pejabat uni eropa",               "Uni Eropa"),
    # Generic / ambiguous (put last — broad matches)
    ("organisasi masyarakat sipil",     "OMS"),
    ("masyarakat lokal",                "Warga Lokal"),
    ("warga lokal",                     "Warga Lokal"),
    ("negara-negara kepulauan pasifik", "Kep. Pasifik"),
    ("pemerintah dan dpr",              "Pem. & DPR"),
    ("pemerintah indonesia",            "Pemerintah"),
    ("pemerintah",                      "Pemerintah"),
    ("indonesia",                       "Indonesia"),
]

# ── Full name → short display label ──────────────────────────────────────────
INST_SHORT = {
    "koalisi masyarakat sipil untuk transisi energi berkeadilan": "KMSTEB",
    "koalisi masyarakat sipil indonesia untuk energi bersih":      "KMSEB",
    "koalisi masyarakat sipil":        "Koalisi MST",
    "badan riset dan inovasi nasional": "BRIN",
    "badan riset dan inovasi nasional (brin)": "BRIN",
    "kementerian esdm":                "ESDM",
    "kementerian energi dan sumber daya mineral (esdm)": "ESDM",
    "dewan energi nasional":           "DEN",
    "pemerintah indonesia":            "Pemerintah",
    "pemerintah jepang":               "Jepang",
    "pemerintah korea selatan":        "Korea Selatan",
    "pemerintah as":                   "AS",
    "pemerintah rusia":                "Rusia",
    "pemerintah kanada":               "Kanada",
    "pemerintah dan dpr":              "Pem. & DPR",
    "pt pln (persero)":                "PLN",
    "pln indonesia power":             "PLN Power",
    "walhi kepulauan bangka belitung": "WALHI Babel",
    "institute for essential services reform": "IESR",
    "federasi ilmuwan amerika (fas)":  "FAS",
    "panel antarpemerintah untuk perubahan iklim (ipcc)": "IPCC",
    "international atomic energy agency (iaea)": "IAEA",
    "badan pengawas tenaga nuklir (bapeten)": "Bapeten",
    "perusahaan listrik negara (pln)": "PLN",
    "dewan perwakilan rakyat (dpr)":   "DPR",
    "badan perencanaan pembangunan nasional (bappenas)": "Bappenas",
    "kementerian lingkungan hidup dan kehutanan (klhk)": "KLHK",
    "organisasi masyarakat sipil":     "OMS",
    "masyarakat lokal":                "Warga Lokal",
    "warga lokal dan kelompok anti-nuklir": "Warga Lokal",
    "warga dan organisasi masyarakat sipil di pulau galesa dan pulau semesak": "Warga Lokal",
    "negara-negara kepulauan pasifik": "Kep. Pasifik",
    "negara-negara terdekat (korea selatan, jepang, negara-negara kepulauan pasifik)": "Negara Tetangga",
    "pejabat uni eropa":               "Uni Eropa",
    "yayasan srikandi lestari":        "Srikandi Lestari",
}


def normalize_inst(name: str) -> str:
    """Shorten a full institution name using INST_SHORT (case-insensitive lookup)."""
    return INST_SHORT.get(name.lower(), name)


def get_institution(actor: str, actor_type: str, actor_role) -> str | None:
    """
    Map an actor to its canonical institution name.
    Returns None if the actor cannot be mapped (will be excluded from graph).
    """
    if actor_type in ("INSTITUSI", "MEDIA"):
        return normalize_inst(actor)
    role_lower  = (str(actor_role) if pd.notna(actor_role) else "").lower()
    actor_lower = actor.lower()
    for keyword, canonical in INST_KEYWORDS:
        if keyword in role_lower or keyword in actor_lower:
            return normalize_inst(canonical)
    return None
