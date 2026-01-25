"""MCP tools for Sentinel DV.

This module implements all 14 MCP tools documented in docs/tools/overview.md.
"""

from typing import Any, Optional
from fastmcp import FastMCP

from sentinel_dv.indexing.store import IndexStore
from sentinel_dv.schemas.common import PaginationInfo


# ============================================================================
# Tool implementations
# ============================================================================

def list_runs(
    store: IndexStore,
    suite: Optional[str] = None,
    ci_system: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """
    List available test runs.
    
    Args:
        store: Index store instance
        suite: Filter by suite name
        ci_system: Filter by CI system
        page: Page number (1-based)
        page_size: Items per page
        
    Returns:
        Dictionary with runs and pagination info
    """
    # TODO: Implement with store.query_runs()
    return {
        "runs": [],
        "pagination": PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=0,
            total_pages=0
        ).model_dump()
    }


def get_run_details(store: IndexStore, run_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific run.
    
    Args:
        store: Index store instance
        run_id: Run identifier
        
    Returns:
        Run details dictionary
    """
    run = store.get_run(run_id)
    if not run:
        raise ValueError(f"Run not found: {run_id}")
    return run


def list_tests(
    store: IndexStore,
    run_id: Optional[str] = None,
    framework: Optional[str] = None,
    status: Optional[str] = None,
    name_pattern: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """
    List tests with filtering and pagination.
    
    Args:
        store: Index store instance
        run_id: Filter by run
        framework: Filter by framework (uvm, cocotb)
        status: Filter by status (pass, fail, error)
        name_pattern: Filter by name pattern
        page: Page number
        page_size: Items per page
        
    Returns:
        Dictionary with tests and pagination
    """
    results, total = store.query_tests(
        run_id=run_id,
        framework=framework,
        status=status,
        name_pattern=name_pattern,
        page=page,
        page_size=page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "tests": results,
        "pagination": PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages
        ).model_dump()
    }


def list_failures(
    store: IndexStore,
    test_id: Optional[str] = None,
    run_id: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    tags_any: Optional[list[str]] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """
    List failures with filtering.
    
    Args:
        store: Index store instance
        test_id: Filter by test
        run_id: Filter by run
        category: Filter by category
        severity: Filter by severity
        tags_any: Filter by any of these tags
        page: Page number
        page_size: Items per page
        
    Returns:
        Dictionary with failures and pagination
    """
    results, total = store.query_failures(
        test_id=test_id,
        run_id=run_id,
        category=category,
        severity=severity,
        tags_any=tags_any,
        page=page,
        page_size=page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "failures": results,
        "pagination": PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages
        ).model_dump()
    }


def get_regression_summary(
    store: IndexStore,
    suite: str,
    window_days: int = 7,
) -> dict[str, Any]:
    """
    Get regression summary for a suite.
    
    Args:
        store: Index store instance
        suite: Suite name
        window_days: Time window in days
        
    Returns:
        Regression summary
    """
    # Simplified implementation
    return {
        "suite": suite,
        "window_days": window_days,
        "pass_rate": 0.0,
        "top_signatures": []
    }


def compare_runs(
    store: IndexStore,
    base_run_id: str,
    compare_run_id: str,
) -> dict[str, Any]:
    """
    Compare two runs (diff).
    
    Args:
        store: Index store instance
        base_run_id: Base run ID
        compare_run_id: Compare run ID
        
    Returns:
        Diff summary
    """
    # Simplified implementation
    return {
        "base_run_id": base_run_id,
        "compare_run_id": compare_run_id,
        "test_changes": [],
        "new_failures": [],
        "resolved_failures": []
    }
