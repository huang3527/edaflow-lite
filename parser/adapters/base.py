from __future__ import annotations

from dataclasses import dataclass
from parser.timing_parser import TimingPath
from typing import List, Protocol


@dataclass(frozen=True)
class AdapterConfig:
    """
    Placeholder config for adapter behavior.
    For real tools, you'd include knobs like:
    - max paths per endpoint
    - whether to parse hold/setup separately
    - unit scaling (ps/ns)
    """

    name: str = "base"


class ReportAdapter(Protocol):
    def parse(self, report_text: str) -> List[TimingPath]: ...
