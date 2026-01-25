"""
cocotb test result parser for Sentinel DV.

Parses cocotb JUnit XML output and Python exception traces to extract:
- Test results (pass/fail status)
- Failure events from exceptions
- Test metadata
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from sentinel_dv.normalization.redaction import Redactor
from sentinel_dv.schemas.common import EvidenceRef
from sentinel_dv.schemas.failures import FailureEvent
from sentinel_dv.schemas.tests import TestCase, TestStatus
from sentinel_dv.taxonomy_engine import classify_failure
from sentinel_dv.utils.bounded_text import truncate_text


class CocotbParser:
    """
    Parser for cocotb test results.

    Supports:
    - JUnit XML output
    - Python exception traces
    """

    def __init__(self, redactor: Redactor | None = None):
        """
        Initialize cocotb parser.

        Args:
            redactor: Redactor instance
        """
        self.redactor = redactor or Redactor()

    def parse_junit_xml(self, xml_path: Path) -> dict:
        """
        Parse cocotb JUnit XML output.

        Args:
            xml_path: Path to results.xml file

        Returns:
            Dictionary with tests and failures
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        tests = []
        failures = []

        # Parse each testcase
        for testcase in root.findall('.//testcase'):
            name = testcase.get('name', 'unknown')
            classname = testcase.get('classname', '')
            time_sec = float(testcase.get('time', '0'))

            # Check for failure/error elements
            failure_elem = testcase.find('failure')
            error_elem = testcase.find('error')

            if failure_elem is not None or error_elem is not None:
                status = TestStatus.FAIL
                elem = failure_elem if failure_elem is not None else error_elem

                message = elem.get('message', '')
                details = elem.text or ''

                # Classify failure
                taxonomy = classify_failure(
                    message=message + '\n' + details,
                    severity='error',
                    framework='cocotb'
                )

                # Create failure event
                failure = FailureEvent(
                    severity=taxonomy.severity.value,
                    category=taxonomy.category.value,
                    summary=self.redactor.redact(truncate_text(message, 200)),
                    message=self.redactor.redact(truncate_text(details, 2000)),
                    tags=taxonomy.tags,
                    evidence=[
                        EvidenceRef(
                            kind="junit_xml",
                            path=str(xml_path),
                            extract=truncate_text(details, 1000)
                        )
                    ]
                )
                failures.append(failure)
            else:
                status = TestStatus.PASS

            # Create test case
            test = TestCase(
                name=f"{classname}.{name}" if classname else name,
                status=status,
                framework="cocotb",
                duration=int(time_sec * 1000),  # Convert to ms
                evidence=[
                    EvidenceRef(
                        kind="junit_xml",
                        path=str(xml_path)
                    )
                ]
            )
            tests.append(test)

        return {
            "tests": tests,
            "failures": failures
        }
