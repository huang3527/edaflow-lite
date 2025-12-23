from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TimingPath:
    startpoint: str
    endpoint: str
    path_group: str
    path_type: str
    slack: float
    slack_status: str  # MET / VIOLATED
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_BLOCK_SPLIT_RE = re.compile(r"=+\n", re.MULTILINE)

_START_RE = re.compile(r"^Startpoint:\s*(.+)$", re.MULTILINE)
_END_RE = re.compile(r"^Endpoint:\s*(.+)$", re.MULTILINE)
_GROUP_RE = re.compile(r"^Path Group:\s*(.+)$", re.MULTILINE)
_TYPE_RE = re.compile(r"^Path Type:\s*(.+)$", re.MULTILINE)

# slack line examples:
# slack (VIOLATED)                        -0.06
# slack (MET)                              0.15
_SLACK_RE = re.compile(
    r"^\s*slack\s*\((MET|VIOLATED)\)\s*([-+]?\d+(?:\.\d+)?)",
    re.MULTILINE,
)

_NOTE_RE = re.compile(r"^note:\s*(.+)$", re.MULTILINE)


def _extract_one(
    pattern: re.Pattern, text: str, default: Optional[str] = None
) -> Optional[str]:
    m = pattern.search(text)
    return m.group(1).strip() if m else default


def parse_timing_report(report_text: str) -> List[TimingPath]:
    """
    Parse a simplified STA timing report into structured TimingPath objects.

    Robustness philosophy:
    - If a block is missing key fields, we skip it (rather than crashing).
    - Slack is required; otherwise the block is not useful for signoff summary.
    """
    blocks = [b.strip() for b in _BLOCK_SPLIT_RE.split(report_text) if b.strip()]
    paths: List[TimingPath] = []
    print(f"DEBUG: total raw blocks = {len(blocks)}")
    for block in blocks:
        startpoint = _extract_one(_START_RE, block)
        endpoint = _extract_one(_END_RE, block)
        path_group = _extract_one(_GROUP_RE, block, default="UNKNOWN")
        path_type = _extract_one(_TYPE_RE, block, default="UNKNOWN")

        slack_m = _SLACK_RE.search(block)
        if not slack_m:
            # no slack -> ignore this block
            continue
        slack_status = slack_m.group(1).strip()
        slack = float(slack_m.group(2))

        notes = [n.strip() for n in _NOTE_RE.findall(block)]

        if not startpoint or not endpoint:
            # still allow if slack exists, but keep placeholders
            startpoint = startpoint or "UNKNOWN_START"
            endpoint = endpoint or "UNKNOWN_END"

        paths.append(
            TimingPath(
                startpoint=startpoint,
                endpoint=endpoint,
                path_group=path_group,
                path_type=path_type,
                slack=slack,
                slack_status=slack_status,
                notes=notes,
            )
        )

    return paths


def load_report(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="Path to timing_report.txt")
    args = ap.parse_args()

    text = load_report(args.report)
    paths = parse_timing_report(text)
    print(json.dumps([p.to_dict() for p in paths], indent=2))
