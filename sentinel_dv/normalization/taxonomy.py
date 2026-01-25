"""Failure taxonomy and categorization for Sentinel DV.

Maps failure patterns to standardized categories.
"""

import re

from sentinel_dv.schemas.failures import FailureCategory, Severity


class FailureTaxonomy:
    """Taxonomy-based failure categorization."""

    # Patterns for each category (regex, case-insensitive)
    ASSERTION_PATTERNS = [
        r"\bassertion\b.*\bfail",
        r"\bsva\b.*\bfail",
        r"\bimmediate assertion\b",
        r"assertion.*violated",
    ]

    SCOREBOARD_PATTERNS = [
        r"\bscoreboard\b.*\bmismatch",
        r"\bexpected.*but\s+got\b",
        r"\bdata\s+mismatch\b",
        r"\bcomparison\s+fail",
    ]

    PROTOCOL_PATTERNS = [
        r"\bprotocol\b.*\bviolation",
        r"\bhandshake\b.*\berror",
        r"\binvalid\s+response",
        r"\b(AXI|AHB|APB|PCIe|USB)\b.*\berror",
    ]

    TIMEOUT_PATTERNS = [
        r"\btimeout\b",
        r"\bdeadlock\b",
        r"\bhang\b",
        r"\bobjection.*timeout",
        r"\bwatchdog",
    ]

    XPROP_PATTERNS = [
        r"\bx\s+propagation\b",
        r"\bunknown\s+value",
        r"\b(X|Z)\s+detected",
    ]

    COMPILE_PATTERNS = [
        r"\bcompile\b.*\berror",
        r"\bsyntax\s+error\b",
        r"\bundeclared\s+identifier",
        r"\bvlog\b.*\berror",
    ]

    ELAB_PATTERNS = [
        r"\belaboration\b.*\berror",
        r"\bbind\b.*\bfail",
        r"\binstance.*not\s+found\b",
    ]

    RUNTIME_PATTERNS = [
        r"\bsegmentation\s+fault\b",
        r"\bcore\s+dump\b",
        r"\bfatal\b.*\berror",
        r"\bexception\b",
    ]

    @classmethod
    def categorize(cls, message: str, severity: Severity | None = None) -> FailureCategory:
        """Categorize failure based on message content.

        Args:
            message: Failure message to categorize.
            severity: Optional severity hint.

        Returns:
            Categorized failure type.
        """
        message_lower = message.lower()

        # Check each category
        if cls._matches_patterns(message_lower, cls.ASSERTION_PATTERNS):
            return "assertion"
        elif cls._matches_patterns(message_lower, cls.SCOREBOARD_PATTERNS):
            return "scoreboard"
        elif cls._matches_patterns(message_lower, cls.PROTOCOL_PATTERNS):
            return "protocol"
        elif cls._matches_patterns(message_lower, cls.TIMEOUT_PATTERNS):
            return "timeout"
        elif cls._matches_patterns(message_lower, cls.XPROP_PATTERNS):
            return "xprop"
        elif cls._matches_patterns(message_lower, cls.COMPILE_PATTERNS):
            return "compile"
        elif cls._matches_patterns(message_lower, cls.ELAB_PATTERNS):
            return "elab"
        elif cls._matches_patterns(message_lower, cls.RUNTIME_PATTERNS):
            return "runtime"

        # Default to unknown
        return "unknown"

    @staticmethod
    def _matches_patterns(text: str, patterns: list[str]) -> bool:
        """Check if text matches any pattern in list.

        Args:
            text: Text to check (should be lowercase).
            patterns: List of regex patterns.

        Returns:
            True if any pattern matches.
        """
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    @classmethod
    def extract_tags(cls, message: str, category: FailureCategory) -> list[str]:
        """Extract relevant tags from failure message.

        Args:
            message: Failure message.
            category: Categorized failure type.

        Returns:
            List of extracted tags (e.g., ["AXI", "BRESP", "DECERR"]).
        """
        tags = []

        # Extract protocol names
        protocols = ["AXI4", "AXI3", "AHB", "APB", "PCIe", "USB", "Ethernet", "I2C", "SPI", "UART"]
        for protocol in protocols:
            if re.search(rf"\b{protocol}\b", message, re.IGNORECASE):
                tags.append(protocol.upper())

        # Extract signal names (simple heuristic: all-caps words or snake_case)
        signal_pattern = r"\b([A-Z]{2,}|[a-z_]+)\b"
        potential_signals = re.findall(signal_pattern, message)
        # Add unique signals (limit to avoid bloat)
        for signal in set(potential_signals[:10]):
            if len(signal) > 2 and signal.upper() not in tags:
                tags.append(signal.upper())

        # Extract response types (OKAY, DECERR, SLVERR, etc.)
        responses = ["OKAY", "DECERR", "SLVERR", "EXOKAY"]
        for resp in responses:
            if re.search(rf"\b{resp}\b", message, re.IGNORECASE):
                tags.append(resp)

        # Limit tag count
        return tags[:20]
