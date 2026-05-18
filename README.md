# Qualitative Analysis Toolkit

Python toolkit for **phenomenological and thematic analysis** — parses MAXQDA `.qdpx` exports via the REFI-QDA open standard, generates structured codebooks, and produces frequency/cross-tabulation reports.

## What it does

- Parse `.qdpx` project exports from MAXQDA (REFI-QDA XML standard)
- Build and validate codebooks programmatically
- Generate coding frequency reports and source coverage matrices
- Export thematic summaries with exemplar quotes
- Visualise theme co-occurrence as a heatmap

## Quickstart

```bash
pip install -r requirements.txt
python analyse.py --project sample_project.qdpx --output report/
```

## Output

| File | Description |
|---|---|
| `codebook.xlsx` | Full codebook - codes, definitions, frequencies, source counts |
| `theme_matrix.xlsx` | Source x theme coverage matrix |
| `coding_report.html` | Dark-theme interactive report with quote evidence |
| `maxmaps_export.json` | Code relationship data for visualisation |

## Methods

Supports Braun & Clarke thematic analysis and IPA (interpretive phenomenological analysis) write-up frameworks. Codebook structure follows REFI-QDA `.qdc` standard for round-trip import back into MAXQDA, NVivo, and Atlas.ti.

## Author

Dr. Sandeep Grover — PhD, 10+ years applied research, 60+ peer-reviewed publications
