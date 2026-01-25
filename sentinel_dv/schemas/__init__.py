"""Schemas module initialization."""

from sentinel_dv.schemas.assertions import AssertionFailure, AssertionInfo
from sentinel_dv.schemas.common import EvidenceRef, PaginationInfo, RunRef
from sentinel_dv.schemas.coverage import CoverageMetric, CoverageSummary
from sentinel_dv.schemas.failures import FailureEvent, FailureSignature
from sentinel_dv.schemas.regressions import DiffItem, RegressionSummary, RunDiff
from sentinel_dv.schemas.tests import InterfaceBinding, TestCase, TestTopology, UvmTopology
from sentinel_dv.schemas.versioning import CURRENT_SCHEMA_VERSION, get_schema_version

__all__ = [
    # Common
    "EvidenceRef",
    "RunRef",
    "PaginationInfo",
    # Tests
    "TestCase",
    "TestTopology",
    "UvmTopology",
    "InterfaceBinding",
    # Failures
    "FailureEvent",
    "FailureSignature",
    # Assertions
    "AssertionInfo",
    "AssertionFailure",
    # Coverage
    "CoverageSummary",
    "CoverageMetric",
    # Regressions
    "RegressionSummary",
    "RunDiff",
    "DiffItem",
    # Versioning
    "CURRENT_SCHEMA_VERSION",
    "get_schema_version",
]
