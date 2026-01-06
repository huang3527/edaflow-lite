from __future__ import annotations

import argparse
import json
from parser.adapters.mock_sta import MockSTAAdapter
from parser.timing_parser import load_report
from parser.violation_summary import summarize
from pathlib import Path

import pandas as pd

from visualize.slack_distribution import plot_slack_distribution


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


def main():
    ap = argparse.ArgumentParser(description="edaflow-lite: mock EDA signoff flow")
    ap.add_argument("--report", required=True, help="Path to timing report txt")
    ap.add_argument("--outdir", default="out", help="Output directory")
    args = ap.parse_args()

    report_path = Path(args.report)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    text = load_report(str(report_path))

    # Adapter layer (swap for real STA formats later)
    adapter = MockSTAAdapter()
    paths = adapter.parse(text)

    # 1) paths.json
    paths_json = [p.to_dict() for p in paths]
    write_json(paths_json, outdir / "paths.json")

    # 2) paths.csv
    write_csv(paths_json, outdir / "paths.csv")

    # 3) summary.json
    summary = summarize(paths)
    write_json(summary, outdir / "summary.json")

    # 4) slack_distribution.png
    png_path = plot_slack_distribution(
        [p.slack for p in paths], outdir / "slack_distribution.png"
    )

    print("[OK] Generated artifacts:")
    print(f" - { (outdir / 'paths.json').resolve() }")
    print(f" - { (outdir / 'paths.csv').resolve() }")
    print(f" - { (outdir / 'summary.json').resolve() }")
    print(f" - { png_path.resolve() }")


if __name__ == "__main__":
    main()
