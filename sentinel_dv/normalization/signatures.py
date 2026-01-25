"""Failure signature generation for Sentinel DV.

Stable signature hashing enables grouping similar failures across runs.
"""

from sentinel_dv.schemas.failures import FailureCategory
from sentinel_dv.utils.hashing import stable_signature


def generate_failure_signature(
    category: FailureCategory,
    summary: str,
    protocol: str | None = None,
) -> str:
    """Generate stable failure signature ID.

    Signature is computed from:
    - Normalized category
    - Normalized summary
    - Optional protocol tag

    Args:
        category: Failure category.
        summary: Normalized failure summary.
        protocol: Optional protocol tag (e.g., "AXI4", "APB").

    Returns:
        Stable signature ID (e.g., "sig_abc123def456").
    """
    components = [category, summary.lower().strip()]

    if protocol:
        components.append(protocol.upper())

    hash_part = stable_signature(components)
    return f"sig_{hash_part}"


def normalize_failure_summary(raw_message: str, max_length: int = 256) -> str:
    """Normalize failure message to create stable summary.

    Normalization removes:
    - Timestamps
    - Line numbers
    - Memory addresses
    - Transient identifiers (transaction IDs, etc.)

    Args:
        raw_message: Raw failure message.
        max_length: Maximum summary length.

    Returns:
        Normalized summary suitable for signature generation.
    """
    import re

    summary = raw_message.strip()

    # Remove common UVM prefixes
    summary = re.sub(r"^UVM_(INFO|WARNING|ERROR|FATAL)\s*[@:]?\s*\d*[a-z]*:?\s*", "", summary)

    # Remove timestamps (@ 1250ns, @ 1.25us, etc.)
    summary = re.sub(r"@\s*\d+(\.\d+)?\s*(ns|us|ms|s)\s*:?", "", summary)

    # Remove line numbers
    summary = re.sub(r"\bline\s+\d+\b", "line N", summary, flags=re.IGNORECASE)

    # Remove memory addresses (0x...)
    summary = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", summary)

    # Remove transaction/sequence IDs
    summary = re.sub(
        r"\b(id|seq|trans|transaction)[:=]?\s*\d+", r"\1=N", summary, flags=re.IGNORECASE
    )

    # Normalize multiple spaces
    summary = " ".join(summary.split())

    # Truncate if needed
    if len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."

    return summary
