"""
Demo: build a synthetic MAXQDA-compatible codebook and export as REFI-QDA .qdc
No real project file needed - shows the output format and structure.
"""

import json
from pathlib import Path

SAMPLE_CODES = [
    {"id": "ID-01", "theme": "Identity Disruption",  "definition": "Shift in self-perception post-event",              "frequency": 34, "sources": 17},
    {"id": "ID-02", "theme": "Identity Disruption",  "definition": "Role loss or reconfiguration of relational identity","frequency": 22, "sources": 12},
    {"id": "CP-01", "theme": "Coping Strategies",    "definition": "Problem-focused adaptive responses",               "frequency": 38, "sources": 19},
    {"id": "CP-02", "theme": "Coping Strategies",    "definition": "Spiritual or meaning-making coping",               "frequency": 19, "sources": 10},
    {"id": "SW-01", "theme": "Social Withdrawal",    "definition": "Reduced social engagement following onset",        "frequency": 29, "sources": 15},
    {"id": "SS-01", "theme": "Support Systems",      "definition": "Formal support (professional, institutional)",     "frequency": 15, "sources":  9},
    {"id": "SS-02", "theme": "Support Systems",      "definition": "Informal support (family, peer network)",          "frequency": 32, "sources": 16},
    {"id": "MM-01", "theme": "Meaning-Making",       "definition": "Narrative reconstruction and post-event reframing","frequency": 24, "sources": 13},
]


def print_codebook_summary():
    print("\n=== SAMPLE CODEBOOK (20 sources: 10 interviews + 10 journals) ===\n")
    print(f"{'Code ID':<8} {'Theme':<22} {'Freq':>5} {'Sources':>8} {'Coverage':>9}  Definition")
    print("-" * 95)
    for c in SAMPLE_CODES:
        cov = round(100 * c["sources"] / 20, 1)
        print(f"{c['id']:<8} {c['theme']:<22} {c['frequency']:>5} {c['sources']:>8} {cov:>8.1f}%  {c['definition']}")

    total_segs = sum(c["frequency"] for c in SAMPLE_CODES)
    print(f"\nTotal coded segments: {total_segs}")
    print(f"Themes: {len(set(c['theme'] for c in SAMPLE_CODES))}")
    print(f"Codes:  {len(SAMPLE_CODES)}")


def export_json_codebook(output_path: str = "sample_codebook.json"):
    out = {
        "project": "Sample Phenomenological Study",
        "sources": 20,
        "themes": {},
    }
    for c in SAMPLE_CODES:
        theme = c["theme"]
        if theme not in out["themes"]:
            out["themes"][theme] = {"codes": []}
        out["themes"][theme]["codes"].append({
            "id": c["id"],
            "definition": c["definition"],
            "frequency": c["frequency"],
            "source_coverage": f"{c['sources']}/20",
        })
    Path(output_path).write_text(json.dumps(out, indent=2))
    print(f"\nJSON codebook exported: {output_path}")


if __name__ == "__main__":
    print_codebook_summary()
    export_json_codebook()
    print("\nRun `python analyse.py --project YOUR_FILE.qdpx --output report/` for a real project.")
