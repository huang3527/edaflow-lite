from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from .timing_parser import TimingPath


@dataclass
class ViolationStats:
    total_paths: int
    violated_paths: int
    met_paths: int
    wns: float  # worst negative slack (most negative)
    tns: float  # total negative slack (sum of all negative slacks)


def compute_stats(paths: List[TimingPath]) -> ViolationStats:
    total = len(paths)
    neg_slacks = [p.slack for p in paths if p.slack < 0]
    violated = len(neg_slacks)
    met = total - violated
    wns = min(neg_slacks) if neg_slacks else 0.0
    tns = sum(neg_slacks) if neg_slacks else 0.0
    return ViolationStats(
        total_paths=total,
        violated_paths=violated,
        met_paths=met,
        wns=wns,
        tns=tns,
    )


def group_by_path_group(paths: List[TimingPath]) -> Dict[str, List[TimingPath]]:
    d: Dict[str, List[TimingPath]] = defaultdict(list)
    for p in paths:
        d[p.path_group].append(p)
    return dict(d)


def infer_violation_type(path: TimingPath) -> str:
    """
    Very lightweight heuristic.
    In real STA, you'd parse explicit violation sections.
    Here we infer from notes or endpoint types.
    """
    notes = " ".join(path.notes).lower()
    if "transition" in notes:
        return "transition"
    if "capacitance" in notes or "max_capacitance" in notes:
        return "max_capacitance"
    if path.slack < 0:
        return "setup"
    return "none"


def count_violation_types(paths: List[TimingPath]) -> Dict[str, int]:
    c: Dict[str, int] = defaultdict(int)
    for p in paths:
        vt = infer_violation_type(p)
        if vt != "none":
            c[vt] += 1
    return dict(c)


def summarize(paths: List[TimingPath]) -> Dict:
    stats = compute_stats(paths)
    by_group = group_by_path_group(paths)

    group_stats = {}
    for g, ps in by_group.items():
        group_stats[g] = compute_stats(ps).__dict__

    vio_types = count_violation_types(paths)

    return {
        "overall": stats.__dict__,
        "by_path_group": group_stats,
        "violation_types": vio_types,
    }


if __name__ == "__main__":
    import argparse
    import json

    from .timing_parser import load_report, parse_timing_report

    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    text = load_report(args.report)
    paths = parse_timing_report(text)

    print(json.dumps(summarize(paths), indent=2))
