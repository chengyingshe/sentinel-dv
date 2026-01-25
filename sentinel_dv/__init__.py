"""Sentinel DV - Verification Intelligence for AI Agents.

This package provides a Model Context Protocol (MCP) server for safe,
read-only access to verification artifacts from SystemVerilog/UVM/cocotb ecosystems.
"""

__version__ = "1.0.0"
__author__ = "Sentinel DV Team"
__license__ = "Apache-2.0"

from sentinel_dv.schemas.common import EvidenceRef, RunRef
from sentinel_dv.schemas.tests import TestCase, TestTopology
from sentinel_dv.schemas.failures import FailureEvent, FailureSignature
from sentinel_dv.schemas.assertions import AssertionInfo, AssertionFailure
from sentinel_dv.schemas.coverage import CoverageSummary, CoverageMetric

__all__ = [
    "__version__",
    "EvidenceRef",
    "RunRef",
    "TestCase",
    "TestTopology",
    "FailureEvent",
    "FailureSignature",
    "AssertionInfo",
    "AssertionFailure",
    "CoverageSummary",
    "CoverageMetric",
]
