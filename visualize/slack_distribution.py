from __future__ import annotations

import argparse
from parser.timing_parser import load_report, parse_timing_report
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="Path to timing report txt")
    ap.add_argument("--out", default="slack_distribution.png", help="Output PNG path")
    args = ap.parse_args()

    text = load_report(args.report)
    paths = parse_timing_report(text)
    slacks = [p.slack for p in paths]

    plt.figure()
    plt.hist(slacks, bins=12)
    plt.title("Slack Distribution")
    plt.xlabel("Slack (ns)")
    plt.ylabel("Count")
    plt.tight_layout()

    out_path = Path(args.out)
    plt.savefig(out_path, dpi=200)
    print(f"[OK] saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
