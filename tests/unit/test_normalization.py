"""Tests for normalization layer."""

import pytest

from sentinel_dv.normalization.redaction import Redactor, redact
from sentinel_dv.normalization.signatures import (
    generate_failure_signature,
    normalize_failure_summary,
)
from sentinel_dv.normalization.taxonomy import FailureTaxonomy


class TestFailureSignatures:
    """Tests for failure signature generation."""

    def test_generate_signature_deterministic(self):
        """Signature should be deterministic for same inputs."""
        sig1 = generate_failure_signature("assertion", "AXI BRESP error")
        sig2 = generate_failure_signature("assertion", "AXI BRESP error")
        assert sig1 == sig2
        assert sig1.startswith("sig_")

    def test_generate_signature_with_protocol(self):
        """Signature should include protocol when provided."""
        sig1 = generate_failure_signature("protocol", "Bus error", protocol="AXI4")
        sig2 = generate_failure_signature("protocol", "Bus error", protocol="APB")
        assert sig1 != sig2  # Different protocols = different signatures

    def test_normalize_failure_summary(self):
        """normalize_failure_summary should remove transient data."""
        msg = "UVM_ERROR @ 1250ns: Assertion failed at line 42, address 0x12345678"
        normalized = normalize_failure_summary(msg)

        # Should not contain:
        assert "UVM_ERROR" not in normalized
        assert "@" not in normalized or "1250ns" not in normalized
        assert "0x12345678" not in normalized  # Address redacted

    def test_normalize_removes_timestamps(self):
        """Normalization should remove simulation timestamps."""
        msg = "Error @ 1.25us: Transaction failed"
        normalized = normalize_failure_summary(msg)
        assert "1.25us" not in normalized

    def test_normalize_truncates(self):
        """Normalization should truncate long messages."""
        msg = "A" * 500
        normalized = normalize_failure_summary(msg, max_length=100)
        assert len(normalized) <= 100


class TestFailureTaxonomy:
    """Tests for failure taxonomy and categorization."""

    def test_categorize_assertion(self):
        """Should categorize assertion failures."""
        msg = "Assertion axi_protocol_check failed"
        category = FailureTaxonomy.categorize(msg)
        assert category == "assertion"

    def test_categorize_scoreboard(self):
        """Should categorize scoreboard mismatches."""
        msg = "Scoreboard mismatch: expected 0x42 but got 0x43"
        category = FailureTaxonomy.categorize(msg)
        assert category == "scoreboard"

    def test_categorize_protocol(self):
        """Should categorize protocol violations."""
        msg = "AXI protocol violation: invalid handshake"
        category = FailureTaxonomy.categorize(msg)
        assert category == "protocol"

    def test_categorize_timeout(self):
        """Should categorize timeouts."""
        msg = "Test timeout after 1000us"
        category = FailureTaxonomy.categorize(msg)
        assert category == "timeout"

    def test_categorize_unknown(self):
        """Should return unknown for unrecognized failures."""
        msg = "Some random error message"
        category = FailureTaxonomy.categorize(msg)
        assert category == "unknown"

    def test_extract_tags(self):
        """Should extract relevant tags from message."""
        msg = "AXI4 BRESP received DECERR for write transaction"
        tags = FailureTaxonomy.extract_tags(msg, "protocol")

        assert "AXI4" in tags
        assert "BRESP" in tags
        assert "DECERR" in tags


class TestRedaction:
    """Tests for automatic redaction."""

    def test_redact_aws_keys(self):
        """Should redact AWS access keys."""
        text = "AWS key: AKIAIOSFODNN7EXAMPLE"
        redacted = redact(text)
        assert "AKIA" not in redacted
        assert "<AWS_KEY>" in redacted

    def test_redact_github_tokens(self):
        """Should redact GitHub personal access tokens."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuv"
        redacted = redact(text)
        assert "ghp_" not in redacted
        assert "<GITHUB_TOKEN>" in redacted

    def test_redact_bearer_tokens(self):
        """Should redact OAuth Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = redact(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "Bearer <TOKEN>" in redacted

    def test_redact_emails(self):
        """Should redact email addresses when enabled."""
        redactor = Redactor(redact_emails=True)
        text = "Contact: user@example.com"
        redacted = redactor.redact(text)
        assert "user@example.com" not in redacted
        assert "<EMAIL>" in redacted

    def test_redact_paths(self):
        """Should redact absolute paths when enabled."""
        redactor = Redactor(redact_paths=True)
        text = "File: /home/user/secret/file.log"
        redacted = redactor.redact(text)
        assert "/home/user/secret/file.log" not in redacted
        assert "<PATH>" in redacted

    def test_custom_patterns(self):
        """Should support custom redaction patterns."""
        redactor = Redactor(custom_patterns=[(r"\bINTERNAL-\d+\b", "<TICKET>")])
        text = "See ticket INTERNAL-12345"
        redacted = redactor.redact(text)
        assert "INTERNAL-12345" not in redacted
        assert "<TICKET>" in redacted
