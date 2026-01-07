from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def plot_slack_distribution(
    slacks: Iterable[float], out_path: str | Path, title: str = "Slack Distribution"
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    slacks = list(slacks)

    plt.figure()
    plt.hist(slacks, bins=12)
    plt.title(title)
    plt.xlabel("Slack (ns)")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return out_path


def main():
    import argparse
    from parser.timing_parser import load_report, parse_timing_report

    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", default="slack_distribution.png")
    args = ap.parse_args()

    text = load_report(args.report)
    paths = parse_timing_report(text)
    out = plot_slack_distribution([p.slack for p in paths], args.out)
    print(f"[OK] saved: {out.resolve()}")


if __name__ == "__main__":
    main()
