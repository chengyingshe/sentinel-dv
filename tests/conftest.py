"""Test fixtures and shared utilities."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from sentinel_dv.config import SentinelDVConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir: Path) -> SentinelDVConfig:
    """Provide a sample configuration for testing."""
    return SentinelDVConfig(
        artifact_roots=[str(temp_dir)],
        index={"type": "duckdb", "path": str(temp_dir / "test.db")},
    )


@pytest.fixture
def sample_uvm_log(temp_dir: Path) -> Path:
    """Create a sample UVM log file."""
    log_file = temp_dir / "test.log"
    log_file.write_text("""
UVM_INFO @ 0: uvm_test_top [TEST] Starting test
UVM_INFO @ 100ns: uvm_test_top.env [ENV] Environment built
UVM_ERROR @ 1250ns: uvm_test_top.env.agent.monitor [MONITOR] Assertion failed
UVM_FATAL @ 2000ns: uvm_test_top [TEST] Fatal error occurred
    """.strip())
    return log_file


@pytest.fixture
def sample_cocotb_result(temp_dir: Path) -> Path:
    """Create a sample cocotb results file."""
    result_file = temp_dir / "results.xml"
    result_file.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="cocotb_tests" tests="2" failures="1">
    <testcase name="test_basic" time="0.5" />
    <testcase name="test_advanced" time="1.2">
      <failure message="Assertion error">Expected 0x42 but got 0x43</failure>
    </testcase>
  </testsuite>
</testsuites>
    """.strip())
    return result_file
