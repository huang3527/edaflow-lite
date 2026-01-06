from parser.timing_parser import TimingPath
from parser.violation_summary import compute_stats, infer_violation_type


def test_compute_stats_wns_tns():
    paths = [
        TimingPath("A", "B", "g1", "max", -0.10, "VIOLATED", []),
        TimingPath("C", "D", "g1", "max", -0.05, "VIOLATED", []),
        TimingPath("E", "F", "g2", "max", 0.20, "MET", []),
    ]
    stats = compute_stats(paths)
    assert stats.total_paths == 3
    assert stats.violated_paths == 2
    assert stats.met_paths == 1
    assert stats.wns == -0.10
    assert abs(stats.tns - (-0.15)) < 1e-9


def test_infer_violation_type_from_notes():
    p1 = TimingPath(
        "A", "B", "g", "max", -0.1, "VIOLATED", ["transition violation suspected"]
    )
    p2 = TimingPath(
        "A", "B", "g", "max", -0.1, "VIOLATED", ["max_capacitance violation suspected"]
    )
    p3 = TimingPath("A", "B", "g", "max", -0.1, "VIOLATED", [])
    p4 = TimingPath("A", "B", "g", "max", 0.1, "MET", [])

    assert infer_violation_type(p1) == "transition"
    assert infer_violation_type(p2) == "max_capacitance"
    assert infer_violation_type(p3) == "setup"
    assert infer_violation_type(p4) == "none"
