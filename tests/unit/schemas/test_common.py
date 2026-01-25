"""Tests for common schemas."""

import pytest
from pydantic import ValidationError

from sentinel_dv.schemas.common import (
    CIInfo,
    EvidenceKind,
    EvidenceRef,
    PaginationInfo,
    RunRef,
    TimeSpan,
)
from sentinel_dv.utils.time import now_utc


class TestTimeSpan:
    """Tests for TimeSpan model."""

    def test_valid_line_span(self):
        """TimeSpan should validate with valid line range."""
        span = TimeSpan(start_line=10, end_line=20)
        assert span.start_line == 10
        assert span.end_line == 20

    def test_valid_time_span(self):
        """TimeSpan should validate with valid time range."""
        span = TimeSpan(start_time_ns=1000, end_time_ns=2000)
        assert span.start_time_ns == 1000
        assert span.end_time_ns == 2000

    def test_invalid_line_range(self):
        """TimeSpan should reject end_line < start_line."""
        with pytest.raises(ValidationError):
            TimeSpan(start_line=20, end_line=10)

    def test_invalid_time_range(self):
        """TimeSpan should reject end_time_ns < start_time_ns."""
        with pytest.raises(ValidationError):
            TimeSpan(start_time_ns=2000, end_time_ns=1000)

    def test_partial_span(self):
        """TimeSpan should allow partial ranges."""
        span = TimeSpan(start_line=10)
        assert span.start_line == 10
        assert span.end_line is None


class TestEvidenceRef:
    """Tests for EvidenceRef model."""

    def test_valid_evidence_ref(self):
        """EvidenceRef should validate with valid inputs."""
        ref = EvidenceRef(
            kind="log",
            path="regression/test.log",
            span=TimeSpan(start_line=10, end_line=20),
            extract="Error message",
            hash="a" * 64,
        )
        assert ref.kind == "log"
        assert ref.path == "regression/test.log"
        assert ref.span.start_line == 10

    def test_minimal_evidence_ref(self):
        """EvidenceRef should work with only required fields."""
        ref = EvidenceRef(kind="log", path="test.log")
        assert ref.kind == "log"
        assert ref.path == "test.log"
        assert ref.span is None

    def test_reject_absolute_path(self):
        """EvidenceRef should reject absolute paths."""
        with pytest.raises(ValidationError):
            EvidenceRef(kind="log", path="/absolute/path/to/file.log")

    def test_reject_path_traversal(self):
        """EvidenceRef should reject path traversal."""
        with pytest.raises(ValidationError):
            EvidenceRef(kind="log", path="../../etc/passwd")

    def test_invalid_hash(self):
        """EvidenceRef should reject invalid SHA-256 hash."""
        with pytest.raises(ValidationError):
            EvidenceRef(kind="log", path="test.log", hash="invalid")


class TestRunRef:
    """Tests for RunRef model."""

    def test_valid_run_ref(self):
        """RunRef should validate with valid inputs."""
        ref = RunRef(
            run_id="R123",
            suite="nightly",
            created_at=now_utc(),
            ci=CIInfo(
                system="jenkins", job_url="https://jenkins.example.com/job/123", build_id="123"
            ),
        )
        assert ref.run_id == "R123"
        assert ref.suite == "nightly"
        assert ref.ci.system == "jenkins"

    def test_minimal_run_ref(self):
        """RunRef should work without optional CI info."""
        ref = RunRef(run_id="R123", suite="nightly", created_at=now_utc())
        assert ref.run_id == "R123"
        assert ref.ci is None


class TestPaginationInfo:
    """Tests for PaginationInfo model."""

    def test_valid_pagination(self):
        """PaginationInfo should validate with valid inputs."""
        info = PaginationInfo(page=1, page_size=50, total_items=100, total_pages=2)
        assert info.page == 1
        assert info.page_size == 50
        assert info.total_items == 100
        assert info.total_pages == 2

    def test_reject_invalid_page(self):
        """PaginationInfo should reject page < 1."""
        with pytest.raises(ValidationError):
            PaginationInfo(page=0, page_size=50, total_items=100, total_pages=2)

    def test_reject_invalid_page_size(self):
        """PaginationInfo should reject page_size > 200."""
        with pytest.raises(ValidationError):
            PaginationInfo(page=1, page_size=500, total_items=100, total_pages=1)
