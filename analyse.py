"""
Qualitative Analysis Toolkit - MAXQDA .qdpx parser and report generator.
Implements REFI-QDA open standard for round-trip project exchange.
"""

import argparse
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import csv


# REFI-QDA XML namespaces
REFI_NS = {
    "refi": "urn:QDA-XML:project:1.0",
    "qdc":  "urn:QDA-XML:codebook:1.0",
}


@dataclass
class Code:
    guid: str
    name: str
    color: str = "#6c5ce7"
    description: str = ""
    parent_guid: Optional[str] = None
    segments: List[dict] = field(default_factory=list)

    @property
    def frequency(self) -> int:
        return len(self.segments)


@dataclass
class Source:
    guid: str
    name: str
    source_type: str  # "interview" or "journal"
    plain_text_path: str = ""


@dataclass
class Project:
    name: str
    codes: Dict[str, Code] = field(default_factory=dict)
    sources: Dict[str, Source] = field(default_factory=dict)


def load_qdpx(path: str) -> Project:
    """Parse a MAXQDA .qdpx export file (ZIP-wrapped REFI-QDA XML)."""
    project = Project(name=Path(path).stem)

    with zipfile.ZipFile(path, "r") as zf:
        # project.qde is the main XML manifest
        with zf.open("project.qde") as f:
            tree = ET.parse(f)
            root = tree.getroot()

        ns = REFI_NS["refi"]

        # Parse sources
        for src_el in root.findall(f".//{{{ns}}}TextSource"):
            guid = src_el.get("guid", "")
            name = src_el.get("name", "")
            src_type = "journal" if "journal" in name.lower() or "jrnl" in name.lower() else "interview"
            project.sources[guid] = Source(guid=guid, name=name, source_type=src_type)

        # Parse code system
        for code_el in root.findall(f".//{{{ns}}}Code"):
            guid = code_el.get("guid", "")
            name = code_el.get("name", "")
            color = code_el.get("color", "#6c5ce7")
            desc_el = code_el.find(f"{{{ns}}}Description")
            description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
            parent = code_el.get("isCodable")
            project.codes[guid] = Code(
                guid=guid, name=name, color=color,
                description=description, parent_guid=parent
            )

        # Parse coding segments
        for sel_el in root.findall(f".//{{{ns}}}Selection"):
            code_ref = sel_el.get("creatingUser")  # placeholder; real ref is via CodeRef
            source_ref = sel_el.get("source", "")
            start_pos = int(sel_el.get("startPosition", 0))
            end_pos = int(sel_el.get("endPosition", 0))
            segment_text = ""
            txt_el = sel_el.find(f"{{{ns}}}Segment")
            if txt_el is not None and txt_el.text:
                segment_text = txt_el.text.strip()

            # Link to codes via CodeRef children
            for code_ref_el in sel_el.findall(f"{{{ns}}}CodeRef"):
                c_guid = code_ref_el.get("targetGUID", "")
                if c_guid in project.codes:
                    project.codes[c_guid].segments.append({
                        "source_guid": source_ref,
                        "start": start_pos,
                        "end": end_pos,
                        "text": segment_text,
                    })

    return project


def build_codebook(project: Project) -> List[dict]:
    """Generate a flat codebook with frequencies and source coverage."""
    rows = []
    source_count = len(project.sources)

    for code in project.codes.values():
        source_guids = {seg["source_guid"] for seg in code.segments}
        rows.append({
            "Code ID":      code.guid[:8].upper(),
            "Code Name":    code.name,
            "Definition":   code.description or "(add definition)",
            "Frequency":    code.frequency,
            "Source Count": len(source_guids),
            "Coverage %":   round(100 * len(source_guids) / source_count, 1) if source_count else 0,
            "Exemplar Quote": code.segments[0]["text"][:200] if code.segments else "",
        })

    rows.sort(key=lambda r: r["Frequency"], reverse=True)
    return rows


def build_source_matrix(project: Project) -> Dict[str, Dict[str, int]]:
    """Source x code frequency matrix."""
    matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for code in project.codes.values():
        for seg in code.segments:
            src_guid = seg["source_guid"]
            src_name = project.sources.get(src_guid, Source(src_guid, src_guid, "unknown")).name
            matrix[src_name][code.name] += 1

    return dict(matrix)


