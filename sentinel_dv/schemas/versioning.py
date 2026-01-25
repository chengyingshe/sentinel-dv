"""Schema version management for Sentinel DV.

This module defines schema versioning policy and compatibility checking.
"""

from typing import Literal

from pydantic import BaseModel, Field


# Current schema version
CURRENT_SCHEMA_VERSION = "1.0.0"

# Versioning policy:
# - MAJOR: Breaking changes (field removal/rename, enum narrowing, requiredness changes)
# - MINOR: Additive changes (new fields with defaults, new enum values)
# - PATCH: Documentation, clarifications, stricter validation that doesn't break payloads


class SchemaVersion(BaseModel):
    """Schema version information."""

    version: str = Field(
        default=CURRENT_SCHEMA_VERSION,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Schema version in SemVer format",
    )

    @property
    def major(self) -> int:
        """Extract major version number."""
        return int(self.version.split(".")[0])

    @property
    def minor(self) -> int:
        """Extract minor version number."""
        return int(self.version.split(".")[1])

    @property
    def patch(self) -> int:
        """Extract patch version number."""
        return int(self.version.split(".")[2])

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """Check if this version is compatible with another.

        Compatibility rules:
        - Same MAJOR version required
        - Higher MINOR version can read lower (additive changes)
        - PATCH version differences are always compatible

        Args:
            other: Version to check compatibility with.

        Returns:
            True if versions are compatible.
        """
        if self.major != other.major:
            return False
        # Same major version is compatible
        return True


# Schema version changelog
CHANGELOG = {
    "1.0.0": {
        "date": "2026-01-25",
        "changes": [
            "Initial release",
            "Core types: EvidenceRef, RunRef, TimeSpan, PaginationInfo",
            "Test models: TestCase, TestTopology, UvmTopology, InterfaceBinding",
            "Failure models: FailureEvent, FailureSignature",
            "Assertion models: AssertionInfo, AssertionFailure",
            "Coverage models: CoverageSummary, CoverageMetric",
            "Regression models: RegressionSummary, RunDiff",
        ],
        "breaking": False,
    },
}


def get_schema_version() -> str:
    """Get current schema version."""
    return CURRENT_SCHEMA_VERSION


def validate_schema_version(version: str) -> bool:
    """Validate that a version string is valid and supported.

    Args:
        version: Version string to validate.

    Returns:
        True if version is valid and supported.
    """
    try:
        schema_ver = SchemaVersion(version=version)
        current_ver = SchemaVersion(version=CURRENT_SCHEMA_VERSION)
        return schema_ver.is_compatible_with(current_ver)
    except Exception:
        return False
