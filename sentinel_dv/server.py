"""
Sentinel DV MCP Server.

This module implements the FastMCP server with all verification intelligence tools.
"""

from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from sentinel_dv.config import SentinelDVConfig, load_config
from sentinel_dv.indexing.store import IndexStore
from sentinel_dv.tools.core import (
    compare_runs,
    get_regression_summary,
    get_run_details,
    list_failures,
    list_runs,
    list_tests,
)

# Initialize FastMCP server
mcp = FastMCP("Sentinel DV")

# Global store instance
_store: IndexStore | None = None
_config: SentinelDVConfig | None = None


def get_store() -> IndexStore:
    """Get or create index store instance."""
    global _store, _config

    if _store is None:
        if _config is None:
            raise RuntimeError("Server not initialized. Call init_server() first.")

        db_path = Path(_config.index.db_path)
        _store = IndexStore(db_path)
        _store.connect()

    return _store


def init_server(config_path: Path | None = None) -> None:
    """
    Initialize server with configuration.

    Args:
        config_path: Path to config.yaml file
    """
    global _config

    if config_path:
        _config = load_config(config_path)
    else:
        # Load from default location or use defaults
        _config = SentinelDVConfig()


# ============================================================================
# MCP Tool Definitions
# ============================================================================


@mcp.tool()
def runs_list(
    suite: str | None = Field(None, description="Filter by suite name"),
    ci_system: str | None = Field(None, description="Filter by CI system"),
    page: int = Field(1, description="Page number (1-based)"),
    page_size: int = Field(100, description="Items per page"),
) -> dict[str, Any]:
    """
    List available test runs with filtering and pagination.

    Returns a paginated list of runs, optionally filtered by suite or CI system.
    """
    store = get_store()
    return list_runs(store, suite=suite, ci_system=ci_system, page=page, page_size=page_size)


@mcp.tool()
def runs_get(
    run_id: str = Field(..., description="Run identifier (r_...)"),
) -> dict[str, Any]:
    """
    Get detailed information about a specific run.

    Returns run metadata, status, CI information, and index details.
    """
    store = get_store()
    return get_run_details(store, run_id)


@mcp.tool()
def tests_list(
    run_id: str | None = Field(None, description="Filter by run ID"),
    framework: str | None = Field(None, description="Filter by framework (uvm|cocotb)"),
    status: str | None = Field(None, description="Filter by status (pass|fail|error)"),
    name_pattern: str | None = Field(None, description="Filter by name pattern"),
    page: int = Field(1, description="Page number"),
    page_size: int = Field(100, description="Items per page"),
) -> dict[str, Any]:
    """
    List tests with filtering and pagination.

    Returns tests matching the specified filters with pagination support.
    """
    store = get_store()
    return list_tests(
        store,
        run_id=run_id,
        framework=framework,
        status=status,
        name_pattern=name_pattern,
        page=page,
        page_size=page_size,
    )


@mcp.tool()
def failures_list(
    test_id: str | None = Field(None, description="Filter by test ID"),
    run_id: str | None = Field(None, description="Filter by run ID"),
    category: str | None = Field(None, description="Filter by category"),
    severity: str | None = Field(None, description="Filter by severity"),
    tags_any: list[str] | None = Field(None, description="Filter by any of these tags"),
    page: int = Field(1, description="Page number"),
    page_size: int = Field(100, description="Items per page"),
) -> dict[str, Any]:
    """
    List failures with filtering and pagination.

    Returns failures matching the specified filters with full taxonomy and evidence.
    """
    store = get_store()
    return list_failures(
        store,
        test_id=test_id,
        run_id=run_id,
        category=category,
        severity=severity,
        tags_any=tags_any,
        page=page,
        page_size=page_size,
    )


@mcp.tool()
def regressions_summary(
    suite: str = Field(..., description="Suite name"),
    window_days: int = Field(7, description="Time window in days"),
) -> dict[str, Any]:
    """
    Get regression analytics for a test suite.

    Returns pass rates, trends, and top failure signatures over the specified time window.
    """
    store = get_store()
    return get_regression_summary(store, suite=suite, window_days=window_days)


@mcp.tool()
def runs_diff(
    base_run_id: str = Field(..., description="Base run ID"),
    compare_run_id: str = Field(..., description="Compare run ID"),
) -> dict[str, Any]:
    """
    Compare two runs to identify changes.

    Returns test status changes, new failures, resolved failures, and coverage deltas.
    """
    store = get_store()
    return compare_runs(store, base_run_id=base_run_id, compare_run_id=compare_run_id)


# ============================================================================
# Server lifecycle
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    # Initialize with default config
    init_server()

    # Run server
    mcp.run()


if __name__ == "__main__":
    main()
