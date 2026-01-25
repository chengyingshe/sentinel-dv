"""
Taxonomy engine for failure categorization and tagging.

This module implements the taxonomy rules documented in docs/taxonomy.md.
Rules are applied in order with first-match-wins semantics.
"""

import re
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Failure severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class Category(str, Enum):
    """Failure categories."""
    ASSERTION = "assertion"
    SCOREBOARD = "scoreboard"
    PROTOCOL = "protocol"
    TIMEOUT = "timeout"
    XPROP = "xprop"
    COMPILE = "compile"
    ELAB = "elab"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


@dataclass
class TaxonomyResult:
    """Result of taxonomy classification."""
    severity: Severity
    category: Category
    tags: list[str]
    taxonomy_reason: str | None = None  # Internal debugging field


class TaxonomyEngine:
    """
    Rule-based failure classification engine.

    Applies ordered rules to classify failures into categories and assign tags.
    """

    # Maximum tags per failure
    MAX_TAGS = 20

    def __init__(self):
        """Initialize taxonomy engine with default rules."""
        pass

    def classify(
        self,
        message: str,
        severity: str | None = None,
        component: str | None = None,
        phase: str | None = None,
        framework: str | None = None,
    ) -> TaxonomyResult:
        """
        Classify a failure message.

        Args:
            message: Failure message text
            severity: Raw severity string (UVM_ERROR, etc.)
            component: Component name
            phase: Test phase
            framework: Framework name (uvm, cocotb)

        Returns:
            TaxonomyResult with category, severity, and tags
        """
        # Normalize severity
        normalized_severity = self._normalize_severity(severity, message)

        # Apply category rules (ordered, first match wins)
        category, reason, category_tags = self._categorize(message, framework)

        # Build tag set
        tags = self._build_tags(
            category,
            category_tags,
            message,
            component,
            phase,
            framework,
        )

        return TaxonomyResult(
            severity=normalized_severity,
            category=category,
            tags=tags[:self.MAX_TAGS],  # Enforce limit
            taxonomy_reason=reason,
        )

    # ========================================================================
    # Severity normalization
    # ========================================================================

    def _normalize_severity(self, raw_severity: str | None, message: str) -> Severity:
        """
        Normalize severity from various formats.

        Args:
            raw_severity: Raw severity string
            message: Message text (for context)

        Returns:
            Normalized Severity enum
        """
        if not raw_severity:
            # Infer from message keywords
            message_lower = message.lower()
            if any(kw in message_lower for kw in ['fatal', 'segfault', 'crash', 'abort']):
                return Severity.FATAL
            if any(kw in message_lower for kw in ['error', 'fail', 'exception']):
                return Severity.ERROR
            if any(kw in message_lower for kw in ['warning', 'warn']):
                return Severity.WARNING
            return Severity.INFO

        sev_lower = raw_severity.lower()

        # UVM severity mapping
        if 'uvm_fatal' in sev_lower or 'fatal' in sev_lower:
            return Severity.FATAL
        if 'uvm_error' in sev_lower or '*e' in sev_lower:  # *E for Xcelium
            return Severity.ERROR
        if 'uvm_warning' in sev_lower or '*w' in sev_lower:
            return Severity.WARNING
        if 'uvm_info' in sev_lower:
            return Severity.INFO

        # Default to error for safety
        return Severity.ERROR

    # ========================================================================
    # Category rules (ordered)
    # ========================================================================

    def _categorize(
        self,
        message: str,
        framework: str | None = None,
    ) -> tuple[Category, str, list[str]]:
        """
        Apply category rules in order.

        Args:
            message: Failure message
            framework: Framework name

        Returns:
            Tuple of (Category, reason_code, initial_tags)
        """
        msg_lower = message.lower()

        # Rule Group A: Compile / Elaboration (highest priority)

        # Rule 1: Compile
        compile_patterns = [
            r'compilation\s+failed',
            r'error-[a-z0-9]+.*compile',
            r'vlog-',
            r'xmvlog',
            r'syntax\s+error',
            r'unexpected\s+token',
            r'undefined\s+variable',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in compile_patterns):
            return Category.COMPILE, "RULE_COMPILE", ["compile"]

        # Rule 2: Elaboration
        elab_patterns = [
            r'elaboration\s+failed',
            r'unresolved\s+reference',
            r'cannot\s+find\s+instance',
            r'binding\s+failed',
            r'top\s+module\s+not\s+found',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in elab_patterns):
            return Category.ELAB, "RULE_ELAB", ["elab"]

        # Rule Group B: Assertions

        # Rule 3: Assertion failures
        assertion_patterns = [
            r'assertion\s+failed',
            r'sva.*failed',
            r'assert\s+property.*fail',
            r'\*\*\s+error:.*vsim-.*assertion',  # Questa
            r'assertion\s+failure',  # VCS
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in assertion_patterns):
            tags = ["assertion", "sva"]
            # Extract assertion name if present
            name_match = re.search(r'assertion\s+["\']?(\w+)["\']?', message, re.IGNORECASE)
            if name_match:
                tags.append(f"assert:{name_match.group(1)}")
            return Category.ASSERTION, "RULE_ASSERTION", tags

        # Rule Group C: Timeouts / Deadlocks

        # Rule 4: Timeout
        timeout_patterns = [
            r'timeout',
            r'watchdog',
            r'no\s+activity\s+for',
            r'objection\s+timeout',
            r'phase\s+timeout',
            r'simulation\s+time\s+limit\s+reached',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in timeout_patterns):
            return Category.TIMEOUT, "RULE_TIMEOUT", ["timeout"]

        # Rule Group D: X-Propagation

        # Rule 5: Xprop / X-check
        xprop_patterns = [
            r'x-propagation',
            r'x-check',
            r'unknown\s+value\s+x',
            r'has\s+xs',
            r'xrun:.*\*e.*\bx\b',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in xprop_patterns):
            return Category.XPROP, "RULE_XPROP", ["xprop"]

        # Rule Group E: Scoreboard / Data Mismatches

        # Rule 6: Scoreboard mismatch
        scoreboard_patterns = [
            r'scoreboard.*(mismatch|compare\s+failed|unexpected|expected)',
            r'data\s+mismatch',
            r'crc\s+mismatch',
            r'sequence\s+item\s+mismatch',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in scoreboard_patterns):
            return Category.SCOREBOARD, "RULE_SCOREBOARD", ["scoreboard"]

        # Rule Group F: Protocol Violations

        # Rule 7: Protocol
        protocol_patterns = [
            r'protocol\s+violation',
            r'handshake\s+violation',
            r'illegal\s+transition',
            r'unexpected\s+response',
            r'bresp.*error',
            r'rresp.*error',
            r'pslverr',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in protocol_patterns):
            return Category.PROTOCOL, "RULE_PROTOCOL", ["protocol"]

        # Rule Group G: Runtime/Infrastructure

        # Rule 8: Runtime
        runtime_patterns = [
            r'segmentation\s+fault',
            r'core\s+dumped',
            r'simulator\s+terminated',
            r'out\s+of\s+memory',
            r'license\s+checkout\s+failed',
            r'importerror',
            r'runtimeerror',
            r'simulatorerror',
        ]
        if any(re.search(p, msg_lower, re.IGNORECASE) for p in runtime_patterns):
            return Category.RUNTIME, "RULE_RUNTIME", ["runtime"]

        # Default: Unknown
        return Category.UNKNOWN, "RULE_DEFAULT", []

    # ========================================================================
    # Tag building
    # ========================================================================

    def _build_tags(
        self,
        category: Category,
        category_tags: list[str],
        message: str,
        component: str | None,
        phase: str | None,
        framework: str | None,
    ) -> list[str]:
        """
        Build comprehensive tag set.

        Tags are ordered: category/framework/protocol/vendor/phase/component_role/other

        Args:
            category: Classified category
            category_tags: Tags from category rule
            message: Message text
            component: Component name
            phase: Test phase
            framework: Framework name

        Returns:
            Ordered list of tags
        """
        tags = list(category_tags)  # Start with category tags

        # Add framework tag
        if framework:
            framework_tag = framework.lower()
            if framework_tag not in tags:
                tags.append(framework_tag)

        # Add protocol tags
        protocol_tags = self._detect_protocol(message)
        tags.extend([t for t in protocol_tags if t not in tags])

        # Add vendor tags (from message)
        vendor_tags = self._detect_vendor(message)
        tags.extend([t for t in vendor_tags if t not in tags])

        # Add phase tags
        if phase:
            phase_tag = f"phase:{phase.lower()}"
            if phase_tag not in tags:
                tags.append(phase_tag)

        # Add component role tags
        if component:
            role_tags = self._detect_component_role(component)
            tags.extend([t for t in role_tags if t not in tags])

        return tags

    def _detect_protocol(self, message: str) -> list[str]:
        """
        Detect protocol from message content.

        Args:
            message: Message text

        Returns:
            List of protocol tags
        """
        msg_lower = message.lower()
        tags = []

        # AXI
        if any(kw in msg_lower for kw in ['axi', 'awvalid', 'wready', 'bresp']):
            tags.append('axi4')

        # APB
        if any(kw in msg_lower for kw in ['paddr', 'psel', 'pready', 'pslverr']):
            tags.append('apb')

        # AHB
        if any(kw in msg_lower for kw in ['haddr', 'hready', 'hresp']):
            tags.append('ahb')

        # PCIe
        if any(kw in msg_lower for kw in ['ltssm', 'ts1', 'ts2', 'pcie']):
            tags.append('pcie')

        # USB
        if any(kw in msg_lower for kw in ['lfps', 'pipe', 'u0', 'u1', 'u2', 'usb']):
            tags.append('usb')

        # JTAG
        if any(kw in msg_lower for kw in ['tms', 'tck', 'tdo', 'tdi', 'jtag']):
            tags.append('jtag')

        # I2C
        if any(kw in msg_lower for kw in ['scl', 'sda', 'i2c']):
            tags.append('i2c')

        # SPI
        if any(kw in msg_lower for kw in ['mosi', 'miso', 'sclk', 'spi']):
            tags.append('spi')

        return tags

    def _detect_vendor(self, message: str) -> list[str]:
        """
        Detect simulator vendor from message.

        Args:
            message: Message text

        Returns:
            List of vendor tags
        """
        msg_lower = message.lower()
        tags = []

        if any(kw in msg_lower for kw in ['vcs', 'vcsmx']):
            tags.append('vcs')
        elif any(kw in msg_lower for kw in ['questa', 'vsim', 'modelsim']):
            tags.append('questa')
        elif any(kw in msg_lower for kw in ['xcelium', 'xrun', 'xmvlog']):
            tags.append('xcelium')
        elif 'verilator' in msg_lower:
            tags.append('verilator')
        elif 'riviera' in msg_lower:
            tags.append('riviera')

        return tags

    def _detect_component_role(self, component: str) -> list[str]:
        """
        Detect component role from component name.

        Args:
            component: Component name

        Returns:
            List of role tags
        """
        comp_lower = component.lower()
        tags = []

        if 'driver' in comp_lower or 'drv' in comp_lower:
            tags.append('driver')
        if 'monitor' in comp_lower or 'mon' in comp_lower:
            tags.append('monitor')
        if 'scoreboard' in comp_lower or 'scb' in comp_lower:
            tags.append('scoreboard')
        if 'sequencer' in comp_lower or 'sqr' in comp_lower:
            tags.append('sequencer')

        return tags


# Singleton instance
_taxonomy_engine = TaxonomyEngine()


def classify_failure(
    message: str,
    severity: str | None = None,
    component: str | None = None,
    phase: str | None = None,
    framework: str | None = None,
) -> TaxonomyResult:
    """
    Classify a failure message using the default taxonomy engine.

    Args:
        message: Failure message text
        severity: Raw severity string
        component: Component name
        phase: Test phase
        framework: Framework name

    Returns:
        TaxonomyResult with category, severity, and tags
    """
    return _taxonomy_engine.classify(message, severity, component, phase, framework)
