"""
Coverage data parser for Sentinel DV.

Parses vendor coverage reports and extracts metrics.
Supports simplified coverage formats from major EDA tools.
"""

import re
from pathlib import Path

from sentinel_dv.schemas.common import EvidenceRef
from sentinel_dv.schemas.coverage import CoverageMetric, CoverageSummary


class CoverageParser:
    """
    Parser for coverage reports.

    Supports basic coverage formats from:
    - Questa/ModelSim
    - VCS
    - Xcelium
    """

    # Coverage patterns (simplified)
    COVERAGE_LINE_PATTERN = re.compile(
        r'(\w+)\s+coverage:\s*([\d.]+)%'
    , re.IGNORECASE)

    def __init__(self):
        """Initialize coverage parser."""
        pass

    def parse_report(self, report_path: Path) -> CoverageSummary:
        """
        Parse a coverage report file.

        Args:
            report_path: Path to coverage report

        Returns:
            CoverageSummary with metrics
        """
        with open(report_path, encoding='utf-8', errors='replace') as f:
            content = f.read()

        metrics = []

        # Extract coverage metrics
        for match in self.COVERAGE_LINE_PATTERN.finditer(content):
            kind = match.group(1).lower()
            percentage = float(match.group(2))

            metric = CoverageMetric(
                kind=kind,
                name=kind,
                scope="module",
                hit=int(percentage),
                total=100,
                percentage=percentage
            )
            metrics.append(metric)

        # If no metrics found, create a default metric
        if not metrics:
            metrics.append(
                CoverageMetric(
                    kind="line",
                    name="line",
                    scope="module",
                    hit=0,
                    total=0,
                    percentage=0.0
                )
            )

        return CoverageSummary(
            kind="functional",
            metrics=metrics,
            evidence=[
                EvidenceRef(
                    kind="coverage_report",
                    path=str(report_path)
                )
            ]
        )
