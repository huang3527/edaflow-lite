from parser.timing_parser import parse_timing_report

import pandas as pd

from edaflow import _paths_to_df, filter_paths


def test_filter_group_and_violations_only():
    report = """
Startpoint: A
Endpoint:   B
Path Group: g1
Path Type:  max
slack (VIOLATED)                        -0.10
============================================================
Startpoint: C
Endpoint:   D
Path Group: g2
Path Type:  max
slack (MET)                              0.05
============================================================
"""
    paths = parse_timing_report(report)
    df = _paths_to_df(paths)

    dfv = filter_paths(df, group="g1", violations_only=True)
    assert len(dfv) == 1
    assert dfv.iloc[0]["path_group"] == "g1"
    assert dfv.iloc[0]["slack"] < 0    assert len(dfv) == 1
    assert dfv.iloc[0]["path_group"] == "g1"
    assert dfv.iloc[0]["slack"] < 0