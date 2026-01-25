"""
UVM log parser adapter for Sentinel DV.

Parses UVM simulation logs and extracts:
- Test information (name, status, duration)
- Failure events (UVM_ERROR, UVM_FATAL, etc.)
- Topology information (component hierarchy)
- Assertion failures
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from sentinel_dv.normalization.redaction import Redactor
from sentinel_dv.schemas.common import EvidenceRef, TimeSpan
from sentinel_dv.schemas.failures import FailureEvent
from sentinel_dv.schemas.tests import (
    TestCase,
    TestStatus,
    TestTopology,
    UvmTopology,
)
from sentinel_dv.taxonomy_engine import classify_failure
from sentinel_dv.utils.bounded_text import extract_excerpt, truncate_text


@dataclass
class UVMMessage:
    """Parsed UVM message."""

    severity: str  # UVM_INFO, UVM_WARNING, UVM_ERROR, UVM_FATAL
    component: str
    message: str
    time_ns: int | None
    phase: str | None
    line_number: int


class UVMLogParser:
    """
    Parser for UVM simulation logs.

    Supports standard UVM report formats from major simulators:
    - Questa/ModelSim
    - VCS
    - Xcelium
    """

    # UVM message pattern (generic)
    # Format: UVM_[SEVERITY] @ [TIME]: [COMPONENT] [FILE]([LINE]) [MESSAGE]
    UVM_MSG_PATTERN = re.compile(
        r"(UVM_(?:INFO|WARNING|ERROR|FATAL))"  # Severity
        r"(?:\s+@\s*(\d+(?:\.\d+)?)\s*([a-z]+))?"  # Optional: @ time units
        r"(?::\s*)?"
        r"(?:\(([^)]+)\))?"  # Optional: (component)
        r"(?:\s+([^:]+):(\d+))?"  # Optional: file:line
        r"(?:\s+@\s*(\d+))?"  # Optional: @ time (alternative format)
        r"(?::|\s+)"
        r"(.+?)$",  # Message
        re.MULTILINE | re.IGNORECASE,
    )

    # Questa/VCS specific patterns
    QUESTA_PATTERN = re.compile(
        r"#\s*(UVM_(?:INFO|WARNING|ERROR|FATAL))\s+"
        r"(?:@\s*(\d+)\s*([a-z]+)\s*)?"
        r"(?:\[([^\]]+)\]\s*)?"  # Reporter ID
        r"(?:\(([^)]+)\):\s*)?"  # Component
        r"(.+?)$",
        re.MULTILINE | re.IGNORECASE,
    )

    # VCS specific patterns
    VCS_PATTERN = re.compile(
        r"(UVM_(?:INFO|WARNING|ERROR|FATAL))\s+"
        r"(?:@\s*(\d+)\s*([a-z]+)\s*)?"
        r"(?:\[([^\]]+)\]\s*)?"  # Reporter ID
        r"([^:]+\.sv[h]?):\((\d+)\)\s+"
        r"(?:@\s*(\d+)\s*)?"
        r"(.+?)$",
        re.MULTILINE,
    )

    # Phase detection
    PHASE_PATTERN = re.compile(r'(?:UVM_INFO.*)?(?:phase|Phase)\s+["\']?(\w+)["\']?', re.IGNORECASE)

    # Test name extraction
    TEST_NAME_PATTERN = re.compile(
        r'(?:TEST|test_name|Running test|Starting test)[\s:]+["\']?(\w+)["\']?', re.IGNORECASE
    )

    # Test status patterns
    TEST_PASSED_PATTERN = re.compile(
        r"(?:TEST\s+PASSED|test\s+passed|PASS|All\s+tests\s+passed)", re.IGNORECASE
    )

    TEST_FAILED_PATTERN = re.compile(r"(?:TEST\s+FAILED|test\s+failed|FAIL)", re.IGNORECASE)

    # Topology extraction
    COMPONENT_PATTERN = re.compile(r"(?:uvm_test_top|uvm_top)\.(\S+)", re.IGNORECASE)

    def __init__(self, redactor: Redactor | None = None):
        """
        Initialize UVM log parser.

        Args:
            redactor: Redactor instance for PII/credential removal
        """
        self.redactor = redactor or Redactor()

    def parse_log(self, log_path: Path) -> dict:
        """
        Parse a UVM log file.

        Args:
            log_path: Path to UVM log file

        Returns:
            Dictionary with:
                - test: TestCase or None
                - failures: List of FailureEvent
                - topology: TestTopology or None
        """
        log_path = Path(log_path)

        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")

        # Read log file
        with open(log_path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Parse messages
        messages = list(self._extract_messages(content))

        # Extract test information
        test_name = self._extract_test_name(content)
        test_status = self._determine_test_status(content, messages)

        # Extract failures (UVM_ERROR and UVM_FATAL)
        failures = self._extract_failures(messages, log_path)

        # Extract topology
        topology = self._extract_topology(content)

        # Build test case (if we found a test name)
        test = None
        if test_name:
            test = TestCase(
                name=test_name,
                status=test_status,
                framework="uvm",
                duration=None,  # Would need timing info from log
                seed=None,  # Would need seed info from command line or log
                evidence=[EvidenceRef(kind="log", path=str(log_path), extract=None)],
                topology=topology,
            )

        return {
            "test": test,
            "failures": failures,
            "topology": topology,
        }

    def _extract_messages(self, content: str) -> Iterator[UVMMessage]:
        """
        Extract all UVM messages from log content.

        Args:
            content: Log file content

        Yields:
            UVMMessage instances
        """
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Try generic pattern
            match = self.UVM_MSG_PATTERN.search(line)
            if match:
                severity = match.group(1).upper()
                time_str = match.group(2) or match.group(7)
                time_unit = match.group(3)
                component = match.group(4) or "unknown"
                message = match.group(8).strip()

                time_ns = self._parse_time(time_str, time_unit) if time_str else None
                phase = self._extract_phase(message)

                yield UVMMessage(
                    severity=severity,
                    component=component,
                    message=message,
                    time_ns=time_ns,
                    phase=phase,
                    line_number=line_num,
                )
                continue

            # Try Questa pattern
            match = self.QUESTA_PATTERN.search(line)
            if match:
                severity = match.group(1).upper()
                time_str = match.group(2)
                time_unit = match.group(3)
                component = match.group(5) or match.group(4) or "unknown"
                message = match.group(6).strip()

                time_ns = self._parse_time(time_str, time_unit) if time_str else None
                phase = self._extract_phase(message)

                yield UVMMessage(
                    severity=severity,
                    component=component,
                    message=message,
                    time_ns=time_ns,
                    phase=phase,
                    line_number=line_num,
                )
                continue

            # Try VCS pattern
            match = self.VCS_PATTERN.search(line)
            if match:
                severity = match.group(1).upper()
                time_str = match.group(2) or match.group(7)
                time_unit = match.group(3)
                component = match.group(4) or "unknown"
                message = match.group(8).strip()

                time_ns = self._parse_time(time_str, time_unit) if time_str else None
                phase = self._extract_phase(message)

                yield UVMMessage(
                    severity=severity,
                    component=component,
                    message=message,
                    time_ns=time_ns,
                    phase=phase,
                    line_number=line_num,
                )

    def _parse_time(self, time_str: str, unit: str | None) -> int | None:
        """
        Parse simulation time to nanoseconds.

        Args:
            time_str: Time value string
            unit: Time unit (ns, us, ms, s, ps, fs)

        Returns:
            Time in nanoseconds, or None if parsing fails
        """
        try:
            time_val = float(time_str)
        except (ValueError, TypeError):
            return None

        # Convert to nanoseconds
        if not unit:
            return int(time_val)  # Assume ns if no unit

        unit_lower = unit.lower()
        if unit_lower == "fs":
            return int(time_val / 1_000_000)
        elif unit_lower == "ps":
            return int(time_val / 1_000)
        elif unit_lower == "ns":
            return int(time_val)
        elif unit_lower in ("us", "μs"):
            return int(time_val * 1_000)
        elif unit_lower == "ms":
            return int(time_val * 1_000_000)
        elif unit_lower == "s":
            return int(time_val * 1_000_000_000)
        else:
            return int(time_val)  # Default to ns

    def _extract_phase(self, message: str) -> str | None:
        """Extract UVM phase from message."""
        match = self.PHASE_PATTERN.search(message)
        return match.group(1) if match else None

    def _extract_test_name(self, content: str) -> str | None:
        """Extract test name from log content."""
        match = self.TEST_NAME_PATTERN.search(content)
        return match.group(1) if match else None

    def _determine_test_status(self, content: str, messages: list[UVMMessage]) -> TestStatus:
        """
        Determine overall test status.

        Args:
            content: Full log content
            messages: Parsed UVM messages

        Returns:
            TestStatus enum value
        """
        # Check for explicit pass/fail markers
        if self.TEST_PASSED_PATTERN.search(content):
            return "pass"

        if self.TEST_FAILED_PATTERN.search(content):
            return "fail"

        # Check for UVM_FATAL (always fail)
        has_fatal = any(msg.severity == "UVM_FATAL" for msg in messages)
        if has_fatal:
            return "fail"

        # Check for UVM_ERROR (usually fail)
        has_error = any(msg.severity == "UVM_ERROR" for msg in messages)
        if has_error:
            return "fail"

        # Default to pass if no errors
        return "pass"

    def _extract_failures(self, messages: list[UVMMessage], log_path: Path) -> list[FailureEvent]:
        """
        Extract failure events from UVM messages.

        Args:
            messages: Parsed UVM messages
            log_path: Path to log file

        Returns:
            List of FailureEvent instances
        """
        failures = []

        for msg in messages:
            # Only extract ERROR and FATAL messages
            if msg.severity not in ("UVM_ERROR", "UVM_FATAL"):
                continue

            # Classify using taxonomy engine
            taxonomy = classify_failure(
                message=msg.message,
                severity=msg.severity,
                component=msg.component,
                phase=msg.phase,
                framework="uvm",
            )

            # Apply redaction
            summary = self.redactor.redact(truncate_text(msg.message, 200))
            message_full = self.redactor.redact(truncate_text(msg.message, 2000))

            # Create evidence reference
            evidence = [
                EvidenceRef(
                    kind="log",
                    path=log_path.name,  # Use relative path (just filename)
                    start_line=msg.line_number,
                    end_line=msg.line_number,
                    extract=extract_excerpt(msg.message, 500),
                )
            ]

            # Create failure event
            failure = FailureEvent(
                severity=taxonomy.severity,
                category=taxonomy.category,
                summary=summary,
                message=message_full,
                component=msg.component,
                phase=msg.phase,
                time_ns=msg.time_ns,
                tags=taxonomy.tags,
                evidence=evidence,
            )

            failures.append(failure)

        return failures

    def _extract_topology(self, content: str) -> TestTopology | None:
        """
        Extract test topology from log content.

        Args:
            content: Log file content

        Returns:
            TestTopology or None if no topology found
        """
        # Extract component hierarchy (simplified)
        components = set()

        for match in self.COMPONENT_PATTERN.finditer(content):
            comp_path = match.group(1)
            components.add(comp_path)

        if not components:
            return None

        # Build simplified UVM topology
        uvm_top = UvmTopology(
            test_name="unknown",
            env_name="env" if any("env" in c for c in components) else None,
            agents=[],  # Would need more sophisticated parsing
            scoreboards=[],
            monitors=[],
            interfaces=[],
        )

        return TestTopology(framework="uvm", dut_top=None, uvm=uvm_top)
