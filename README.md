# edaflow-lite
> A minimal, end-to-end mock EDA signoff pipeline to demonstrate **parsing**, **data normalization**, and **automation workflows**.

This repo implements a lightweight, mock “EDA signoff” flow:
- Parse a simplified STA timing report
- Compute violation summaries (WNS/TNS, group breakdown, inferred violation types)
- Visualize slack distribution
- (Optional) baseline ML scaffold for violation classification

---

## Repo Structure
```text
edaflow-lite/
├── edaflow.py
├── pyproject.toml
├── reports/
│   └── timing_report.txt
├── parser/
│   ├── timing_parser.py
│   ├── violation_summary.py
│   └── adapters/
│       └── mock_sta.py
├── visualize/
│   └── slack_distribution.py
├── ml/
│   └── violation_classifier.ipynb
├── tests/                  # (optional but recommended)
└── .github/workflows/       # (optional but recommended)
```

## Quickstart

## v0.1 (module-level scripts)

### 1) Create venv & install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install matplotlib pandas scikit-learn
```
### 2) Parse report -> JSON:
```bash
python -m parser.timing_parser --report reports/timing_report.txt
```
### 3) Summary report
```bash
python -m parser.violation_summary --report reports/timing_report.txt
```
### 4) Plot slack distribution
```bash
python visualize/slack_distribution.py --report reports/timing_report.txt --out slack.png
```
### Next Steps (Ideas)
	•	Support real STA formats (PrimeTime/Tempus-like)
	•	Extract more features: arrival/required times, cell arc, clock path delay
	•	Add CSV/JSON outputs for dashboards
	•	Add unit tests + CI

## v0.2 (Signoff-style CLI)

### Run full flow (default topk=20)
```bash
python edaflow.py --report reports/timing_report.txt --outdir out
```
### Only violations 
```bash
python edaflow.py --report reports/timing_report.txt --outdir out --violations-only
```
### Filter by path group
```bash
python edaflow.py --report reports/timing_report.txt --outdir out --group clk_core
```
### Top 50 worst paths (after filters)
```bash
python edaflow.py --report reports/timing_report.txt --outdir out --violations-only --topk 50```
```
### Artifacts:
### Generated under out/:
	•	out/paths.json
	•	out/paths.csv
	•	out/summary.json
	•	out/top_violations.csv
	•	out/slack_distribution.png
	•	out/summary.md

### Roadmap
	•	Real STA formats (PrimeTime / Tempus-like adapters)
	•	Additional extracted features (arrival/required, clock path details)
	•	Dashboard integration (Streamlit)
	•	Unit tests + CI
	•	Type checking (mypy) + lint (ruff)

## v0.4 (Streamlit Dashboard)

### Artifact viewer workflow
1) Generate artifacts:
```bash
python edaflow.py --report reports/timing_report.txt --outdir out
```
2)	Launch dashboard:
```bash
streamlit run app.py
```
### Features:
	•	Upload or use sample timing report
	•	Filter by path_group, violations-only, topk
	•	View WNS/TNS metrics, top violations table, slack histogram
	•	Download top_violations.csv and summary.md

