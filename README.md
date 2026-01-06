# edaflow-lite
A minimal, end-to-end mock EDA signoff pipeline built to demonstrate parsing, data normalization, and automation workflows.

A lightweight mock "EDA signoff" flow:
- Parse a simplified STA timing report
- Generate violation summary (WNS/TNS, group breakdown, violation type inference)
- Visualize slack distribution
- (Optional) baseline ML classifier for violation types

## Repo Structure

edaflow-lite/ \\
├── reports/ \\
│   └── timing_report.txt \\
├── parser/ \\
│   ├── timing_parser.py \\
│   └── violation_summary.py \\
├── visualize/ \\
│   └── slack_distribution.py \\
└── ml/ \\
    └── violation_classifier.ipynb \\

## Quickstart
## v0.1
### 1) Create venv & install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install matplotlib pandas scikit-learn
```
### 2) Create venv & install deps
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

## v0.2 CLI Examples

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
	•	out/paths.json
	•	out/paths.csv
	•	out/summary.json
	•	out/top_violations.csv
	•	out/slack_distribution.png
	•	out/summary.md
