"""
config/keyword_merge.py
========================
Keyword/topic alias merging for the DNA network visualization.

Some scraped keywords are near-duplicates or sub-topics of the same theme.
This dict maps them to a single canonical label so the bipartite network
stays clean and readable.

Edit this file to:
  - Merge additional duplicate keywords
  - Split a merged topic back into separate nodes
"""

KEYWORD_MERGE: dict[str, str] = {
    "RUU EBET DIM":                        "RUU EBET",
    "RUU EBET PP 40 2025 harmonisasi":     "RUU EBET",
    "panja EBET nuklir":                   "RUU EBET",
    "DIM nuklir fraksi sidang":            "RUU EBET",
    "just transition nuklir Indonesia":    "just transition nuklir",
    "PLTU nuklir just transition":         "just transition nuklir",
}
