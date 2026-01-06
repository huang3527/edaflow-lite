from __future__ import annotations

from parser.timing_parser import TimingPath, parse_timing_report
from typing import List

from .base import AdapterConfig


class MockSTAAdapter:
    def __init__(self, cfg: AdapterConfig | None = None):
        self.cfg = cfg or AdapterConfig(name="mock_sta")

    def parse(self, report_text: str) -> List[TimingPath]:
        # Currently this uses the generic parser, but you can swap logic later
        return parse_timing_report(report_text)
