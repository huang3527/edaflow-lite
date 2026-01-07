from __future__ import annotations

import tempfile
from parser.adapters.mock_sta import MockSTAAdapter
from parser.timing_parser import load_report
from parser.violation_summary import infer_violation_type
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from visualize.slack_distribution import plot_slack_distribution


@st.cache_data(show_spinner=False)
def parse_report_text(report_text: str) -> pd.DataFrame:
    adapter = MockSTAAdapter()
    paths = adapter.parse(report_text)

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


def compute_view(
    df: pd.DataFrame, group: Optional[str], violations_only: bool
) -> pd.DataFrame:
    out = df.copy()
    if group:
        out = out[out["path_group"] == group]
    if violations_only:
        out = out[out["slack"] < 0]
    out = out.sort_values(by=["slack"], ascending=True, kind="mergesort").reset_index(
        drop=True
    )
    return out


def stats_from_df(df: pd.DataFrame) -> dict:
    total = int(len(df))
    violated = int((df["slack"] < 0).sum())
    met = total - violated
    wns = float(df["slack"].min()) if violated > 0 else 0.0
    tns = float(df.loc[df["slack"] < 0, "slack"].sum()) if violated > 0 else 0.0
    return {"total": total, "violated": violated, "met": met, "wns": wns, "tns": tns}


def build_summary_md(df_all: pd.DataFrame, df_view: pd.DataFrame, topk: int) -> str:
    overall = stats_from_df(df_all)
    view = stats_from_df(df_view)

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

    vio_types = (
        df_all[df_all["violation_type"] != "none"]
        .groupby("violation_type")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    top_df = df_view.head(topk)[
        ["slack", "path_group", "violation_type", "startpoint", "endpoint", "notes"]
    ]
    top_md = (
        top_df.to_markdown(index=False)
        if len(top_df)
        else "_No paths match current filters._"
    )

    return f"""# Signoff Summary (edaflow-lite dashboard)

## Overall (all parsed paths)
- Total paths: **{overall["total"]}**
- Violated paths: **{overall["violated"]}**
- MET paths: **{overall["met"]}**
- WNS: **{overall["wns"]:.4f} ns**
- TNS: **{overall["tns"]:.4f} ns**

## Current View (after filters)
- Total paths: **{view["total"]}**
- Violated paths: **{view["violated"]}**
- MET paths: **{view["met"]}**
- WNS: **{view["wns"]:.4f} ns**
- TNS: **{view["tns"]:.4f} ns**

## Breakdown by Path Group (all)
{by_group.to_markdown(index=False)}

## Violation Type Counts (all)
{(vio_types.to_markdown(index=False) if len(vio_types) else "_No violation types inferred._")}

## Top {topk} Worst Paths (current view)
{top_md}

## Recommended Actions (triage)
1. Start with **worst WNS** paths and confirm whether logic depth vs. clock uncertainty dominates.
2. If violations cluster in a single `path_group`, prioritize **constraints** and **clock assumptions**.
3. If `transition` / `max_capacitance` dominate, validate **slew/cap constraints** and fix high-fanout nets first.
"""


def main():
    st.set_page_config(page_title="edaflow-lite", layout="wide")
    st.title("edaflow-lite — Signoff Dashboard (v0.4)")

    st.sidebar.header("Inputs")
    use_sample = st.sidebar.checkbox(
        "Use sample report (reports/timing_report.txt)", value=True
    )
    upload = st.sidebar.file_uploader(
        "Or upload a timing report (.txt)", type=["txt"], disabled=use_sample
    )

    if use_sample:
        report_path = Path("reports/timing_report.txt")
        if not report_path.exists():
            st.error("Sample report not found: reports/timing_report.txt")
            st.stop()
        report_text = load_report(str(report_path))
        st.sidebar.caption(f"Using: {report_path}")
    else:
        if upload is None:
            st.info("Upload a .txt timing report or enable the sample report.")
            st.stop()
        report_text = upload.getvalue().decode("utf-8", errors="replace")

    df_all = parse_report_text(report_text)
    if df_all.empty:
        st.warning("Parsed 0 timing paths from report.")
        st.stop()

    st.sidebar.header("Filters")
    groups = ["(all)"] + sorted(df_all["path_group"].unique().tolist())
    group_choice = st.sidebar.selectbox("Path group", groups, index=0)
    group = None if group_choice == "(all)" else group_choice

    violations_only = st.sidebar.checkbox("Violations only (slack < 0)", value=False)
    topk = st.sidebar.slider(
        "Top K worst paths", min_value=5, max_value=200, value=20, step=5
    )

    df_view = compute_view(df_all, group=group, violations_only=violations_only)

    # Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    overall = stats_from_df(df_all)
    view = stats_from_df(df_view)

    c1.metric("Overall WNS (ns)", f"{overall['wns']:.4f}")
    c2.metric("Overall TNS (ns)", f"{overall['tns']:.4f}")
    c3.metric("View WNS (ns)", f"{view['wns']:.4f}")
    c4.metric("View TNS (ns)", f"{view['tns']:.4f}")
    c5.metric("View Violations", f"{view['violated']}/{view['total']}")

    # Top violations table + downloads
    st.subheader("Top Violations (current view)")
    top_df = df_view.head(topk)
    st.dataframe(top_df, use_container_width=True)

    st.download_button(
        "Download top_violations.csv",
        data=top_df.to_csv(index=False).encode("utf-8"),
        file_name="top_violations.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download paths.csv (all)",
        data=df_all.to_csv(index=False).encode("utf-8"),
        file_name="paths.csv",
        mime="text/csv",
    )

    # Slack distribution plot (save to temp and display)
    st.subheader("Slack Distribution (all paths)")
    with tempfile.TemporaryDirectory() as td:
        png_path = Path(td) / "slack_distribution.png"
        plot_slack_distribution(df_all["slack"].tolist(), png_path)
        st.image(str(png_path), use_container_width=True)

    # Summary markdown
    st.subheader("Signoff Summary (Markdown)")
    md = build_summary_md(df_all=df_all, df_view=df_view, topk=topk)
    st.markdown(md)

    st.download_button(
        "Download summary.md",
        data=md.encode("utf-8"),
        file_name="summary.md",
        mime="text/markdown",
    )


if __name__ == "__main__":
    main()
