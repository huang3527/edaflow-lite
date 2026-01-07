from __future__ import annotations

import argparse
import json
from datetime import datetime
from parser.adapters.mock_sta import MockSTAAdapter
from parser.timing_parser import load_report
from parser.violation_summary import infer_violation_type, summarize
from pathlib import Path
from typing import Optional

import pandas as pd

from visualize.slack_distribution import plot_slack_distribution


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _paths_to_df(paths) -> pd.DataFrame:
    rows = []
    for p in paths:
        rows.append(
            {
                "startpoint": p.startpoint,
                "endpoint": p.endpoint,
                "path_group": p.path_group,
                "path_type": p.path_type,
                "slack": p.slack,
                "slack_status": p.slack_status,
                "notes": " ".join(p.notes),
                "violation_type": infer_violation_type(p),
            }
        )
    return pd.DataFrame(rows)


def filter_paths(
    df: pd.DataFrame,
    group: Optional[str],
    violations_only: bool,
) -> pd.DataFrame:
    out = df.copy()

    if group:
        out = out[out["path_group"] == group]

    if violations_only:
        out = out[out["slack"] < 0]

    # stable sort: worst slack first
    out = out.sort_values(by=["slack"], ascending=True, kind="mergesort").reset_index(
        drop=True
    )
    return out


def build_summary_md(
    report_path: Path,
    df_all: pd.DataFrame,
    df_view: pd.DataFrame,
    outdir: Path,
    topk: int,
) -> str:
    # overall stats from ALL parsed paths (not filtered)
    # (You can change this to filtered-only if you prefer)
    # We'll display both overall and current view

    # Rebuild TimingPath list for stats (small dataset; ok)
    # If you want to avoid this, compute directly from df.
    # We'll compute from df for simplicity:
    def stats_from_df(df: pd.DataFrame) -> dict:
        total = int(len(df))
        violated = int((df["slack"] < 0).sum())
        met = total - violated
        wns = float(df["slack"].min()) if violated > 0 else 0.0
        tns = float(df.loc[df["slack"] < 0, "slack"].sum()) if violated > 0 else 0.0
        return {
            "total_paths": total,
            "violated_paths": violated,
            "met_paths": met,
            "wns": wns,
            "tns": tns,
        }

    overall = stats_from_df(df_all)
    view = stats_from_df(df_view)

    # Group breakdown (ALL)
    by_group = (
        df_all.assign(is_viol=(df_all["slack"] < 0))
        .groupby("path_group")
        .agg(
            total_paths=("slack", "size"),
            violated_paths=("is_viol", "sum"),
            wns=("slack", "min"),
            tns=("slack", lambda s: float(s[s < 0].sum())),
        )
        .reset_index()
        .sort_values(by=["wns"], ascending=True)
    )

    # Violation type counts (ALL)
    vio_types = (
        df_all[df_all["violation_type"] != "none"]
        .groupby("violation_type")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    # TopK table (VIEW)
    top_df = df_view.head(topk).copy()
    if len(top_df) == 0:
        top_md = "_No paths match current filters._"
    else:
        top_df = top_df[
            ["slack", "path_group", "violation_type", "startpoint", "endpoint", "notes"]
        ]
        # Keep markdown compact
        top_md = top_df.to_markdown(index=False)

    # Helpful artifact links (relative)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = f"""# Signoff Summary (edaflow-lite)

- Report: `{report_path.name}`
- Generated: `{now}`
- Output directory: `{outdir.as_posix()}`

## Overall (all parsed paths)

- Total paths: **{overall["total_paths"]}**
- Violated paths: **{overall["violated_paths"]}**
- MET paths: **{overall["met_paths"]}**
- WNS: **{overall["wns"]:.4f} ns**
- TNS: **{overall["tns"]:.4f} ns**

## Current View (after filters)

- Total paths: **{view["total_paths"]}**
- Violated paths: **{view["violated_paths"]}**
- MET paths: **{view["met_paths"]}**
- WNS: **{view["wns"]:.4f} ns**
- TNS: **{view["tns"]:.4f} ns**

## Breakdown by Path Group (all)

{by_group.to_markdown(index=False)}

## Violation Type Counts (all)

{(vio_types.to_markdown(index=False) if len(vio_types) else "_No violation types inferred._")}

## Top {topk} Worst Paths (current view)

{top_md}

## Artifacts

- `paths.json`
- `paths.csv`
- `summary.json`
- `top_violations.csv`
- `slack_distribution.png`
"""
    return summary


def main():
    ap = argparse.ArgumentParser(description="edaflow-lite v0.2: mock EDA signoff flow")
    ap.add_argument("--report", required=True, help="Path to timing report txt")
    ap.add_argument("--outdir", default="out", help="Output directory")

    # v0.2 CLI controls
    ap.add_argument(
        "--topk", type=int, default=20, help="Top K worst slack paths to export/report"
    )
    ap.add_argument(
        "--violations-only", action="store_true", help="Only keep paths with slack < 0"
    )
    ap.add_argument(
        "--group", type=str, default=None, help="Filter by a specific path group"
    )

    args = ap.parse_args()

    report_path = Path(args.report)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    text = load_report(str(report_path))

    # Adapter layer (swap for real STA formats later)
    adapter = MockSTAAdapter()
    paths = adapter.parse(text)

    # Build df once
    df_all = _paths_to_df(paths)

    # 1) paths.json
    paths_json = df_all.to_dict(orient="records")
    write_json(paths_json, outdir / "paths.json")

    # 2) paths.csv
    write_csv(df_all, outdir / "paths.csv")

    # 3) summary.json (all paths, not filtered)
    summary_obj = summarize(paths)
    write_json(summary_obj, outdir / "summary.json")

    # Apply filters for “view”
    df_view = filter_paths(
        df_all, group=args.group, violations_only=args.violations_only
    )

    # 4) top_violations.csv (topK of current view)
    top_df = df_view.head(args.topk).copy()
    write_csv(top_df, outdir / "top_violations.csv")

    # 5) slack_distribution.png (all paths; change to df_view if you want filtered plot)
    plot_slack_distribution(
        df_all["slack"].tolist(),
        outdir / "slack_distribution.png",
    )

    # 6) summary.md (one-page report)
    md = build_summary_md(
        report_path=report_path,
        df_all=df_all,
        df_view=df_view,
        outdir=outdir,
        topk=args.topk,
    )
    (outdir / "summary.md").write_text(md, encoding="utf-8")

    print("[OK] Generated artifacts:")
    for p in [
        outdir / "paths.json",
        outdir / "paths.csv",
        outdir / "summary.json",
        outdir / "top_violations.csv",
        outdir / "slack_distribution.png",
        outdir / "summary.md",
    ]:
        print(f" - {p.resolve()}")


if __name__ == "__main__":
    main()
