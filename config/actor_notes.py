"""
config/actor_notes.py
======================
Curated human-readable notes for key/ambiguous actors in the DNA pipeline.

Used by 07_export_analysis_csvs.py to enrich the actor_detail.csv output.

Edit this file to:
  - Add notes for newly discovered ambiguous actors
  - Correct or expand existing explanations
  - Add institution full-name expansions
"""

ACTOR_NOTES: dict[str, str] = {
    "Pemerintah":   "Generic 'government' — unclear which ministry/level. "
                    "Likely refers to central government (Pemerintah Pusat). "
                    "Recommend merging with 'Pemerintah Indonesia' in preprocessing.",
    "Indonesia":    "Ambiguous — could mean the Indonesian government, the country as a whole, "
                    "or statements attributed to Indonesia in international forums. "
                    "Recommend clarifying in source text.",
    "PSLH UGM":     "Pusat Studi Lingkungan Hidup — Universitas Gadjah Mada. "
                    "Environmental Studies Center at UGM. Part of UGM's research cluster. "
                    "Often speaks on environmental impact of nuclear plants.",
    "WALHI":        "Wahana Lingkungan Hidup Indonesia — Indonesia's largest environmental NGO. "
                    "National network with branches in all provinces. Generally anti-nuclear.",
    "WALHI Babel":  "Wahana Lingkungan Hidup Indonesia Kepulauan Bangka Belitung — "
                    "WALHI regional branch in Bangka Belitung Islands. "
                    "Strongly opposed to nuclear plant siting in the islands.",
    "JATAM":        "Jaringan Advokasi Tambang — Mining Advocacy Network. "
                    "Anti-extractive industries NGO. Opposes nuclear expansion.",
    "Bapeten":      "Badan Pengawas Tenaga Nuklir — Nuclear Energy Regulatory Agency. "
                    "Government body overseeing nuclear safety and licensing.",
    "BRIN":         "Badan Riset dan Inovasi Nasional — National Research and Innovation Agency. "
                    "Merged from BATAN, LIPI, LAPAN, BPPT. Main state R&D body.",
    "BATAN":        "Badan Tenaga Nuklir Nasional — former National Nuclear Energy Agency. "
                    "Now merged into BRIN but name still appears in older statements.",
    "PLN":          "Perusahaan Listrik Negara — State electricity company. "
                    "Sole power off-taker in Indonesia. Key stakeholder in nuclear decision.",
    "IAEA":         "International Atomic Energy Agency — UN nuclear watchdog. "
                    "Based in Vienna. Provides technical assistance to Indonesia's nuclear program.",
    "KMSTEB":       "Koalisi Masyarakat Sipil untuk Transisi Energi Berkeadilan — "
                    "Coalition of civil society groups pushing for just energy transition. "
                    "Generally anti-nuclear or cautious.",
    "ESDM":         "Kementerian Energi dan Sumber Daya Mineral — Ministry of Energy and Mineral Resources. "
                    "Main government body setting energy policy, including nuclear.",
    "DPR":          "Dewan Perwakilan Rakyat — House of Representatives. "
                    "Includes multiple fraksi (party caucuses) with different stances on RUU EBET.",
    "KemenPANRB":   "Kementerian Pendayagunaan Aparatur Negara dan Reformasi Birokrasi — "
                    "Ministry of Administrative and Bureaucratic Reform. "
                    "Appears in statements related to civil servant recruitment for nuclear sector.",
    "Greenpeace":   "International environmental NGO. Indonesia office based in Jakarta. "
                    "Consistently anti-nuclear globally and in Indonesia.",
    "ICEL":         "Indonesian Center for Environmental Law — environmental law NGO. "
                    "Focuses on legal challenges to energy projects.",
    "KADIN":        "Kamar Dagang dan Industri Indonesia — Indonesian Chamber of Commerce. "
                    "Generally pro-nuclear as part of energy security/investment argument.",
    "IEA":          "International Energy Agency — Paris-based intergovernmental energy organisation. "
                    "Provides global energy data and policy recommendations.",
    "Bappenas":     "Badan Perencanaan Pembangunan Nasional — National Development Planning Agency. "
                    "Sets long-term energy development roadmap (RPJPN).",
    "DEN":          "Dewan Energi Nasional — National Energy Council. "
                    "Cross-ministerial body that sets national energy policy direction.",
    "Rosatom":      "Russian state nuclear energy corporation. "
                    "Has MoU with Indonesia for nuclear cooperation.",
    "Thorcon":      "ThorCon International — US-based company proposing thorium MSR plant in Indonesia.",
    "IESR":         "Institute for Essential Services Reform — energy policy think tank. "
                    "Generally advocates for renewables, cautious on nuclear.",
}


def get_notes(actor: str) -> str:
    """Return the note for an actor, or empty string if none exists."""
    for key, note in ACTOR_NOTES.items():
        if key.lower() in actor.lower() or actor.lower() in key.lower():
            return note
    return ""
