"""Normalization module initialization."""

from sentinel_dv.normalization.redaction import Redactor, get_default_redactor, redact
from sentinel_dv.normalization.signatures import (
    generate_failure_signature,
    normalize_failure_summary,
)
from sentinel_dv.normalization.taxonomy import FailureTaxonomy

__all__ = [
    # Signatures
    "generate_failure_signature",
    "normalize_failure_summary",
    # Taxonomy
    "FailureTaxonomy",
    # Redaction
    "Redactor",
    "get_default_redactor",
    "redact",
]