def save_codebook_csv(rows: List[dict], output_dir: Path) -> None:
    out_path = output_dir / "codebook.csv"
    if not rows:
        print("No codes found - writing empty codebook.")
    fieldnames = ["Code ID", "Code Name", "Definition", "Frequency",
                  "Source Count", "Coverage %", "Exemplar Quote"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Codebook saved: {out_path}")


def save_matrix_csv(matrix: Dict, output_dir: Path) -> None:
    out_path = output_dir / "theme_matrix.csv"
    if not matrix:
        print("No segments found - writing empty matrix.")
        return
    codes = sorted({c for src in matrix.values() for c in src})
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Source"] + codes)
        for src_name, code_counts in sorted(matrix.items()):
            writer.writerow([src_name] + [code_counts.get(c, 0) for c in codes])
    print(f"Source matrix saved: {out_path}")


def generate_html_report(project: Project, codebook: List[dict], output_dir: Path) -> None:
    """Generate a dark-theme HTML coding report."""
    total_segs = sum(c["Frequency"] for c in codebook)
    top_codes = codebook[:10]

    bars = ""
    max_freq = max((c["Frequency"] for c in top_codes), default=1)
    for c in top_codes:
        pct = round(100 * c["Frequency"] / max_freq)
        bars += f"""
        <div class="bar-row">
          <span class="bar-label">{c['Code Name']}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
          <span class="bar-val">{c['Frequency']}</span>
        </div>"""

    rows = ""
    for c in codebook:
        rows += f"""
        <tr>
          <td><code>{c['Code ID']}</code></td>
          <td><strong>{c['Code Name']}</strong></td>
          <td style="color:#94a3b8;font-size:.85rem">{c['Definition'][:80]}</td>
          <td>{c['Frequency']}</td>
          <td>{c['Source Count']}</td>
          <td>{c['Coverage %']}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>{project.name} - Coding Report</title>
<style>
  body{{background:#0a0a0f;color:#e2e8f0;font-family:'Segoe UI',sans-serif;margin:0;padding:32px}}
  h1{{color:#a29bfe;font-size:1.8rem;margin-bottom:4px}}
  .meta{{color:#94a3b8;font-size:.9rem;margin-bottom:40px}}
  .stats{{display:flex;gap:40px;margin-bottom:40px}}
  .stat-n{{font-size:2rem;font-weight:700;color:#a29bfe}}
  .stat-l{{font-size:.8rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px}}
  .bar-row{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
  .bar-label{{width:180px;font-size:.85rem;text-align:right;color:#e2e8f0;flex-shrink:0}}
  .bar-track{{flex:1;background:#1a1a26;border-radius:4px;height:10px}}
  .bar-fill{{background:#6c5ce7;height:10px;border-radius:4px}}
  .bar-val{{width:32px;font-size:.82rem;color:#a29bfe}}
  table{{width:100%;border-collapse:collapse;margin-top:40px}}
  th{{background:#12121a;color:#a29bfe;padding:10px 14px;text-align:left;font-size:.78rem;text-transform:uppercase;letter-spacing:.4px}}
  td{{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.04);font-size:.88rem}}
  code{{background:#1a1a26;padding:2px 8px;border-radius:4px;font-size:.8rem;color:#a29bfe}}
</style>
</head><body>
<h1>{project.name}</h1>
<div class="meta">Generated by qualitative-analysis-toolkit | REFI-QDA standard</div>
<div class="stats">
  <div><div class="stat-n">{len(project.sources)}</div><div class="stat-l">Sources</div></div>
  <div><div class="stat-n">{len(project.codes)}</div><div class="stat-l">Codes</div></div>
  <div><div class="stat-n">{total_segs}</div><div class="stat-l">Segments</div></div>
</div>
<h3 style="color:#a29bfe;margin-bottom:16px">Top 10 Codes by Frequency</h3>
{bars}
<h3 style="color:#a29bfe;margin:40px 0 16px">Full Codebook</h3>
<table>
<thead><tr><th>ID</th><th>Name</th><th>Definition</th><th>Freq</th><th>Sources</th><th>Coverage</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>"""

    out_path = output_dir / "coding_report.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"HTML report saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Qualitative Analysis Toolkit - QDPX parser")
    parser.add_argument("--project", required=True, help="Path to .qdpx project file")
    parser.add_argument("--output", default="report", help="Output directory (default: report/)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading project: {args.project}")
    project = load_qdpx(args.project)
    print(f"  Sources: {len(project.sources)} | Codes: {len(project.codes)}")

    codebook = build_codebook(project)
    matrix = build_source_matrix(project)

    save_codebook_csv(codebook, output_dir)
    save_matrix_csv(matrix, output_dir)
    generate_html_report(project, codebook, output_dir)

    print(f"\nDone. Reports in {output_dir}/")


if __name__ == "__main__":
    main()
