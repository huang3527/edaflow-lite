from parser.timing_parser import parse_timing_report


def test_parse_extracts_paths_and_slack():
    report = """
Startpoint: A
Endpoint:   B
Path Group: clk
Path Type:  max
slack (VIOLATED)                        -0.10
============================================================
Startpoint: C
Endpoint:   D
Path Group: clk
Path Type:  max
slack (MET)                              0.05
============================================================
"""
    paths = parse_timing_report(report)
    assert len(paths) == 2
    assert paths[0].startpoint == "A"
    assert paths[0].endpoint == "B"
    assert paths[0].path_group == "clk"
    assert paths[0].slack == -0.10
    assert paths[0].slack_status == "VIOLATED"
    assert paths[1].slack_status == "MET"


def test_parse_skips_block_without_slack():
    report = """
Startpoint: A
Endpoint:   B
Path Group: clk
Path Type:  max
# no slack line here
============================================================
"""
    paths = parse_timing_report(report)
    assert len(paths) == 0
