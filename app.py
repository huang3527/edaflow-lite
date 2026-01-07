from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st


def stats_from_df(df: pd.DataFrame) -> dict:
    total = int(len(df))
    violated = int((df["slack"] < 0).sum())
    met = total - violated
    wns = float(df["slack"].min()) if violated > 0 else 0.0
    tns = float(df.loc[df["slack"] < 0, "slack"].sum()) if violated > 0 else 0.0
    return {"total": total, "violated": violated, "met": met, "wns": wns, "tns": tns}


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


@st.cache_data(show_spinner=False)
def load_artifacts(outdir: str) -> dict:
    out = Path(outdir)
    paths_csv = out / "paths.csv"
    top_csv = out / "top_violations.csv"
    summary_md = out / "summary.md"
    slack_png = out / "slack_distribution.png"

    if not paths_csv.exists():
        raise FileNotFoundError(
            f"Missing: {paths_csv}. Run edaflow.py to generate artifacts first."
        )

    df_all = pd.read_csv(paths_csv)

    df_top = pd.read_csv(top_csv) if top_csv.exists() else pd.DataFrame()
    md = summary_md.read_text(encoding="utf-8") if summary_md.exists() else ""
    png_path = slack_png if slack_png.exists() else None

    return {"df_all": df_all, "df_top": df_top, "md": md, "png_path": png_path}


def main():
    st.set_page_config(page_title="edaflow-lite", layout="wide")
    st.title("edaflow-lite — Signoff Dashboard (Artifact Viewer)")

    st.sidebar.header("Artifacts")
    outdir = st.sidebar.text_input("outdir", value="out")
    reload_btn = st.sidebar.button("Reload artifacts")

    # Reload trigger
    if reload_btn:
        load_artifacts.clear()

    try:
        artifacts = load_artifacts(outdir)
    except Exception as e:
        st.error(str(e))
        st.info(
            "Example:\n\npython edaflow.py --report reports/timing_report.txt --outdir out"
        )
        st.stop()

    df_all: pd.DataFrame = artifacts["df_all"]
    md: str = artifacts["md"]
    png_path = artifacts["png_path"]

    if df_all.empty:
        st.warning("paths.csv is empty.")
        st.stop()

    # Filters (viewer-side)
    st.sidebar.header("Viewer Filters")
    groups = ["(all)"] + sorted(df_all["path_group"].dropna().unique().tolist())
    group_choice = st.sidebar.selectbox("Path group", groups, index=0)
    group = None if group_choice == "(all)" else group_choice

    violations_only = st.sidebar.checkbox("Violations only (slack < 0)", value=False)
    topk = st.sidebar.slider(
        "Top K worst paths (viewer)", min_value=5, max_value=200, value=20, step=5
    )

    df_view = compute_view(df_all, group=group, violations_only=violations_only)
    overall = stats_from_df(df_all)
    view = stats_from_df(df_view)

    # Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall WNS (ns)", f"{overall['wns']:.4f}")
    c2.metric("Overall TNS (ns)", f"{overall['tns']:.4f}")
    c3.metric("View WNS (ns)", f"{view['wns']:.4f}")
    c4.metric("View TNS (ns)", f"{view['tns']:.4f}")
    c5.metric("View Violations", f"{view['violated']}/{view['total']}")

    # Top table
    st.subheader("Top Violations (viewer filter)")
    top_df = df_view.head(topk)
    st.dataframe(top_df, use_container_width=True)

    st.download_button(
        "Download top_violations_view.csv",
        data=top_df.to_csv(index=False).encode("utf-8"),
        file_name="top_violations_view.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download paths.csv (all)",
        data=df_all.to_csv(index=False).encode("utf-8"),
        file_name="paths.csv",
        mime="text/csv",
    )

    # Plot image from artifacts
    st.subheader("Slack Distribution (artifact)")
    if png_path is not None:
        st.image(str(png_path), use_container_width=True)
    else:
        st.info("slack_distribution.png not found in outdir.")

    # Summary markdown from artifacts
    st.subheader("Signoff Summary (artifact summary.md)")
    if md.strip():
        st.markdown(md)
        st.download_button(
            "Download summary.md",
            data=md.encode("utf-8"),
            file_name="summary.md",
            mime="text/markdown",
        )
    else:
        st.info("summary.md not found in outdir. Run edaflow.py to generate it.")


if __name__ == "__main__":
    main()
