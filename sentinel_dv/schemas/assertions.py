"""Assertion schemas for Sentinel DV."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from sentinel_dv.schemas.common import EvidenceRef


# Assertion languages
AssertionLanguage = Literal["sva", "immediate", "psl", "unknown"]


class AssertionIntent(BaseModel):
    """Assertion intent/purpose metadata."""

    protocol: Optional[str] = Field(None, description="Protocol this assertion checks")
    requirement: Optional[str] = Field(None, description="Requirement or spec reference")


class AssertionInfo(BaseModel):
    """Assertion definition information.

    Represents a static assertion (SVA, immediate, PSL) indexed from
    source code or assertion compile maps.
    """

    id: str = Field(..., description="Stable assertion identifier", min_length=1)
    language: AssertionLanguage = Field(..., description="Assertion language")
    name: str = Field(..., description="Assertion name/label", min_length=1)
    scope: str = Field(
        ..., description="Scope (module/interface/class)", min_length=1
    )
    file: str = Field(..., description="Source file path", min_length=1)
    line: int = Field(..., ge=1, description="Line number in source file")
    intent: Optional[AssertionIntent] = Field(None, description="Assertion intent metadata")
    signals: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Signals referenced in assertion (best-effort)",
    )
    enabled_in_run: Optional[bool] = Field(
        None, description="Whether assertion was enabled in a specific run"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "A_axi_protocol_check_bresp_valid",
                "language": "sva",
                "name": "axi_protocol_check_bresp_valid",
                "scope": "axi_master_agent",
                "file": "rtl/axi_protocol_checker.sv",
                "line": 145,
                "intent": {
                    "protocol": "AXI4",
                    "requirement": "IHI0022E Section A3.4.1",
                },
                "signals": ["bvalid", "bready", "bresp"],
                "enabled_in_run": True,
            }
        }


class AssertionFailure(BaseModel):
    """Runtime assertion failure instance.

    Represents a specific assertion firing during simulation.
    Links to AssertionInfo via assertion_id.
    """

    assertion_id: str = Field(..., description="Reference to AssertionInfo.id")
    test_id: str = Field(..., description="Test where assertion failed")
    time_ns: Optional[int] = Field(None, ge=0, description="Simulation time in nanoseconds")
    message: str = Field(
        ...,
        max_length=2048,
        description="Failure message (bounded and redacted)",
    )
    evidence: list[EvidenceRef] = Field(
        default_factory=list, max_length=10, description="Evidence references"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "assertion_id": "A_axi_protocol_check_bresp_valid",
                "test_id": "T20260125_142305_axi_burst_test",
                "time_ns": 1250,
                "message": "Expected OKAY but got DECERR on write response channel",
                "evidence": [
                    {
                        "kind": "log",
                        "path": "regression/axi_burst_test.log",
                        "span": {"start_line": 142, "end_line": 148, "start_time_ns": 1250},
                        "extract": "Assertion axi_protocol_check_bresp_valid failed...",
                    }
                ],
            }
        }
